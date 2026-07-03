import os
import torch
from torch.utils.data import Dataset
from tokenizers import ByteLevelBPETokenizer

class MuntuPretrainDataset(Dataset):
    def __init__(self, corpus_path, tokenizer_dir, max_seq_len=128):
        self.max_seq_len = max_seq_len
        
        # 1. Chargement natif et propre du ByteLevelBPETokenizer ré-entraîné
        vocab_path = os.path.join(tokenizer_dir, "vocab.json")
        merges_path = os.path.join(tokenizer_dir, "merges.txt")
        
        if not os.path.exists(vocab_path) or not os.path.exists(merges_path):
            raise FileNotFoundError(
                f"[-] Fichiers du Tokenizer introuvables dans {tokenizer_dir}.\n"
                f"Assure-toi que 'vocab.json' et 'merges.txt' s'y trouvent bien."
            )
            
        print("[*] Chargement du dictionnaire d'embeddings MUNTU...")
        # On instancie le tokenizer via ses deux fichiers de structure
        self.tokenizer = ByteLevelBPETokenizer(vocab_path, merges_path)
        self.vocab_size = self.tokenizer.get_vocab_size()

        # 2. Lecture complète du corpus de 27.96 Mo
        print(f"[*] Chargement et tokenisation du corpus : {corpus_path}...")
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
        return self.num_samples

    def __getitem__(self, idx):
        # Saut de bloc strict : index * taille du bloc pour une vitesse maximale en GPU
        start_idx = idx * self.chunk_size
        end_idx = start_idx + self.chunk_size
        chunk = self.tokens[start_idx:end_idx]
        
        # x = inputs (de 0 à max_seq_len)
        # y = targets (de 1 à max_seq_len + 1)
        x = torch.tensor(chunk[:-1], dtype=torch.long)
        y = torch.tensor(chunk[1:], dtype=torch.long)
        
        return x, y
