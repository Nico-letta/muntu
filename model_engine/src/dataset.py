import os
import torch
from torch.utils.data import Dataset
from tokenizers import ByteLevelBPETokenizer

class MuntuPretrainDataset(Dataset):
    def __init__(self, corpus_path, tokenizer_dir, max_seq_len=128):
        self.max_seq_len = max_seq_len

        tokenizer = ByteLevelBPETokenizer(
            os.path.join(tokenizer_dir, "vocab.json"),
            os.path.join(tokenizer_dir, "merges.txt")
        )

        with open(corpus_path, "r", encoding="utf-8") as f:
            raw_text = f.read()

        # Encodage complet du texte via notre nouveau tokenizer calibré
        encoded = self.tokenizer.encode(raw_text)
        self.tokens = encoded.ids
        
        print(f"[+] Nombre total de tokens réels extraits : {len(self.tokens)} (Taille réelle du Vocabulaire : {self.vocab_size} tokens)")

        # 3. Découpage en blocs disjoints stricts (Chunking sans chevauchement)
        # Chaque bloc prend max_seq_len + 1 tokens pour créer le décalage Input -> Target
        self.chunk_size = self.max_seq_len + 1
        self.num_samples = len(self.tokens) // self.chunk_size
        
        print(f"[+] Dataset finalisé avec {self.num_samples} séquences d'entraînement uniques.")

    def __len__(self):
        
        return len(self.tokens) - self.max_seq_len

    def __getitem__(self, idx):

        chunk = self.tokens[idx : idx + self.max_seq_len + 1]

        tensor_chunk = torch.tensor(chunk, dtype=torch.long)

        x = tensor_chunk[:-1] # Input 
        y = tensor_chunk[1:]  # Target
        
        return x, y
