import os
from datasets import load_dataset

def build_massive_corpus():
    base_dir = os.path.dirname(os.path.abspath(__file__))
    output_path = os.path.join(base_dir, "_output", "corpus_pretrain.txt")
    
    print("[*] Début de la collecte des données pour MUNTU...")
    
    # 1. Sauvegarde de ton travail UI/Fintech existant
    existing_content = ""
    if os.path.exists(output_path):
        with open(output_path, "r", encoding="utf-8") as f:
            existing_content = f.read()
        print("[+] Contenu UI/Fintech d'origine sauvegardé.")

    # 2. Collecte de VRAI Texte Wikipédia Français (Format Parquet natif sécurisé)
    print("[*] Téléchargement d'un extrait de wikimedia/wikipedia (20231101.fr)...")
    french_text = []
    target_size_bytes = 10 * 1024 * 1024  # On vise ~10 Mo de pur français
    current_size = 0
    
    try:
        # Version officielle de Wikimédia stockée en Parquet, aucun script exécuté !
        wiki_fr = load_dataset("wikimedia/wikipedia", "20231101.fr", split="train", streaming=True)
        
        for row in wiki_fr:
            text = row['text']
            if len(text.strip()) > 200:
                # On nettoie grossièrement les sauts de lignes multiples pour garder un texte propre
                cleaned_text = " ".join(text.split())
                french_text.append(cleaned_text)
                current_size += len(cleaned_text.encode('utf-8'))
            if current_size >= target_size_bytes:
                break
        print(f"[+] ~{current_size / (1024*1024):.2f} Mo de texte Wikipédia FR récupérés avec succès.")
    except Exception as e:
        print(f"[!] Échec du chargement de Wikipédia FR. Code erreur : {e}")

    # 3. Collecte de Code Source via le dataset fonctionnel (iamtarun)
    print("[*] Téléchargement de iamtarun/python_code_instructions_18k_alpaca...")
    code_dataset = load_dataset("iamtarun/python_code_instructions_18k_alpaca", split="train")
    
    code_text = []
    target_code_bytes = 10 * 1024 * 1024  # On monte à ~10 Mo de code pour équilibrer
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

    # 4. Fusion et écriture finale
    print("[*] Fusion de tous les piliers dans corpus_pretrain.txt...")
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    
    with open(output_path, "w", encoding="utf-8") as f:
        # Étape 1 : Origine
        if existing_content:
            f.write(existing_content + "\n\n")
        
        # Étape 2 : Wikipédia FR
        for text in french_text:
            f.write(text + "\n\n")
            
        # Étape 3 : Code Python
        for code in code_text:
            f.write(code + "\n\n")

    final_size = os.path.getsize(output_path)
    print(f"Opération terminée ! Nouveau corpus hybride prêt : {final_size / (1024*1024):.2f} Mo.")

if __name__ == "__main__":
    build_massive_corpus()