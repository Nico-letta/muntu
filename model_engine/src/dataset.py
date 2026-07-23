import os
import json
import torch
from torch.utils.data import Dataset
import numpy as np

class MuntuPretrainDataset(Dataset):
    def __init__(self, bin_path, tokenizer_dir, max_seq_len=4096):
        """
        Dataset de pré-entraînement optimisé pour MUNTU.
        - bin_path: Chemin vers le fichier binaire `.bin` (uint16)
        - tokenizer_dir: Répertoire contenant 'vocab.json' pour extraire la taille du vocabulaire
        - max_seq_len: Taille de la fenêtre de contexte (block_size)
        """
        self.max_seq_len = max_seq_len
        self.bin_path = bin_path

        vocab_path = os.path.join(tokenizer_dir, "vocab.json")
        if not os.path.exists(vocab_path):
            raise FileNotFoundError(f"[-] Fichier 'vocab.json' introuvable dans {tokenizer_dir}")
            
        with open(vocab_path, "r", encoding="utf-8") as f:
            vocab = json.load(f)
        self.vocab_size = len(vocab)
        
        if not os.path.exists(bin_path):
            raise FileNotFoundError(f"[-] Fichier binaire introuvable : {bin_path}")
            
        print(f"[*] Cartographie mémoire du corpus binaire : {bin_path}...")

        self.data = np.memmap(bin_path, dtype=np.uint16, mode='r')

        self.num_samples = (len(self.data) - 1) // self.max_seq_len
        
        if self.num_samples == 0:
            raise ValueError("Le corpus binaire est trop petit pour la taille de fenêtre (max_seq_len) demandée.")
            
        print(f"[+] Dataset prêt : {len(self.data):,} tokens cartographiés.")
        print(f"[+] {self.num_samples} séquences d'entraînement uniques (sans chevauchement).")
        print(f"[+] Taille du vocabulaire détectée : {self.vocab_size} tokens.")

    def __len__(self):
        return self.num_samples

    def __getitem__(self, idx):
        start_idx = idx * self.max_seq_len
        end_idx = start_idx + self.max_seq_len + 1
        
        chunk = self.data[start_idx:end_idx]

        if len(chunk) < self.max_seq_len + 1:
            end_idx = len(self.data)
            start_idx = end_idx - (self.max_seq_len + 1)
            chunk = self.data[start_idx:end_idx]

        x = torch.tensor(chunk[:-1].astype(np.int64), dtype=torch.long)
        y = torch.tensor(chunk[1:].astype(np.int64), dtype=torch.long)
        
        return x, y
