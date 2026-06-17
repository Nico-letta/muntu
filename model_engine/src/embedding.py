import torch
import torch.nn as nn

class MuntuEmbedding(nn.Module):
    def __init__(self, vocab_size: int, d_model: int, max_seq_len: int):
        """
        vocab_size : Taille de ton vocabulaire (1500 pour MUNTU)
        d_model    : Dimension cachée de ton vecteur (ex: 256)
        max_seq_len: Longueur maximale du contexte (ex: 512 tokens)
        """
        super().__init__()
        
        # 1. La table de correspondance pour les tokens
        self.token_embedding = nn.Embedding(vocab_size, d_model)
        
        # 2. La table de correspondance pour les positions
        self.position_embedding = nn.Embedding(max_seq_len, d_model)
        
    def forward(self, input_ids: torch.Tensor) -> torch.Tensor:
        """
        input_ids: Tensor de forme (batch_size, seq_len) contenant les IDs des tokens
        """
        seq_len = input_ids.size(1)
        device = input_ids.device
        
        # Générer les indices de position [0, 1, 2, ..., seq_len - 1]
        positions = torch.arange(0, seq_len, dtype=torch.long, device=device)
        # Ajuster la forme pour le batch -> (1, seq_len)
        positions = positions.unsqueeze(0) 
        
        # Calculer les deux types d'embeddings
        tok_emb = self.token_embedding(input_ids)     # Forme: (batch_size, seq_len, d_model)
        pos_emb = self.position_embedding(positions) # Forme: (1, seq_len, d_model)
        
        # La magie du Transformer : on additionne simplement la sémantique et la position
        return tok_emb + pos_emb