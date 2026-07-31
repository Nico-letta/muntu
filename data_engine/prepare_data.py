import os
import random
import gc
from datasets import load_dataset

def wikipedia_streamer(filepath):
    if not os.path.exists(filepath):
        return
    
    with open(filepath, "r", encoding="utf-8") as f:
        paragraph = []
        for line in f:
            if line == "\n" or line == "\r\n" or not line.strip():
                if paragraph:
                    text = "".join(paragraph).strip()
                    if len(text) > 50:
                        yield text
                    paragraph = []
            else:
                paragraph.append(line)
        if paragraph:
            text = "".join(paragraph).strip()
            if len(text) > 50:
                yield text

def build_massive_corpus():
    base_dir = os.path.dirname(os.path.abspath(__file__))
    output_path = os.path.join(base_dir, "_output", "corpus_pretrain.txt")
    wikipedia_path = "/content/drive/MyDrive/muntu_project/model_engine/wikipedia_fr_raw.txt"
    
    print("[*] Début de la collecte des données pour MUNTU...")

    existing_content = ""
    if os.path.exists(output_path):
        with open(output_path, "r", encoding="utf-8") as f:
            existing_content = f.read()
        print("[+] Contenu UI/Fintech d'origine sauvegardé en mémoire.")
    else:
        print("[!] Attention : aucun corpus_pretrain.txt trouvé au départ.")

    print("[*] Connexion à uonlp/CulturaX (Séquence de streaming active)...")
    french_text = []
    target_french_bytes = 30 * 1024 * 1024 
    current_french_size = 0
    
    try:
        culturax_fr = load_dataset("uonlp/CulturaX", "fr", split="train", streaming=True)
        for row in culturax_fr:
            text = row['text'].strip()
            if len(text) > 150:
                cleaned_text = " ".join(text.split())
                french_text.append(cleaned_text)
                current_french_size += len(cleaned_text.encode('utf-8'))
            if current_french_size >= target_french_bytes:
                break
        print(f"[+] ~{current_french_size / (1024*1024):.2f} Mo de texte généraliste CulturaX FR récupérés.")
    except Exception as e:
        print(f"[!] Échec du chargement de CulturaX FR : {e}")

    print("[*] Téléchargement de iamtarun/python_code_instructions_18k_alpaca...")
    code_text = []
    try:
        code_dataset = load_dataset("iamtarun/python_code_instructions_18k_alpaca", split="train")
        target_code_bytes = 10 * 1024 * 1024 
        current_code_size = 0
        for row in code_dataset:
            instruction = row.get('instruction', '')
            output_code = row.get('output', '')
            code_chunk = f"# Task: {instruction}\n{output_code}"
            code_text.append(code_chunk)
            current_code_size += len(code_chunk.encode('utf-8'))
            if current_code_size >= target_code_bytes:
                break
        print(f"[+] ~{current_code_size / (1024*1024):.2f} Mo de code algorithmique récupérés.")
    except Exception as e:
        print(f"[!] Échec du chargement du code : {e}")

    fintech_docs = [doc.strip() for doc in existing_content.split("\n\n") if len(doc.strip()) > 50] if existing_content else []
    fintech_pool = fintech_docs * 15 if fintech_docs else []

    small_pool = fintech_pool + french_text + code_text
    random.shuffle(small_pool)
    
    remaining_small = len(small_pool)
    print(f"[+] Pool de documents prioritaires prêt : {remaining_small} documents en RAM.")

    wiki_gen = wikipedia_streamer(wikipedia_path)
    estimated_remaining_wiki = 1500000 if os.path.exists(wikipedia_path) else 0

    print("[*] Initialisation du buffer de mélange glissant (Buffer Size: 50 000)...")
    buffer = []
    BUFFER_SIZE = 50000

    def get_next_document():
        nonlocal remaining_small, estimated_remaining_wiki
        total_est = remaining_small + max(1, estimated_remaining_wiki)
        
        if remaining_small == 0 and estimated_remaining_wiki <= 0:
            return None

        prob_small = remaining_small / total_est
        if random.random() < prob_small and remaining_small > 0:
            doc = small_pool.pop()
            remaining_small -= 1
            return doc
        else:
            try:
                doc = next(wiki_gen)
                estimated_remaining_wiki -= 1
                return doc
            except StopIteration:
                estimated_remaining_wiki = 0
                if remaining_small > 0:
                    doc = small_pool.pop()
                    remaining_small -= 1
                    return doc
                return None

    for _ in range(BUFFER_SIZE):
        doc = get_next_document()
        if doc is None:
            break
        buffer.append(doc)

    print(f"[*] Écriture finale et progressive dans {output_path}...")
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    
    total_written = 0
    with open(output_path, "w", encoding="utf-8") as f_out:
        while buffer:
            idx = random.randint(0, len(buffer) - 1)
            f_out.write(buffer[idx] + "\n\n")
            total_written += 1
            
            if total_written % 100000 == 0:
                print(f" Écrit {total_written} documents dans le fichier final...")

            next_doc = get_next_document()
            if next_doc is not None:
                buffer[idx] = next_doc
            else:
                buffer.pop(idx)

    final_size = os.path.getsize(output_path)
    print(f"\n Opération réussie sans aucun crash de RAM !")
    print(f" Fichier généré : {output_path}")
    print(f" Taille finale : {final_size / (1024*1024*1024):.2f} Go ({total_written} documents mélangés).")
    
    gc.collect()

if __name__ == "__main__":
    build_massive_corpus()
