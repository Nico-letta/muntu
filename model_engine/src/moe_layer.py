import torch
import torch.nn as nn
import torch.nn.functional as F

class MuntuExpert(nn.Module):
    def __init__(self, d_model: int):
        super().__init__()
        self.w1 = nn.Linear(d_model, 4 * d_model)
        self.w2 = nn.Linear(4 * d_model, d_model)
        self.act = nn.GELU()
        self.dropout = nn.Dropout(0.1)

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        return self.dropout(self.w2(self.act(self.w1(x))))


class MuntuMoELayer(nn.Module):
    def __init__(self, d_model: int, num_experts: int = 4):
        super().__init__()
        self.num_experts = num_experts
        self.experts = nn.ModuleList([MuntuExpert(d_model) for _ in range(num_experts)])
        self.router = nn.Linear(d_model, num_experts, bias=False)

    def forward(self, x: torch.Tensor):
        orig_shape = x.shape
        B, T, C = orig_shape
        x_flat = x.view(-1, C) # Shape: (Total_Tokens, d_model)
        
        # 1. Scores bruts et probabilités du routeur
        router_logits = self.router(x_flat) 
        routing_weights = F.softmax(router_logits, dim=-1) # Shape: (Total_Tokens, num_experts)
        
        # 2. Top-1 Routing
        max_weights, selected_experts = torch.max(routing_weights, dim=-1)
        
        # --- [ANTI-COLLAPSE] : Calcul de la Load Balancing Loss ---
        # f : Fraction de tokens alloués à chaque expert (combien de tokens vont chez qui)
        # On calcule combien de tokens ont choisi chaque expert_id, divisé par le total
        tokens_per_expert = torch.zeros(self.num_experts, device=x.device)
        for expert_id in range(self.num_experts):
            tokens_per_expert[expert_id] = (selected_experts == expert_id).sum()
        
        fraction_tokens = tokens_per_expert / x_flat.size(0)
        
        # P : Probabilité moyenne allouée par le routeur à chaque expert sur tout le batch
        mean_routing_weights = routing_weights.mean(dim=0)
        
        # Load Balancing Loss = num_experts * somme(fraction_tokens * mean_routing_weights)
        # Idéalement, si tout est uniforme, cette valeur vaut 1.0
        aux_loss = self.num_experts * torch.sum(fraction_tokens * mean_routing_weights)
        # -----------------------------------------------------------

        out_flat = torch.zeros_like(x_flat)
        
        for expert_id in range(self.num_experts):
            token_mask = (selected_experts == expert_id)
            if token_mask.any():
                expert_inputs = x_flat[token_mask]
                expert_outputs = self.experts[expert_id](expert_inputs)
                padded_weights = max_weights[token_mask].unsqueeze(-1)
                out_flat[token_mask] = expert_outputs * padded_weights
                
        return out_flat.view(orig_shape), aux_loss # On renvoie la sortie ET la perte aux