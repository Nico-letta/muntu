import torch
import torch.nn as nn
from src.embedding import MuntuEmbedding
from src.transformer_block import MuntuTransformerBlock
import torch.nn.functional as F

class MuntuLM(nn.Module):
    def __init__(self, vocab_size: int, d_model: int = 256, max_seq_len: int = 512, n_layers: int = 4):
        """
        vocab_size : Taille du dictionnaire de tokens 
        d_model    : Dimension des vecteurs d'embedding
        max_seq_len: Taille maximale du contexte
        n_layers   : Nombre de blocs Transformers empilés (ici 4)
        """
        super().__init__()
        
        self.max_seq_len = max_seq_len
        
        self.embedding = MuntuEmbedding(vocab_size, d_model, max_seq_len)
        
        self.blocks = nn.ModuleList([MuntuTransformerBlock(d_model) for _ in range(n_layers)])
        
        self.ln_f = nn.LayerNorm(d_model)
        
        self.lm_head = nn.Linear(d_model, vocab_size, bias=False)

        self.lm_head.weight = self.embedding.token_embedding.weight

        self.apply(self._init_weights)
        print("[+] Poids du modèle initialisés selon le standard GPT-2 (std=0.02).")

    def _init_weights(self, module):
        """ Initialisation personnalisée pour stabiliser les gradients au départ """
        if isinstance(module, nn.Linear):
            torch.nn.init.normal_(module.weight, mean=0.0, std=0.02)
            if module.bias is not None:
                torch.nn.init.zeros_(module.bias)
        elif isinstance(module, nn.Embedding):
            torch.nn.init.normal_(module.weight, mean=0.0, std=0.02)

    def forward(self, idx, targets=None):
        B, T = idx.shape
        
        x = self.embedding(idx)
        
        total_aux_loss = 0
        for block in self.blocks:
            x, block_aux_loss = block(x)
            total_aux_loss += block_aux_loss
            
        x = self.ln_f(x)
        logits = self.lm_head(x)
        
        loss = None
        if targets is not None:
            B, T, C = logits.shape
            logits_flat = logits.view(B*T, C)
            targets_flat = targets.view(B*T)

            main_loss = F.cross_entropy(logits_flat, targets_flat)

            loss = main_loss + 0.01 * (total_aux_loss / len(self.blocks))
            
        return logits, loss
    
    @torch.no_grad()
    def generate(self, input_ids: torch.Tensor, max_new_tokens: int, temperature: float = 1.0, top_k: int = None, top_p: float = None):
        """
        Génère une suite de tokens de manière autorégressive avec Temperature, Top-K et Top-P sampling.
        """
        self.eval() 
        
        for _ in range(max_new_tokens):
            input_cond = input_ids[:, -self.max_seq_len:]

            logits, _ = self(input_cond)
            next_token_logits = logits[:, -1, :]
            
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