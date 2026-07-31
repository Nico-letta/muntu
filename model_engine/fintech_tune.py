import os
import sys
import math
import json
import torch
from torch.utils.data import Dataset, DataLoader
from safetensors.torch import load_file
from tqdm import tqdm

sys.path.append(os.getcwd())
from model_engine.src.model import MuntuLM
from tokenizers import Tokenizer

class MuntuSFTDataset(Dataset):
    """Dataset dedicated to parsing ChatML JSONL pairs for SFT instruction tuning."""
    def __init__(self, jsonl_path, tokenizer_dir, max_seq_len=4096):
        self.max_seq_len = max_seq_len

        tokenizer_file = os.path.join(tokenizer_dir, "tokenizer.json")
        if not os.path.exists(tokenizer_file):
            raise FileNotFoundError(f"Tokenizer not found at {tokenizer_file}")
        self.tokenizer = Tokenizer.from_file(tokenizer_file)
        self.vocab_size = self.tokenizer.get_vocab_size()

        self.samples = []
        with open(jsonl_path, "r", encoding="utf-8") as f:
            for line in f:
                if line.strip():
                    data = json.loads(line)
                    self.samples.append(data["text"])

    def __len__(self):
        return len(self.samples)

    def __getitem__(self, idx):
        raw_text = self.samples[idx]
        encoding = self.tokenizer.encode(raw_text)
        tokens = encoding.ids

        if len(tokens) > self.max_seq_len + 1:
            tokens = tokens[: self.max_seq_len + 1]

        inputs = torch.tensor(tokens[:-1], dtype=torch.long)
        targets = torch.tensor(tokens[1:], dtype=torch.long)

        if len(inputs) < self.max_seq_len:
            pad_len = self.max_seq_len - len(inputs)
            pad_id = self.tokenizer.token_to_id("<pad>") or 0
            inputs = torch.cat([inputs, torch.full((pad_len,), pad_id, dtype=torch.long)])
            targets = torch.cat([targets, torch.full((pad_len,), -100, dtype=torch.long)]) 

        return inputs, targets


def fine_tune_fintech():
    base_dir = os.path.dirname(os.path.abspath(__file__)) if '__file__' in globals() else os.getcwd()
    root_dir = os.path.abspath(os.path.join(base_dir, ".."))

    sft_jsonl_path = os.path.join(root_dir, "data_engine", "_output", "sft_dataset.jsonl")
    tokenizer_dir = os.path.join(root_dir, "data_engine", "_output", "muntu_tokenizer")
    pretrained_model_path = os.path.join(base_dir, "muntu_pretrained.safetensors")

    if not os.path.exists(sft_jsonl_path):
        raise FileNotFoundError(f"Missing SFT dataset file: {sft_jsonl_path}")
    if not os.path.exists(pretrained_model_path):
        raise FileNotFoundError(f"Base model checkpoint missing: {pretrained_model_path}")

    BATCH_SIZE = 2
    GRAD_ACC_STEPS = 4
    MAX_SEQ_LEN = 4096  # Alignement strict sur la taille du pré-entraînement (4096)
    LEARNING_RATE = 2e-5
    EPOCHS = 3
    AUX_LOSS_COEF = 5e-3

    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    print(f"[*] Fine-tuning SFT configured on: {device}")

    print("[*] Preparing SFT ChatML Dataset...")
    dataset = MuntuSFTDataset(sft_jsonl_path, tokenizer_dir, max_seq_len=MAX_SEQ_LEN)
    dataloader = DataLoader(dataset, batch_size=BATCH_SIZE, shuffle=True, drop_last=True)

    print(f"[*] Initializing MUNTU MoE Architecture (Vocab: {dataset.vocab_size} tokens)...")
    model = MuntuLM(
        vocab_size=dataset.vocab_size,
        d_model=768,
        max_seq_len=MAX_SEQ_LEN,
        n_layers=4
    )

    print(f"[*] Loading pretrained Safetensors weights from {pretrained_model_path}...")
    weights = load_file(pretrained_model_path)
    model.load_state_dict(weights, strict=True)
    model.to(device)

    optimizer = torch.optim.AdamW(model.parameters(), lr=LEARNING_RATE, weight_decay=0.01)
    scaler = torch.amp.GradScaler("cuda") if device.type == "cuda" else None

    print(f"[➔] Starting SFT Specialization on {len(dataset)} samples across {EPOCHS} epochs...")
    model.train()

    total_batches = len(dataloader)
    for epoch in range(EPOCHS):
        total_loss = 0
        nb_batches = 0
        optimizer.zero_grad(set_to_none=True)

        progress_bar = tqdm(dataloader, desc=f"SFT Epoch {epoch+1:02d}/{EPOCHS:02d}", unit="batch")

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
                optimizer.zero_grad(set_to_none=True)

            progress_bar.set_postfix({"Loss": f"{loss.item() * GRAD_ACC_STEPS:.4f}"})

        epoch_loss = total_loss / nb_batches if nb_batches > 0 else 0
        print(f"\n -> Epoch {epoch+1:02d}/{EPOCHS:02d} Complete | Average SFT Loss: {epoch_loss:.4f}")

    specialized_model_path = os.path.join(base_dir, "muntu_fintech.safetensors")
    
    state_dict_to_save = {k: v.clone() for k, v in model.state_dict().items()}
    from safetensors.torch import save_file
    save_file(state_dict_to_save, specialized_model_path)
    
    print(f"\n[+] Success! Specialized MUNTU Fintech model saved at: {specialized_model_path}")

if __name__ == "__main__":
    fine_tune_fintech()
