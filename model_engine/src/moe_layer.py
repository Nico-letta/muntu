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
    def __init__(self, d_model: int, num_experts: int = 4, k: int = 2):
        super().__init__()
        self.num_experts = num_experts
        self.k = k 
        self.experts = nn.ModuleList([MuntuExpert(d_model) for _ in range(num_experts)])
        self.router = nn.Linear(d_model, num_experts, bias=False)

    def forward(self, x: torch.Tensor):
        orig_shape = x.shape
        B, T, C = orig_shape
        x_flat = x.view(-1, C)
        
  
        router_logits = self.router(x_flat).float() 
        routing_weights = F.softmax(router_logits, dim=-1) 
        
        topk_weights, topk_indices = torch.topk(routing_weights, self.k, dim=-1)
        
 
        denom = topk_weights.sum(dim=-1, keepdim=True)
        topk_weights = topk_weights / (denom + 1e-20)
        
        mean_routing_weights = routing_weights.mean(dim=0)

        expert_mask = torch.zeros_like(router_logits).scatter_(1, topk_indices, 1.0)
        fraction_tokens = expert_mask.mean(dim=0)

        aux_loss = self.num_experts * torch.sum(fraction_tokens * mean_routing_weights)

        topk_weights = topk_weights.to(x.dtype)
        out_flat = torch.zeros_like(x_flat)
        
        for expert_id in range(self.num_experts):
            token_indices, expert_pos = torch.where(topk_indices == expert_id)
            
            if len(token_indices) > 0:
                expert_inputs = x_flat[token_indices]
                expert_outputs = self.experts[expert_id](expert_inputs)

                gating_weight = topk_weights[token_indices, expert_pos].unsqueeze(-1)
                out_flat[token_indices] += expert_outputs * gating_weight

        return out_flat.view(orig_shape), aux_loss.to(x.dtype)