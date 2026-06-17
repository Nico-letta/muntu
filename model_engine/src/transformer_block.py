import torch
import torch.nn as nn
from src.attention import MuntuCausalAttention

class MuntuFeedForward(nn.Module):
    """
    Le réseau de neurones individuel appliqué à chaque token.
    Il projette la dimension d_model vers une dimension 4 fois plus grande (4 * d_model),
    applique une non-linéarité (GELU), puis reprojette vers d_model.
    """
    def __init__(self, d_model: int):
        super().__init__()
        self.net = nn.Sequential(
            nn.Linear(d_model, 4 * d_model),
            nn.GELU(), # Non-linéarité standard et performante pour les LLM
            nn.Linear(4 * d_model, d_model)
        )

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        return self.net(x)


class MuntuTransformerBlock(nn.Module):
    """
    Un bloc Transformer complet encapsulant l'Attention, 
    le Feed-Forward, les Layer Normalizations et les connexions résiduelles.
    """
    def __init__(self, d_model: int):
        super().__init__()
        # 1. Les composants principaux
        self.attention = MuntuCausalAttention(d_model=d_model)
        self.feed_forward = MuntuFeedForward(d_model=d_model)
        
        # 2. Les deux couches de normalisation (une par sous-bloc)
        self.ln1 = nn.LayerNorm(d_model)
        self.ln2 = nn.LayerNorm(d_model)

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        # --- PRE-LN Architecture ---
        
        # Sous-bloc 1 : Normalisation -> Attention -> Connexion Résiduelle
        x = x + self.attention(self.ln1(x))
        
        # Sous-bloc 2 : Normalisation -> Feed-Forward -> Connexion Résiduelle
        x = x + self.feed_forward(self.ln2(x))
        
        return x