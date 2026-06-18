import os
import torch
import torch.nn.functional as F
from tokenizers import ByteLevelBPETokenizer
from src.model import MuntuLM

def generate_text(prompt: str, max_new_tokens: int = 40):
    base_dir = os.path.dirname(os.path.abspath(__file__))
    root_dir = os.path.abspath(os.path.join(base_dir, ".."))
    
    tokenizer_dir = os.path.join(root_dir, "data_engine", "_output", "muntu_tokenizer")
    model_path = os.path.join(base_dir, "muntu_pretrained.pt")
    
    # 1. Charger le Tokeniseur
    tokenizer = ByteLevelBPETokenizer(
        os.path.join(tokenizer_dir, "vocab.json"),
        os.path.join(tokenizer_dir, "merges.txt")
    )
    
    # 2. Instancier et charger les poids entraînés de MUNTU
    model = MuntuLM(vocab_size=1495, d_model=256, max_seq_len=512, n_layers=4)
    model.load_state_dict(torch.load(model_path, map_location=torch.device('cpu')))
    model.eval() 
    
    # 3. Encodage du prompt d'entrée
    encoded = tokenizer.encode(prompt)
    input_ids = torch.tensor([encoded.ids], dtype=torch.long)
    
    print(f"\n[Prompt initial] : {prompt}")
    print("[MUNTU génère...] : ", end="")
    
    # Boucle de génération autoregressive
    for _ in range(max_new_tokens):
        input_cond = input_ids[:, -512:]
        
        with torch.no_grad():
            logits, _ = model(input_cond)
        
        next_token_logits = logits[:, -1, :]
        next_token = torch.argmax(next_token_logits, dim=-1, keepdim=True)
        input_ids = torch.cat((input_ids, next_token), dim=1)
        
        # Décodage propre pour éviter les caractères de contrôle BPE (Ġ, Ċ) dans le terminal
        token_str = tokenizer.decode([next_token.item()])
        print(token_str, end="", flush=True)
    print("\n")

if __name__ == "__main__":
    # Test avec une amorce de code TypeScript propre à ton corpus
    generate_text("const MuntuApp = () => {", max_new_tokens=40)