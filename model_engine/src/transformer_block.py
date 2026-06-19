import torch
import torch.nn as nn
from src.attention import MuntuCausalAttention
from src.moe_layer import MuntuMoELayer  # 1. On importe notre nouvelle couche MoE

class MuntuTransformerBlock(nn.Module):
    """
    Un bloc Transformer complet encapsulant l'Attention Causale, 
    la couche Mixture of Experts (MoE), les Layer Normalizations 
    et les connexions résiduelles en architecture Pre-LN.
    """
    def __init__(self, d_model: int):
        super().__init__()
        # 1. Les composants principaux
        self.attention = MuntuCausalAttention(d_model=d_model)
        
        # 2. Remplacement chirurgical du FFN classique par le MoE
        # On configure 4 experts par défaut pour MUNTU
        self.moe_layer = MuntuMoELayer(d_model=d_model, num_experts=4)
        
        # 3. Les deux couches de normalisation (Pre-LN)
        self.ln1 = nn.LayerNorm(d_model)
        self.ln2 = nn.LayerNorm(d_model)

    def forward(self, x: torch.Tensor):
        # Sous-bloc 1
        x = x + self.attention(self.ln1(x))
        
        # Sous-bloc 2 : On récupère la sortie et la perte aux du MoE
        moe_out, aux_loss = self.moe_layer(self.ln2(x))
        x = x + moe_out
        
        return x, aux_loss # On fait remonter aux_loss