import torch
import torch.nn as nn
import torch.nn.functional as F

class MuntuCausalAttention(nn.Module):
    def __init__(self, d_model: int):
        super().__init__()
        self.d_model = d_model
        
        self.q_proj = nn.Linear(d_model, d_model)
        self.k_proj = nn.Linear(d_model, d_model)
        self.v_proj = nn.Linear(d_model, d_model)
        
        self.out_proj = nn.Linear(d_model, d_model)

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        """
        x: Tenseur d'embeddings en entrée de forme (Batch_size, Seq_len, d_model)
        """
        B, T, C = x.shape 
        
        q = self.q_proj(x) 
        k = self.k_proj(x) 
        v = self.v_proj(x) 
        
        # Calcul des scores d'affinité (Matrice d'Attention)
        scores = torch.bmm(q, k.transpose(1, 2)) * (1.0 / (C ** 0.5)) # (B, T, T)
        
        # Masque Causal matrice triangulaire supérieure de 1
        mask = torch.triu(torch.ones(T, T, device=x.device), diagonal=1).bool()
        scores = scores.masked_fill(mask.unsqueeze(0), float('-inf'))
        
        attention_weights = F.softmax(scores, dim=-1) # (B, T, T)
        
        context = torch.bmm(attention_weights, v) # (B, T, C)

        return self.out_proj(context) 