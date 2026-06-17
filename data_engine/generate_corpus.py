import os

def generate_pretrain_corpus():
    base_dir = os.path.dirname(os.path.abspath(__file__))
    raw_dir = os.path.join(base_dir, "corpus_raw")
    output_dir = os.path.join(base_dir, "_output")
    output_file = os.path.join(output_dir, "corpus_pretrain.txt")
    
    # Sécurité : Créer le dossier _output s'il n'existe pas
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)
    
    print("[*] Démarrage de la compilation du corpus MUNTU...")
    
    collected_text = []
    
    # Parcourir récursivement tous les dossiers de corpus_raw
    for root, dirs, files in os.walk(raw_dir):
        for file in files:
            if file.endswith(('.md', '.tsx', '.ts', '.txt')):
                file_path = os.path.join(root, file)
                # print(file_path)
                try:
                    with open(file_path, 'r', encoding='utf-8') as f:
                        content = f.read()
                        print(content)
                        # --- ANONYMISATION ET SÉCURITÉ ---
                        # content = content.replace("Rhema", "GlobalBrandAgency")
                        
                        # Balisage minimal pour donner une structure textuelle au modèle
                        relative_path = os.path.relpath(file_path, raw_dir)
                        collected_text.append(f"\n--- START FILE: {relative_path} ---\n")
                        collected_text.append(content)
                        collected_text.append(f"\n--- END FILE: {relative_path} ---\n")
                except Exception as e:
                    print(f"[-] Erreur de lecture sur le fichier {file}: {e}")

    # Écriture du fichier final consolidé (Ligne corrigée !)
    with open(output_file, 'w', encoding='utf-8') as f_out:
        f_out.write("".join(collected_text))
        
    size_mo = os.path.getsize(output_file) / (1024 * 1024)
    print(f"[+] Compilation terminée ! Fichier généré : {output_file} ({size_mo:.2f} Mo)")

if __name__ == "__main__":
    generate_pretrain_corpus()