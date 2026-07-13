import os
import torch
from torch.utils.data import Dataset
from tokenizers import ByteLevelBPETokenizer

class MuntuPretrainDataset(Dataset):
    def __init__(self, corpus_path, tokenizer_dir, max_seq_len=4096):
        self.max_seq_len = max_seq_len

        vocab_path = os.path.join(tokenizer_dir, "vocab.json")
        merges_path = os.path.join(tokenizer_dir, "merges.txt")
        
        if not os.path.exists(vocab_path) or not os.path.exists(merges_path):
            raise FileNotFoundError(
                f"[-] Fichiers du Tokenizer introuvables dans {tokenizer_dir}.\n"
                f"Assure-toi que 'vocab.json' et 'merges.txt' s'y trouvent bien."
            )
            
        print("[*] Chargement du dictionnaire d'embeddings MUNTU...")
        self.tokenizer = ByteLevelBPETokenizer(vocab_path, merges_path)
        self.vocab_size = self.tokenizer.get_vocab_size()

        print(f"[*] Chargement et tokenisation progressive du corpus : {corpus_path}...")

        self.tokens = []
        with open(corpus_path, "r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if line:  
                    self.tokens.extend(self.tokenizer.encode(line).ids)

        print(f"[+] Nombre total de tokens réels extraits : {len(self.tokens)} (Taille réelle du Vocabulaire : {self.vocab_size} tokens)")
    
        self.num_samples = (len(self.tokens) - 1) // self.max_seq_len
        
        if self.num_samples == 0:
            raise ValueError("Le corpus est trop petit pour la taille de fenêtre (max_seq_len) demandée.")
        
        print(f"[+] Dataset finalisé avec {self.num_samples} séquences d'entraînement uniques (sans chevauchement).")

    def __len__(self):
        return self.num_samples

    def __getitem__(self, idx):
        start_idx = idx * self.max_seq_len
        end_idx = start_idx + self.max_seq_len + 1
        
        chunk = self.tokens[start_idx:end_idx]
        
        if len(chunk) < self.max_seq_len + 1:
            end_idx = len(self.tokens)
            start_idx = end_idx - (self.max_seq_len + 1)
            chunk = self.tokens[start_idx:end_idx]
            
        x = torch.tensor(chunk[:-1], dtype=torch.long)
        y = torch.tensor(chunk[1:], dtype=torch.long)
        
        return x, y