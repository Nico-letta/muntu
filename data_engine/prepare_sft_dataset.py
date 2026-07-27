import os
import json
import glob

OUTPUT_PATH = "/content/drive/MyDrive/muntu_project/data_engine/_output/sft_dataset.jsonl"
PROJECT_ROOT = "/content/drive/MyDrive/muntu_project"
SYSTEM_PROMPT = "Tu es MUNTU, un assistant IA utile, précis et spécialisé en ingénierie logicielle, architectures cloud et systèmes fintech."

def format_chatml(system_text: str, user_text: str, assistant_text: str) -> str:
    return (
        f"<|im_start|>system\n{system_text}<|im_end|>\n"
        f"<|im_start|>user\n{user_text}<|im_end|>\n"
        f"<|im_start|>assistant\n{assistant_text}<|im_end|>\n"
    )

def parse_markdown_blocks(filepath):
    """
    Extrait les sections des fichiers Markdown pour les transformer en Q/R.
    """
    records = []
    filename = os.path.basename(filepath)
    category = os.path.basename(os.path.dirname(filepath))
    
    try:
        with open(filepath, "r", encoding="utf-8") as f:
            content = f.read().strip()
            
        if not content:
            return records

        sections = content.split("\n## ")
        for sec in sections:
            lines = sec.strip().split("\n")
            header = lines[0].replace("#", "").strip()
            body = "\n".join(lines[1:]).strip()
            
            if len(body) > 30 and header:
                prompt = f"Explique le concept ou la spécification suivante pour {category} / {filename} : {header}"
                records.append(format_chatml(SYSTEM_PROMPT, prompt, body[:2000]))
            elif len(content) > 50 and not records:
                prompt = f"Résume la documentation technique suivante : {filename}"
                records.append(format_chatml(SYSTEM_PROMPT, prompt, content[:2000]))
                break

    except Exception as e:
        pass
        
    return records

def build_sft_dataset():
    os.makedirs(os.path.dirname(OUTPUT_PATH), exist_ok=True)
    records = []

    print("[*] Scan complet de data_engine/corpus_raw (.md et .txt)...")

    corpus_dir = os.path.join(PROJECT_ROOT, "data_engine", "corpus_raw")
    files = glob.glob(os.path.join(corpus_dir, "**/*.md"), recursive=True) + \
            glob.glob(os.path.join(corpus_dir, "**/*.txt"), recursive=True)
            
    print(f"[+] {len(files)} fichiers documentaires trouvés dans le corpus.")

    for filepath in files:
        extracted = parse_markdown_blocks(filepath)
        for chatml_text in extracted:
            records.append({"text": chatml_text})

    seed_files = [
        os.path.join(PROJECT_ROOT, "Airtel.txt"),
        os.path.join(PROJECT_ROOT, "Momo documentation.txt")
    ]
    for sf in seed_files:
        if os.path.exists(sf):
            try:
                with open(sf, "r", encoding="utf-8") as f:
                    txt = f.read().strip()
                    if txt:
                        prompt = f"Explique les fonctionnalités et l'intégration de {os.path.basename(sf)}"
                        records.append({"text": format_chatml(SYSTEM_PROMPT, prompt, txt[:2000])})
            except Exception:
                pass

    with open(OUTPUT_PATH, "w", encoding="utf-8") as f:
        for r in records:
            f.write(json.dumps(r, ensure_ascii=False) + "\n")

    print(f"OPÉRATION RÉUSSIE ! {len(records)} conversations générées directement à partir de ton corpus sous {OUTPUT_PATH}")

if __name__ == "__main__":
    build_sft_dataset()