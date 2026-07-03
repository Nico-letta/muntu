import os
import torch
from torch.utils.data import DataLoader

# Importations depuis ton sous-dossier src/
from src.model import MuntuLM
from src.dataset import MuntuPretrainDataset

def train_muntu():

    base_dir = os.path.dirname(os.path.abspath(__file__))
    root_dir = os.path.abspath(os.path.join(base_dir, ".."))
    
    corpus_path = os.path.join(root_dir, "data_engine", "_output", "corpus_pretrain.txt")
    tokenizer_dir = os.path.join(root_dir, "data_engine", "_output", "muntu_tokenizer")
    output_model_path = os.path.join(base_dir, "muntu_pretrained.pt")
    

    if os.path.exists(output_model_path):
        archive_path = os.path.join(base_dir, "muntu_dense_legacy.pt")
        if os.path.exists(archive_path):
            os.remove(archive_path)
        os.rename(output_model_path, archive_path)
        print(f"[*] Ancien modèle obsolète archivé sous : {archive_path}")

    BATCH_SIZE = 16
    MAX_SEQ_LEN = 64
    LEARNING_RATE = 3e-4
    EPOCHS = 10
    
    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    print(f"[*] Entraînement configuré sur le device : {device}")

    print("[*] Préparation du Dataset et du DataLoader...")
    dataset = MuntuPretrainDataset(corpus_path, tokenizer_dir, max_seq_len=MAX_SEQ_LEN)
    dataloader = DataLoader(dataset, batch_size=BATCH_SIZE, shuffle=True, drop_last=True)


    print("[*] Initialisation du modèle MUNTU MoE LM (4 Experts)...")
    model = MuntuLM(
        vocab_size=1495,
        d_model=256,
        max_seq_len=512,
        n_layers=4
    ).to(device)
    
    optimizer = torch.optim.AdamW(model.parameters(), lr=LEARNING_RATE, weight_decay=0.01)

    print(f"Lancement du Pré-entraînement MoE pour {EPOCHS} époques...")
    model.train()
    
    for epoch in range(EPOCHS):
        total_loss = 0
        nb_batches = 0
        
        for inputs, targets in dataloader:
            inputs, targets = inputs.to(device), targets.to(device)
            
            optimizer.zero_grad()
            
            # calcule des logits et de la cross-entropy loss classique
            logits, loss = model(inputs, targets)
            
            loss.backward()
            
            torch.nn.utils.clip_grad_norm_(model.parameters(), max_norm=1.0)
            optimizer.step()
            
            total_loss += loss.item()
            nb_batches += 1
            
        epoch_loss = total_loss / nb_batches
        print(f"Epoch {epoch+1:02d}/{EPOCHS:02d} | Loss Moyenne : {epoch_loss:.4f}")

    torch.save(model.state_dict(), output_model_path)
    print(f"Entraînement terminé ! Nouveau cerveau MoE sauvegardé sous : {output_model_path}")

if __name__ == "__main__":
    train_muntu()