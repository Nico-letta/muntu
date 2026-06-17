import os
import torch
from tokenizers import ByteLevelBPETokenizer

# Importation du modèle complet
from src.model import MuntuLM

def run_test_bench():
    # --- STAGE 1 : CONFIG ---
    base_dir = os.path.dirname(os.path.abspath(__file__))
    root_dir = os.path.abspath(os.path.join(base_dir, ".."))
    tokenizer_dir = os.path.join(root_dir, "data_engine", "_output", "muntu_tokenizer")
    
    tokenizer = ByteLevelBPETokenizer(
        os.path.join(tokenizer_dir, "vocab.json"),
        os.path.join(tokenizer_dir, "merges.txt")
    )

    sample_text = "const MuntuApp = () => { return <div className='p-4'>Performance first</div> }"
    
    # --- STAGE 2 : TOKENISATION ---
    print("\n=== STAGE 1 : TOKENISATION ===")
    encoded = tokenizer.encode(sample_text)
    input_tensor = torch.tensor([encoded.ids], dtype=torch.long)
    print(f"Shape entrée : {input_tensor.shape}")

    # --- STAGE 3 : DU BLOC UNIQUE AU LLM COMPLET ---
    print("\n=== STAGE 2 : INITIALISATION DE MUNTU LM ===")
    model = MuntuLM(
        vocab_size=1495, # Notre vocabulaire exact basé sur l'entraînement BPE précédent
        d_model=256,
        max_seq_len=512,
        n_layers=4       # On empile 4 blocs consécutifs
    )
    
    # Calcul des paramètres
    total_params = sum(p.numel() for p in model.parameters() if p.requires_grad)
    print(f"[+] Modèle global initialisé avec succès !")
    print(f"[+] Nombre total de paramètres entraînables : {total_params:,}")

    # --- STAGE 4 : INFERENCE ---
    print("\n=== STAGE 3 : TEST D'INFERENCE BRUTE ===")
    with torch.no_grad():
        logits, _ = model(input_tensor)
        
    print(f"Shape des Logits de sortie : {logits.shape} -> (Batch_size, Seq_len, Vocab_size)")
    
    if logits.shape == (1, 32, 1495):
        print("L'architecture complète de MUNTU est opérationnelle de bout en bout.")
        print("Chacun des 32 tokens d'entrée dispose d'un vecteur de prédiction de taille 1495 pour le mot suivant.")
    else:
        print("Erreur : Anomalie détectée dans la dimension finale des logits.")

if __name__ == "__main__":
    run_test_bench()