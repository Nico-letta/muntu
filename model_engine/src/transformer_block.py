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
        self.attention = MuntuCausalAttention(d_model=d_model)
        
        self.moe_layer = MuntuMoELayer(d_model=d_model, num_experts=4)
        
        self.ln1 = nn.LayerNorm(d_model)
        self.ln2 = nn.LayerNorm(d_model)

    def forward(self, x: torch.Tensor):
        # Sous-bloc 1
        x = x + self.attention(self.ln1(x))
        
        moe_out, aux_loss = self.moe_layer(self.ln2(x))
        x = x + moe_out
        
        return x, aux_loss