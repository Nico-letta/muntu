import torch
import torch.nn as nn

class MuntuEmbedding(nn.Module):
    def __init__(self, vocab_size: int, d_model: int, max_seq_len: int):
        """
        vocab_size : Taille du vocabulaire
        d_model    : Dimension cachée du vecteur 
        max_seq_len: Longueur maximale du contexte
        """
        super().__init__()

        self.token_embedding = nn.Embedding(vocab_size, d_model)

        self.position_embedding = nn.Embedding(max_seq_len, d_model)
        
    def forward(self, input_ids: torch.Tensor) -> torch.Tensor:
        """
        input_ids: Tensor de forme (batch_size, seq_len) contenant les IDs des tokens
        """
        seq_len = input_ids.size(1)
        device = input_ids.device

        positions = torch.arange(0, seq_len, dtype=torch.long, device=device)
        positions = positions.unsqueeze(0) 
        
        tok_emb = self.token_embedding(input_ids)     # shape: (batch_size, seq_len, d_model)
        pos_emb = self.position_embedding(positions) # shape: (1, seq_len, d_model)
        
        return tok_emb + pos_emb