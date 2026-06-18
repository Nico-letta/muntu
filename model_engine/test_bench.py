import os
import torch
from torch.utils.data import DataLoader

# Importations de tes modules
from src.model import MuntuLM
from src.dataset import MuntuPretrainDataset

def run_test_bench():
    # --- STAGE 1 : SETUP DES CHEMINS ---
    base_dir = os.path.dirname(os.path.abspath(__file__))
    root_dir = os.path.abspath(os.path.join(base_dir, ".."))
    
    corpus_path = os.path.join(root_dir, "data_engine", "_output", "corpus_pretrain.txt")
    tokenizer_dir = os.path.join(root_dir, "data_engine", "_output", "muntu_tokenizer")

    print("\n=== STAGE 1 : CHARGEMENT DU DATASET ===")
    max_seq_len = 64  # Taille de contexte adaptée à notre test
    
    dataset = MuntuPretrainDataset(
        corpus_path=corpus_path,
        tokenizer_dir=tokenizer_dir,
        max_seq_len=max_seq_len
    )

    # Création du DataLoader (Batch_size = 2 pour simuler un traitement parallèle)
    # shuffle=True permet de mélanger les exemples à chaque époque
    dataloader = DataLoader(dataset, batch_size=2, shuffle=True)
    
    # Récupérer un seul lot (batch) pour tester la tuyauterie
    inputs_batch, targets_batch = next(iter(dataloader))
    print(f"[+] Format du Batch Inputs  (x) : {inputs_batch.shape}  -> (Batch_size, Seq_len)")
    print(f"[+] Format du Batch Targets (y) : {targets_batch.shape}  -> (Batch_size, Seq_len)")

    

    # --- STAGE 2 : LE MODÈLE COMPLEMENTAIRE ---
    print("\n=== STAGE 2 : INFERENCE & CALCUL DE LA LOSS ===")
    model = MuntuLM(
        vocab_size=1495,
        d_model=256,
        max_seq_len=512,
        n_layers=4
    )
    #logits, loss = model(inputs_batch, targets_batch)
    print(f"DEBUG - Taille dict Embedding : {model.embedding.token_embedding.weight.shape}")
    print(f"DEBUG - Taille dict LM Head   : {model.lm_head.weight.shape}")
    print(f"DEBUG - Max ID dans le Batch   : {inputs_batch.max().item()}")
    # On passe le batch d'inputs ET de targets dans le modèle pour obtenir la Loss
    logits, loss = model(inputs_batch, targets_batch)
    
    print(f"[+] Shape finale des Logits : {logits.shape}")
    print(f"[+] Loss initiale calculée  : {loss.item():.4f}")
    
    # Explication technique de la loss initiale
    # Pour un dictionnaire de 1495 tokens aléatoires, la loss théorique de départ
    # est égale à -ln(1/1495) ~= 7.31. Si on est dans ces eaux-là, les maths sont parfaites !
    print(" Pipeline de données connecté à l'architecture ! Prêt pour l'entraînement réel.")

if __name__ == "__main__":
    run_test_bench()