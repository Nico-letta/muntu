import os
import torch
from torch.utils.data import Dataset
from tokenizers import ByteLevelBPETokenizer

class MuntuPretrainDataset(Dataset):
    def __init__(self, corpus_path: str, tokenizer_dir: str, max_seq_len: int = 64):
        """
        corpus_path  : Chemin vers ton fichier corpus_pretrain.txt
        tokenizer_dir: Chemin vers le dossier de ton tokeniseur (vocab.json, merges.txt)
        max_seq_len  : La taille de la fenêtre de contexte (ex: 64 tokens pour notre petit corpus)
        """
        self.max_seq_len = max_seq_len

        tokenizer = ByteLevelBPETokenizer(
            os.path.join(tokenizer_dir, "vocab.json"),
            os.path.join(tokenizer_dir, "merges.txt")
        )

        with open(corpus_path, "r", encoding="utf-8") as f:
            full_text = f.read()
            
        encoded = tokenizer.encode(full_text)
        self.tokens = encoded.ids
        
        print(f"[+] Dataset chargé : {len(self.tokens)} tokens au total dans le corpus.")

    def __len__(self):
        
        return len(self.tokens) - self.max_seq_len

    def __getitem__(self, idx):

        chunk = self.tokens[idx : idx + self.max_seq_len + 1]

        tensor_chunk = torch.tensor(chunk, dtype=torch.long)

        x = tensor_chunk[:-1] # Input 
        y = tensor_chunk[1:]  # Target
        
        return x, y