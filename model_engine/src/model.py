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