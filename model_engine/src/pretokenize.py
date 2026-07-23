import os
import numpy as np
from tokenizers import ByteLevelBPETokenizer
from tqdm import tqdm

def pretokenize():
    root_dir = os.getcwd()
    corpus_path = os.path.join(root_dir, "data_engine", "_output", "corpus_pretrain.txt")
    output_bin = os.path.join(root_dir, "data_engine", "_output", "corpus_pretrain.bin")
    tokenizer_dir = os.path.join(root_dir, "data_engine", "_output", "muntu_tokenizer")
 
    print("[*] Initialisation du tokenizer...")
    tokenizer = ByteLevelBPETokenizer(
        os.path.join(tokenizer_dir, "vocab.json"),
        os.path.join(tokenizer_dir, "merges.txt")
    )

    print("[*] Début de la tokenisation sécurisée par lignes...")
    
    file_size = os.path.getsize(corpus_path)

    MAX_LINE_LENGTH = 50000 

    with open(corpus_path, "r", encoding="utf-8", errors="replace") as f_in, open(output_bin, "wb") as f_out:
        with tqdm(total=file_size, unit='B', unit_scale=True, desc="Tokenisation") as pbar:
            for line_idx, line in enumerate(f_in):
                try:
                    if len(line) > MAX_LINE_LENGTH:
                        chunks = [line[i:i + 10000] for i in range(0, len(line), 10000)]
                    else:
                        chunks = [line]

                    for chunk in chunks:
                        if not chunk.strip():
                            continue
                        
                        encoded = tokenizer.encode(chunk)
                        arr = np.array(encoded.ids, dtype=np.uint16)
                        f_out.write(arr.tobytes())

                    pbar.update(len(line.encode('utf-8')))
                    
                except Exception as e:
                    print(f"\n[!] Erreur gérée à la ligne {line_idx} : {e}")
                    continue

    print(f"\n[+] Opération terminée. Fichier prêt : {output_bin}")

if __name__ == "__main__":
    pretokenize()