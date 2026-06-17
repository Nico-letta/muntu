import torch
import torch.nn as nn
import torch.nn.functional as F

class MuntuCausalAttention(nn.Module):
    def __init__(self, d_model: int):
        super().__init__()
        self.d_model = d_model
        
        # Les trois projections linéaires pour transformer nos embeddings en Q, K, V
        self.q_proj = nn.Linear(d_model, d_model)
        self.k_proj = nn.Linear(d_model, d_model)
        self.v_proj = nn.Linear(d_model, d_model)
        
        # Projection finale de sortie
        self.out_proj = nn.Linear(d_model, d_model)

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        """
        x: Tenseur d'embeddings en entrée de forme (Batch_size, Seq_len, d_model)
        """
        B, T, C = x.shape # Batch_size, Seq_len (Time), Channels (d_model)
        
        # 1. Calcul des Query, Key, Value
        q = self.q_proj(x) # (B, T, C)
        k = self.k_proj(x) # (B, T, C)
        v = self.v_proj(x) # (B, T, C)
        
        # 2. Calcul des scores d'affinité (Matrice d'Attention)
        # On multiplie Q par K transposée pour croiser chaque mot avec tous les autres.
        # On divise par la racine carrée de la dimension (scaled dot-product) pour stabiliser les gradients.
        scores = torch.bmm(q, k.transpose(1, 2)) * (1.0 / (C ** 0.5)) # (B, T, T)
        
        # 3. Application du Masque Causal (Bloquer le futur)
        # On crée une matrice triangulaire supérieure de 1 (au-dessus de la diagonale principale)
        mask = torch.triu(torch.ones(T, T, device=x.device), diagonal=1).bool()
        # Là où le masque est vrai (le futur), on force le score à -infini
        scores = scores.masked_fill(mask.unsqueeze(0), float('-inf'))
        
        # 4. Softmax pour convertir les scores en probabilités (les poids d'attention)
        # Le -infini devient un 0 net après Softmax : le futur est totalement ignoré.
        attention_weights = F.softmax(scores, dim=-1) # (B, T, T)
        
        # 5. Agrégation des valeurs
        # On multiplie les poids par V pour obtenir la nouvelle représentation contextuelle
        context = torch.bmm(attention_weights, v) # (B, T, C)
        
        # 6. Projection finale
        return self.out_proj(context) 