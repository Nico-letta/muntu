import os
import sys
import torch
from tokenizers import ByteLevelBPETokenizer
from src.model import MuntuLM

def run_inference(prompt: str, max_tokens: int = 50, temperature: float = 0.7, top_k: int = 40):
    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    print(f"[*] Inference running on device: {device}")

    # 1. Chargement du Tokenizer customisé
    tokenizer_path = "data_engine/_output/muntu_tokenizer"
    tokenizer = ByteLevelBPETokenizer(
        os.path.join(tokenizer_path, "vocab.json"),
        os.path.join(tokenizer_path, "merges.txt")
    )
    vocab_size = tokenizer.get_vocab_size()

    # 2. Chargement des poids pour validation
    model_path = "model_engine/muntu_pretrained.pt"
    if not os.path.exists(model_path):
        raise FileNotFoundError(f"Impossible de trouver le fichier {model_path}")
    state_dict = torch.load(model_path, map_location=device)
    
    # Sécurité de production : s'adapter si les poids ont une taille différente
    saved_vocab_size = state_dict['embedding.token_embedding.weight'].shape[0]
    if vocab_size != saved_vocab_size:
        print(f"[!] Warning: Taille du tokenizer ({vocab_size}) décalée des poids ({saved_vocab_size}). Alinement forcé.")
        vocab_size = saved_vocab_size

    # 3. Initialisation du modèle
    model = MuntuLM(vocab_size=vocab_size, d_model=256, max_seq_len=512, n_layers=4)
    model.load_state_dict(state_dict)
    print(f"[+] Configuration validée et poids injectés ({vocab_size} tokens).")
        
    model.to(device)
    model.eval()

    # 4. Encodage et Génération
    encoded = tokenizer.encode(prompt)
    input_ids = torch.tensor([encoded.ids], dtype=torch.long, device=device)

    print(f"\n[Prompt] : {prompt}")
    print("[MUNTU] : ", end="")
    
    with torch.no_grad():
        generated_ids = model.generate(
            input_ids, 
            max_new_tokens=max_tokens, 
            temperature=temperature, 
            top_k=top_k
        )
    
    generated_text = tokenizer.decode(generated_ids[0].tolist(), skip_special_tokens=True)
    print(generated_text)

if __name__ == "__main__":
    run_inference(prompt="Notre collectif accompagne", max_tokens=40, temperature=0.7, top_k=40)