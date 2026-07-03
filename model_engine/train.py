import os
import sys
import torch
from torch.utils.data import DataLoader

sys.path.append(os.getcwd())
from model_engine.src.model import MuntuLM
from model_engine.src.dataset import MuntuPretrainDataset

def train_muntu():
    base_dir = os.path.dirname(os.path.abspath(__file__))
    root_dir = os.path.abspath(os.path.join(base_dir, ".."))
    
    corpus_path = os.path.join(root_dir, "data_engine", "_output", "corpus_pretrain.txt")
    tokenizer_dir = os.path.join(root_dir, "data_engine", "_output", "muntu_tokenizer")
    
    # Configuration des dossiers de sauvegarde
    checkpoint_dir = os.path.join(base_dir, "checkpoints")
    os.makedirs(checkpoint_dir, exist_ok=True)
    checkpoint_path = os.path.join(checkpoint_dir, "muntu_latest_checkpoint.pt")
    output_model_path = os.path.join(base_dir, "muntu_pretrained.pt")
    
    # Archivage  si un vieux fichier traîne
    if os.path.exists(output_model_path) and not os.path.exists(checkpoint_path):
        archive_path = os.path.join(base_dir, "muntu_legacy_small_vocab.pt")
        if os.path.exists(archive_path):
            os.remove(archive_path)
        os.rename(output_model_path, archive_path)
        print(f"[*] Ancien modèle final archivé sous : {archive_path}")

    BATCH_SIZE = 32          
    MAX_SEQ_LEN = 128        
    LEARNING_RATE = 5e-4     
    EPOCHS = 5               
    
    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    print(f"[*] Entraînement configuré sur le device : {device}")

    print("[*] Préparation du Dataset et du DataLoader...")
    dataset = MuntuPretrainDataset(corpus_path, tokenizer_dir, max_seq_len=MAX_SEQ_LEN)
    dataloader = DataLoader(dataset, batch_size=BATCH_SIZE, shuffle=True, drop_last=True)


    total_batches = len(dataloader)
    file_size_bytes = os.path.getsize(corpus_path)
    
    # Estimation théorique : taille fichier / (B * T) avec une marge de sécurité de 3x pour le chevauchement
    max_batches_theorique = file_size_bytes / (BATCH_SIZE * MAX_SEQ_LEN)
    seuil_alerte = int(max_batches_theorique * 3)
    
    print(f"[➔] VÉRIFICATION : Nombre total de batches par époque : {total_batches} (Seuil max estimé : {seuil_alerte})")
    if total_batches > seuil_alerte and total_batches > 10:
        file_size_mo = file_size_bytes / (1024 * 1024)
        print(f"DANGER : Le nombre de batches ({total_batches}) est anormalement élevé pour la taille du fichier ({file_size_mo:.2f} Mo). Produit des séquences redondantes ou infinies.")

    print(f"[*] Initialisation du modèle MUNTU MoE (Vocab : {dataset.vocab_size} tokens)...")
    model = MuntuLM(
        vocab_size=dataset.vocab_size,
        d_model=256,
        max_seq_len=512,
        n_layers=4
    ).to(device)
    
    optimizer = torch.optim.AdamW(model.parameters(), lr=LEARNING_RATE, weight_decay=0.01)

    start_epoch = 0
    if os.path.exists(checkpoint_path):
        print(f"Checkpoint détecté ! Chargement des états depuis {checkpoint_path}...")
        checkpoint = torch.load(checkpoint_path, map_location=device)
        model.load_state_dict(checkpoint['model_state_dict'])
        optimizer.load_state_dict(checkpoint['optimizer_state_dict'])
        start_epoch = checkpoint['epoch'] + 1
        print(f"[+] Reprise validée à partir de l'Époque {start_epoch + 1}")

    print(f"Lancement du Pré-entraînement MoE ({EPOCHS - start_epoch} époques restantes)...")
    model.train()
    
    for epoch in range(start_epoch, EPOCHS):
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
            
            # Logs plus réguliers pour observer le rythme (toutes les 50 itérations)
            if nb_batches % 50 == 0:
                print(f" -> Époque {epoch+1:02d}/{EPOCHS:02d} | Batch {nb_batches}/{total_batches} | Loss courante : {loss.item():.4f}")
            
            # Sauvegarde de secours(tous les 500 batches)
            if nb_batches % 500 == 0:
                torch.save({
                    'epoch': epoch,
                    'model_state_dict': model.state_dict(),
                    'optimizer_state_dict': optimizer.state_dict(),
                }, checkpoint_path)
                print(f"Sauvegarde automatique de secours effectuée (Batch {nb_batches})")
            
        epoch_loss = total_loss / nb_batches
        print(f"=== ÉPOQUE {epoch+1:02d}/{EPOCHS:02d} TERMINÉE | Loss Moyenne : {epoch_loss:.4f} ===")
        
        torch.save({
            'epoch': epoch,
            'model_state_dict': model.state_dict(),
            'optimizer_state_dict': optimizer.state_dict(),
        }, checkpoint_path)
        print(f"Checkpoint d'époque validé et écrit.")

    torch.save(model.state_dict(), output_model_path)
    if os.path.exists(checkpoint_path):
        os.remove(checkpoint_path)
        
    print(f"Entraînement massif terminé ! Cerveau MoE final exporté sous : {output_model_path}")

if __name__ == "__main__":
    train_muntu()