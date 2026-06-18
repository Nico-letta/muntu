import torch
import torch.nn as nn
from src.embedding import MuntuEmbedding
from src.transformer_block import MuntuTransformerBlock

class MuntuLM(nn.Module):
    def __init__(self, vocab_size: int, d_model: int = 256, max_seq_len: int = 512, n_layers: int = 4):
        """
        vocab_size : Taille du dictionnaire de tokens (1495)
        d_model    : Dimension des vecteurs d'embedding (256)
        max_seq_len: Taille maximale du contexte (512)
        n_layers   : Nombre de blocs Transformers empilés (ici 4 pour un modèle compact)
        """
        super().__init__()
        
        # 1. Couche d'entrée : Embedding
        self.embedding = MuntuEmbedding(vocab_size, d_model, max_seq_len)
        
        # 2. Le cœur du modèle : Empilement séquentiel de N blocs Transformers
        self.blocks = nn.ModuleList([MuntuTransformerBlock(d_model) for _ in range(n_layers)])
        
        # 3. Normalisation finale de stabilisation
        self.ln_f = nn.LayerNorm(d_model)
        
        # 4. Tête de prédiction du langage (Language Modeling Head)
        # Projette d_model (256) -> vocab_size (1495)
        self.lm_head = nn.Linear(d_model, vocab_size, bias=False)
        
        # Optionnel mais pro : Partage des poids (Weight Tying)
        # On lie les poids de la couche d'embedding et de la tête de sortie. 
        # Ça réduit drastiquement le nombre de paramètres et améliore les performances sur les petits corpus.
        self.lm_head.weight = self.embedding.token_embedding.weight

        # ======= INITIALISATION DES POIDS =======
        self.apply(self._init_weights)
        print("[+] Poids du modèle initialisés selon le standard GPT-2 (std=0.02).")

    def _init_weights(self, module):
        """ Initialisation personnalisée pour stabiliser les gradients au départ """
        if isinstance(module, nn.Linear):
            # On force des poids très petits et proches de 0
            torch.nn.init.normal_(module.weight, mean=0.0, std=0.02)
            if module.bias is not None:
                torch.nn.init.zeros_(module.bias)
        elif isinstance(module, nn.Embedding):
            torch.nn.init.normal_(module.weight, mean=0.0, std=0.02)

    def forward(self, input_ids: torch.Tensor, targets: torch.Tensor = None):
        """
        input_ids: Tenseur de tokens d'entrée (Batch_size, Seq_len)
        targets: Tenseur de tokens cibles pour le calcul de la loss (Batch_size, Seq_len)
        """
        # Flux à travers les couches
        x = self.embedding(input_ids) # (B, T, d_model)
        
        for block in self.blocks:
            x = block(x)              # (B, T, d_model)
            
        x = self.ln_f(x)              # (B, T, d_model)
        
        # Calcul des logits (les scores bruts non-normalisés pour chaque mot du vocabulaire)
        logits = self.lm_head(x)      # (B, T, vocab_size)
        
        # Calcul optionnel de la Loss (Entropie croisée) si on est en phase d'entraînement
        loss = None
        if targets is not None:
            # PyTorch CrossEntropy expects (Batch * Seq_len, Vocab_size)
            loss = nn.functional.cross_entropy(
                logits.view(-1, logits.size(-1)), 
                targets.view(-1),
                ignore_index=-1 # Évite de calculer la perte sur le padding si nécessaire
            )
            
        return logits, loss
    
    @torch.no_grad()
    def generate(self, input_ids: torch.Tensor, max_new_tokens: int, temperature: float = 1.0, top_k: int = None, top_p: float = None):
        """
        Génère une suite de tokens de manière autorégressive avec Temperature, Top-K et Top-P sampling.
        """
        self.eval() 
        
        for _ in range(max_new_tokens):
            input_cond = input_ids[:, -512:]
            logits, _ = self(input_cond)
            next_token_logits = logits[:, -1, :]
            
            # 1. Application de la Température
            if temperature != 1.0:
                next_token_logits = next_token_logits / temperature
                
            # 2. Application du Top-K
            if top_k is not None and top_k > 0:
                v, _ = torch.topk(next_token_logits, min(top_k, next_token_logits.size(-1)))
                next_token_logits[next_token_logits < v[:, [-1]]] = -float('Inf')
            
            # 3. Application du Top-P (Nucleus Sampling)
            if top_p is not None and top_p > 0.0 and top_p < 1.0:
                # On trie les logits par ordre décroissant
                sorted_logits, sorted_indices = torch.sort(next_token_logits, descending=True, dim=-1)
                # Calcul des probabilités cumulées
                cumulative_probs = torch.cumsum(nn.functional.softmax(sorted_logits, dim=-1), dim=-1)
                
                # Masquer les tokens qui dépassent le seuil top_p
                sorted_indices_to_remove = cumulative_probs > top_p
                # On décale vers la droite pour conserver au moins le premier token au-dessus du seuil
                sorted_indices_to_remove[..., 1:] = sorted_indices_to_remove[..., :-1].clone()
                sorted_indices_to_remove[..., 0] = 0
                
                # Remplacer les logits exclus par -inf
                indices_to_remove = sorted_indices_to_remove.scatter(1, sorted_indices, sorted_indices_to_remove)
                next_token_logits[indices_to_remove] = -float('Inf')
            
            # 4. Conversion en probabilités et échantillonnage
            probs = nn.functional.softmax(next_token_logits, dim=-1)
            next_token = torch.multinomial(probs, num_samples=1)
            
            input_ids = torch.cat((input_ids, next_token), dim=1)
            
        return input_ids