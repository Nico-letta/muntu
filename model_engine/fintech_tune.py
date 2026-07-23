import os
import sys
import torch
from torch.utils.data import DataLoader

sys.path.append(os.getcwd())
from model_engine.src.model import MuntuLM
from model_engine.src.dataset import MuntuPretrainDataset

def fine_tune_fintech():
    base_dir = os.path.dirname(os.path.abspath(__file__))
    root_dir = os.path.abspath(os.path.join(base_dir, ".."))

    fintech_corpus = os.path.join(root_dir, "data_engine", "_output", "corpus_fintech.txt")
    tokenizer_dir = os.path.join(root_dir, "data_engine", "_output", "muntu_tokenizer")
    pretrained_model_path = os.path.join(base_dir, "muntu_pretrained.pt")

    if not os.path.exists(fintech_corpus):
        raise FileNotFoundError(f"Crée d'abord le fichier {fintech_corpus} avec tes données Fintech.")
    if not os.path.exists(pretrained_model_path):
        raise FileNotFoundError(f"Impossible de trouver le modèle de base à spécialiser : {pretrained_model_path}")

    BATCH_SIZE = 4
    MAX_SEQ_LEN = 128
    LEARNING_RATE = 2e-5
    EPOCHS = 3

    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    print(f"[*] Fine-tuning configuré sur : {device}")

    print("[*] Préparation du Dataset Fintech...")
    dataset = MuntuPretrainDataset(fintech_corpus, tokenizer_dir, max_seq_len=MAX_SEQ_LEN)
    dataloader = DataLoader(dataset, batch_size=BATCH_SIZE, shuffle=True, drop_last=True)

    print(f"[*] Chargement du cerveau MUNTU MoE initial...")
    model = MuntuLM(
        vocab_size=dataset.vocab_size,
        d_model=768,
        max_seq_len=512,
        n_layers=4
    )

    model.load_state_dict(torch.load(pretrained_model_path, map_location=device))
    model.to(device)

    optimizer = torch.optim.AdamW(model.parameters(), lr=LEARNING_RATE, weight_decay=0.01)

    print(f"[➔] Lancement de la spécialisation sur {EPOCHS} époques...")
    model.train()

    total_batches = len(dataloader)
    for epoch in range(EPOCHS):
        total_loss = 0
        nb_batches = 0
        for inputs, targets in dataloader:
            inputs, targets = inputs.to(device), targets.to(device)

            optimizer.zero_grad()
            logits, loss = model(inputs, targets)
            loss.backward()

            torch.nn.utils.clip_grad_norm_(model.parameters(), max_norm=1.0)
            optimizer.step()

            total_loss += loss.item()
            nb_batches += 1

        epoch_loss = total_loss / nb_batches if nb_batches > 0 else 0
        print(f" -> Époque {epoch+1:02d}/{EPOCHS:02d} terminée | Loss Spécialisation : {epoch_loss:.4f}")

    specialized_model_path = os.path.join(base_dir, "muntu_fintech.pt")
    torch.save(model.state_dict(), specialized_model_path)
    print(f"\n[+] Succès ! Modèle spécialisé Fintech sauvegardé sous : {specialized_model_path}")

if __name__ == "__main__":
    fine_tune_fintech()
