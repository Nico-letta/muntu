import os
import sys
import math
import torch
from torch.utils.data import DataLoader
from torch.optim.lr_scheduler import LambdaLR
from safetensors.torch import save_file
from tqdm import tqdm 

sys.path.append(os.getcwd())
from model_engine.src.model import MuntuLM
from model_engine.src.dataset import MuntuPretrainDataset

def get_cosine_schedule_with_warmup(optimizer, num_warmup_steps, num_training_steps, min_lr_ratio=0.1):
    def lr_lambda(current_step):
        if current_step < num_warmup_steps:
            return float(current_step) / float(max(1, num_warmup_steps))
        progress = float(current_step - num_warmup_steps) / float(max(1, num_training_steps - num_warmup_steps))
        cosine_decay = 0.5 * (1.0 + math.cos(math.pi * progress))
        return min_lr_ratio + (1.0 - min_lr_ratio) * cosine_decay
    return LambdaLR(optimizer, lr_lambda)


def train_muntu():
    base_dir = os.path.dirname(os.path.abspath(__file__))

    bin_path = "/content/drive/MyDrive/muntu_project/data_engine/_output/corpus_pretrain.bin"
    tokenizer_dir = "/content/drive/MyDrive/muntu_project/data_engine/_output/muntu_tokenizer"
    
    checkpoint_dir = os.path.join(base_dir, "checkpoints")
    os.makedirs(checkpoint_dir, exist_ok=True)
    checkpoint_path = os.path.join(checkpoint_dir, "muntu_latest_checkpoint.pt")
    
    output_model_path = os.path.join(base_dir, "muntu_pretrained.safetensors")
    
    if os.path.exists(output_model_path) and not os.path.exists(checkpoint_path):
        archive_path = os.path.join(base_dir, "muntu_legacy_small_vocab.safetensors")
        if os.path.exists(archive_path):
            os.remove(archive_path)
        os.rename(output_model_path, archive_path)
        print(f"[*] Ancien modèle final archivé sous : {archive_path}")

    MICRO_BATCH_SIZE = 1         
    GRAD_ACC_STEPS = 32         
    MAX_SEQ_LEN = 4096           
    LEARNING_RATE = 2e-4         
    EPOCHS = 1             
    AUX_LOSS_COEF = 5e-3  
    
    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    print(f"[*] Entraînement configuré sur le device : {device}")

    print("[*] Préparation du Dataset et du DataLoader...")
    dataset = MuntuPretrainDataset(bin_path, tokenizer_dir, max_seq_len=MAX_SEQ_LEN)
    dataloader = DataLoader(dataset, batch_size=MICRO_BATCH_SIZE, shuffle=True, drop_last=True)

    total_batches = len(dataloader)
    
    total_optimization_steps = (total_batches // GRAD_ACC_STEPS) * EPOCHS
    warmup_steps = int(0.05 * total_optimization_steps) 

    print(f"[*] Initialisation du modèle MUNTU MoE (Vocab : {dataset.vocab_size} tokens)...")
    model = MuntuLM(
        vocab_size=dataset.vocab_size,
        d_model=768,
        max_seq_len=MAX_SEQ_LEN, 
        n_layers=4
    ).to(device)
    
    optimizer = torch.optim.AdamW(model.parameters(), lr=LEARNING_RATE, weight_decay=0.01)
    scheduler = get_cosine_schedule_with_warmup(optimizer, warmup_steps, total_optimization_steps)
    scaler = torch.amp.GradScaler("cuda") if device.type == "cuda" else None

    start_epoch = 0
    if os.path.exists(checkpoint_path):
        print(f"Checkpoint détecté ! Chargement des états depuis {checkpoint_path}...")
        checkpoint = torch.load(checkpoint_path, map_location=device)
        model.load_state_dict(checkpoint['model_state_dict'])
        optimizer.load_state_dict(checkpoint['optimizer_state_dict'])
        if 'scheduler_state_dict' in checkpoint:
            scheduler.load_state_dict(checkpoint['scheduler_state_dict'])

        last_completed_epoch = checkpoint['epoch']
        start_epoch = last_completed_epoch + 1
        
        print(f"[+] Reprise validée à partir de l'Époque {start_epoch + 1}")

    print(f"Lancement du Pré-entraînement MoE ({EPOCHS - start_epoch} époques restantes)...")
    model.train()
    
    for epoch in range(start_epoch, EPOCHS):
        total_loss = 0
        nb_batches = 0
        optimizer.zero_grad(set_to_none=True)

        progress_bar = tqdm(dataloader, desc=f"Époque {epoch+1:02d}/{EPOCHS:02d}", unit="batch")
        
        for inputs, targets in progress_bar:
            inputs, targets = inputs.to(device), targets.to(device)

            if device.type == "cuda":
                with torch.amp.autocast("cuda"):
                    outputs = model(inputs, targets)
                    if isinstance(outputs, tuple) and len(outputs) == 3:
                        logits, main_loss, total_aux_loss = outputs
                        loss = main_loss + (AUX_LOSS_COEF * total_aux_loss)
                    else:
                        logits, loss = outputs 
                    loss = loss / GRAD_ACC_STEPS
                scaler.scale(loss).backward()
            else:
                outputs = model(inputs, targets)
                if isinstance(outputs, tuple) and len(outputs) == 3:
                    logits, main_loss, total_aux_loss = outputs
                    loss = main_loss + (AUX_LOSS_COEF * total_aux_loss)
                else:
                    logits, loss = outputs
                
                loss = loss / GRAD_ACC_STEPS
                loss.backward()
            
            total_loss += loss.item() * GRAD_ACC_STEPS
            nb_batches += 1

            if nb_batches % GRAD_ACC_STEPS == 0 or nb_batches == total_batches:
                if scaler:
                    scaler.unscale_(optimizer)
                    torch.nn.utils.clip_grad_norm_(model.parameters(), max_norm=1.0)
                    scaler.step(optimizer)
                    scaler.update()
                else:
                    torch.nn.utils.clip_grad_norm_(model.parameters(), max_norm=1.0)
                    optimizer.step()

                scheduler.step()
                optimizer.zero_grad(set_to_none=True)

            if nb_batches % 10 == 0:
                current_loss = loss.item() * GRAD_ACC_STEPS
                current_lr = scheduler.get_last_lr()[0]
                current_ppl = math.exp(min(current_loss, 20))

                progress_bar.set_postfix({
                    "Loss": f"{current_loss:.4f}",
                    "PPL": f"{current_ppl:.1f}",
                    "LR": f"{current_lr:.1e}"
                })

            if nb_batches % 500 == 0:
                torch.save({
                    'epoch': epoch,
                    'model_state_dict': model.state_dict(),
                    'optimizer_state_dict': optimizer.state_dict(),
                    'scheduler_state_dict': scheduler.state_dict(),
                }, checkpoint_path)
            
        epoch_loss = total_loss / nb_batches
        print(f"\n=== ÉPOQUE {epoch+1:02d}/{EPOCHS:02d} TERMINÉE | Loss Moyenne : {epoch_loss:.4f} ===")

        torch.save({
            'epoch': epoch,
            'model_state_dict': model.state_dict(),
            'optimizer_state_dict': optimizer.state_dict(),
            'scheduler_state_dict': scheduler.state_dict(),
        }, checkpoint_path)
        print(f"Checkpoint d'époque validé et écrit.")
    state_dict = model.state_dict()

    state_dict_to_save = {}
    for k, v in state_dict.items():
        state_dict_to_save[k] = v.clone()

    save_file(state_dict_to_save, output_model_path)
    
    if os.path.exists(checkpoint_path):
        os.remove(checkpoint_path)
        
    print(f"Entraînement massif terminé ! Cerveau MoE final exporté sous : {output_model_path}")

if __name__ == "__main__":
    train_muntu()