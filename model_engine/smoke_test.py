
import os
import sys
import torch
import torch.nn as nn
from torch.utils.data import Dataset, DataLoader
from transformers import AutoTokenizer
import time

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from src.model import MuntuLM

# ==========================================
# CONFIGURATION MATÉRIELLE & ENTRAÎNEMENT
# ==========================================
CORPUS_PATH = "/content/drive/MyDrive/muntu_project/data_engine/_output/corpus_pretrain.txt"
TOKENIZER_NAME = "Qwen/Qwen2.5-Coder-1.5B"


CONTEXT_LENGTH = 4096  
VOCAB_SIZE = 151936    
D_MODEL = 256          
N_LAYERS = 4           


BATCH_SIZE = 1         
GRAD_ACC_STEPS = 4     

# ==========================================
# DATASET CAUSAL PAR TRANCHES DE 4096
# ==========================================
class MuntuDataset(Dataset):
    def __init__(self, corpus_path, tokenizer_name, max_len):
        tokenizer = AutoTokenizer.from_pretrained(tokenizer_name)
        with open(corpus_path, "r", encoding="utf-8") as f:
            text = f.read()
        
        print("[*] Tokenisation du corpus complet...")
        self.tokens = tokenizer.encode(text, add_special_tokens=False)
        self.max_len = max_len

    def __len__(self):
        return len(self.tokens) // self.max_len

    def __getitem__(self, idx):
        start = idx * self.max_len
        end = start + self.max_len
        
        x = torch.tensor(self.tokens[start:end], dtype=torch.long)
        y = torch.tensor(self.tokens[start+1:end+1], dtype=torch.long)
        
        if len(y) < self.max_len:
            padding = torch.zeros(self.max_len - len(y), dtype=torch.long)
            y = torch.cat([y, padding])
        return x, y

# ==========================================
# EXÉCUTION DU DIAGNOSTIC
# ==========================================
def run_diagnostic():
    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    print(f"[*] Démarrage du Smoke Test sur : {device}")

    dataset = MuntuDataset(CORPUS_PATH, TOKENIZER_NAME, CONTEXT_LENGTH)
    dataloader = DataLoader(dataset, batch_size=BATCH_SIZE, shuffle=True)

    print("[*] Initialisation de MuntuLM...")
    model = MuntuLM(
        vocab_size=VOCAB_SIZE, 
        d_model=D_MODEL, 
        max_seq_len=CONTEXT_LENGTH, 
        n_layers=N_LAYERS
    ).to(device)

    optimizer = torch.optim.AdamW(model.parameters(), lr=1e-4)
    scaler = torch.amp.GradScaler("cuda") if device.type == "cuda" else None

    model.train()
    print("[*] Envoi des 5 itérations de contrôle...")
    optimizer.zero_grad(set_to_none=True)

    for step, (x, y) in enumerate(dataloader):
        if step >= 5:
            break
            
        x, y = x.to(device), y.to(device)

        if device.type == "cuda":
            with torch.amp.autocast("cuda"):
                logits, loss = model(x, targets=y)
                loss = loss / GRAD_ACC_STEPS
            scaler.scale(loss).backward()
        else:
            logits, loss = model(x, targets=y)
            loss = loss / GRAD_ACC_STEPS
            loss.backward()

        if (step + 1) % GRAD_ACC_STEPS == 0 or step == 4:
            if scaler:
                scaler.step(optimizer)
                scaler.update()
            else:
                optimizer.step()
            optimizer.zero_grad(set_to_none=True)

        if device.type == "cuda":
            mem = torch.cuda.memory_allocated() / (1024 ** 2)
            peak = torch.cuda.max_memory_allocated() / (1024 ** 2)
            print(f"Step {step+1}/5 | Loss calculée: {loss.item()*GRAD_ACC_STEPS:.4f} | VRAM: {mem:.1f}MB (Peak: {peak:.1f}MB)")
        else:
            print(f"Step {step+1}/5 | Loss calculée: {loss.item()*GRAD_ACC_STEPS:.4f} | Mode CPU")

        torch.cuda.empty_cache()

    print("\n[+] Diagnostic validé ! Ton architecture réelle compile et encaisse le flux sans OOM.")

if __name__ == "__main__":
    run_diagnostic()
