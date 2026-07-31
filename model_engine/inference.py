import os
import sys
import torch
from safetensors.torch import load_file
from tokenizers import Tokenizer

sys.path.append(os.getcwd())
from model_engine.src.model import MuntuLM

def test_fintech_inference():
    base_dir = os.path.dirname(os.path.abspath(__file__)) if '__file__' in globals() else os.getcwd()
    root_dir = os.path.abspath(os.path.join(base_dir, ".."))

    # Chemins absolus nettoyés
    model_path = os.path.join(base_dir, "muntu_fintech.safetensors")
    tokenizer_path = os.path.join(root_dir, "data_engine", "_output", "muntu_tokenizer", "tokenizer.json")

    if not os.path.exists(model_path):
        raise FileNotFoundError(f"[!] Fichier de poids introuvable : {model_path}")
    if not os.path.exists(tokenizer_path):
        raise FileNotFoundError(f"[!] Tokenizer introuvable : {tokenizer_path}")

    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    print(f"[*] Appareil d'inférence : {device}")
    print(f"[*] Chargement du tokenizer depuis : {tokenizer_path}")
    tokenizer = Tokenizer.from_file(tokenizer_path)

    print(f"[*] Chargement des poids Fintech depuis : {model_path}")
    model = MuntuLM(
        vocab_size=tokenizer.get_vocab_size(),
        d_model=768,
        max_seq_len=4096,
        n_layers=4
    )
    weights = load_file(model_path)
    model.load_state_dict(weights)
    model.to(device)
    model.eval()

    # Question orientée Fintech avec structure ChatML
    user_query = "Explique le fonctionnement d'une transaction de paiement mobile."
    formatted_prompt = f"<|im_start|>user\n{user_query}<|im_end|>\n<|im_start|>assistant\n"
    
    input_ids = torch.tensor([tokenizer.encode(formatted_prompt).ids], dtype=torch.long).to(device)

    print("\n" + "="*50)
    print(f"[PROMPT SFT] : {user_query}")
    print("="*50 + "\n")

    with torch.no_grad():
        for _ in range(150):
            logits = model(input_ids)
            if isinstance(logits, tuple):
                logits = logits[0]
            
            # Application de la température
            next_token_logits = logits[:, -1, :] / 0.7
            probs = torch.softmax(next_token_logits, dim=-1)
            next_token = torch.multinomial(probs, num_samples=1)

            input_ids = torch.cat([input_ids, next_token], dim=-1)

            # Condition d'arrêt sur balise ChatML
            decoded_word = tokenizer.decode([next_token.item()])
            if "<|im_end|>" in decoded_word:
                break

    output_text = tokenizer.decode(input_ids[0].tolist())
    print("[MUNTU FINTECH] :")
    response = output_text.split("<|im_start|>assistant\n")[-1].replace("<|im_end|>", "").strip()
    print(response)

if __name__ == "__main__":
    test_fintech_inference()