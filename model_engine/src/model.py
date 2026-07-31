import torch
import torch.nn as nn
from src.embedding import MuntuEmbedding
from src.transformer_block import MuntuTransformerBlock
import torch.nn.functional as F

class MuntuLM(nn.Module):
    def __init__(self, vocab_size: int, d_model: int = 768, max_seq_len: int = 4096, n_layers: int = 4):
        super().__init__()
        
        self.max_seq_len = max_seq_len
        self.embedding = MuntuEmbedding(vocab_size, d_model, max_seq_len)
        self.blocks = nn.ModuleList([MuntuTransformerBlock(d_model) for _ in range(n_layers)])
        self.ln_f = nn.LayerNorm(d_model)
        self.lm_head = nn.Linear(d_model, vocab_size, bias=False)

        # Weight tying
        self.lm_head.weight = self.embedding.token_embedding.weight

        self.apply(self._init_weights)
        print(f"[+] Poids du modèle initialisés (d_model={d_model}, max_seq_len={max_seq_len}).")

    def _init_weights(self, module):
        if isinstance(module, nn.Linear):
            torch.nn.init.normal_(module.weight, mean=0.0, std=0.02)
            if module.bias is not None:
                torch.nn.init.zeros_(module.bias)
        elif isinstance(module, nn.Embedding):
            torch.nn.init.normal_(module.weight, mean=0.0, std=0.02)

    def forward(self, idx, targets=None):
        B, T = idx.shape
        x = self.embedding(idx)
        
        total_aux_loss = 0.0
        for block in self.blocks:
            x, block_aux_loss = block(x)
            total_aux_loss += block_aux_loss
            
        x = self.ln_f(x)
        logits = self.lm_head(x)
        
        if targets is not None:
            B, T, C = logits.shape
            logits_flat = logits.view(B*T, C)
            targets_flat = targets.view(B*T)

            main_loss = F.cross_entropy(logits_flat, targets_flat)
            
            return logits, main_loss, total_aux_loss
            
        return logits, None
    
    @torch.no_grad()
    @torch.no_grad()
    def generate(self, input_ids: torch.Tensor, max_new_tokens: int, temperature: float = 1.0, 
                 top_k: int = None, top_p: float = None, repetition_penalty: float = 1.2):
        """
        Génère une suite de tokens avec Temperature, Top-K, Top-P et Repetition Penalty.
        """
        self.eval() 
        
        for _ in range(max_new_tokens):
            input_cond = input_ids[:, -self.max_seq_len:]

            logits, _ = self(input_cond)
            next_token_logits = logits[:, -1, :]
            
            # Pénalité de répétition
            if repetition_penalty != 1.0:
                for i in range(input_ids.shape[0]): 
                    already_generated = set(input_ids[i].tolist())
                    for token_id in already_generated:
                        if next_token_logits[i, token_id] > 0:
                            next_token_logits[i, token_id] /= repetition_penalty
                        else:
                            next_token_logits[i, token_id] *= repetition_penalty

            # 1. Température
            if temperature != 1.0:
                next_token_logits = next_token_logits / temperature
                
            # 2. Top-K
            if top_k is not None and top_k > 0:
                v, _ = torch.topk(next_token_logits, min(top_k, next_token_logits.size(-1)))
                next_token_logits[next_token_logits < v[:, [-1]]] = -float('Inf')
            
            # 3. Top-P (Nucleus Sampling)
            if top_p is not None and top_p > 0.0 and top_p < 1.0:
                sorted_logits, sorted_indices = torch.sort(next_token_logits, descending=True, dim=-1)
                cumulative_probs = torch.cumsum(F.softmax(sorted_logits, dim=-1), dim=-1)
                
                sorted_indices_to_remove = cumulative_probs > top_p
                sorted_indices_to_remove[..., 1:] = sorted_indices_to_remove[..., :-1].clone()
                sorted_indices_to_remove[..., 0] = 0
                
                indices_to_remove = sorted_indices_to_remove.scatter(1, sorted_indices, sorted_indices_to_remove)
                next_token_logits[indices_to_remove] = -float('Inf')

            probs = F.softmax(next_token_logits, dim=-1)
            next_token = torch.multinomial(probs, num_samples=1)
            
            input_ids = torch.cat((input_ids, next_token), dim=1)
            
        return input_ids