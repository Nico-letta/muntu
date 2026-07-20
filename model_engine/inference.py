import os
import sys
import torch
from tokenizers import ByteLevelBPETokenizer
from safetensors.torch import load_file

sys.path.append(os.getcwd())
from model_engine.src.model import MuntuLM

expert_activations = []

def router_hook(module, input, output):
    """
    Espion connecté au routeur MoE.
    Capture l'expert choisi pour le TOUT DERNIER token en cours de traitement.
    """
    global expert_activations

    if isinstance(output, tuple):
        output = output[0]

    if output.dim() == 3:
        last_token_logits = output[0, -1, :]
    elif output.dim() == 2:
        last_token_logits = output[-1, :]
    else:
        last_token_logits = output.flatten()

    selected_expert = torch.argmax(last_token_logits, dim=-1).item()
    expert_activations.append(selected_expert)

def run_inference(prompt: str, max_tokens: int = 50, top_k: int = 40):
    global expert_activations
    
    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    print(f"[*] Inférence lancée sur : {device}")

    base_dir = os.path.dirname(os.path.abspath(__file__))
    root_dir = os.path.abspath(os.path.join(base_dir, ".."))
    
    tokenizer_path = os.path.join(root_dir, "data_engine", "_output", "muntu_tokenizer")

    model_path = os.path.join(base_dir, "muntu_pretrained.safetensors")

    if not os.path.exists(model_path):
        raise FileNotFoundError(f"Le fichier de poids du modèle est introuvable : {model_path}")

    tokenizer = ByteLevelBPETokenizer(
        os.path.join(tokenizer_path, "vocab.json"),
        os.path.join(tokenizer_path, "merges.txt")
    )

    vocab_size = tokenizer.get_vocab_size()

    print("[*] Chargement des poids du modèle depuis Safetensors...")
    state_dict = load_file(model_path)
    
    saved_vocab_size = state_dict['embedding.token_embedding.weight'].shape[0]

    if vocab_size != saved_vocab_size:
        print(f"[!] Warning: Taille vocabulaire Tokenizer ({vocab_size}) != Checkpoint ({saved_vocab_size}). Alignement.")
        vocab_size = saved_vocab_size

    model = MuntuLM(vocab_size=vocab_size, d_model=768, max_seq_len=4096, n_layers=4)

    random_weights = model.embedding.token_embedding.weight.clone()

    model.load_state_dict(state_dict, strict=False)
    
    assert torch.max(torch.abs(random_weights - model.embedding.token_embedding.weight)).item() > 0, \
        "CRITICAL ERROR: Les poids du modèle sont identiques à l'initialisation aléatoire ! Le checkpoint n'a pas chargé."

    model.to(device)
    model.eval()

    hook_success = False
    try:
        last_block = model.blocks[-1]
        for name, module in last_block.named_modules():
            if name.endswith('router'):
                handle = module.register_forward_hook(router_hook)
                hook_success = True
                print("[+] Télémétrie connectée au routeur MoE (Couche 4).")
                break
        if not hook_success:
            print("[!] Attention : Aucun module 'router' trouvé dans le dernier bloc de ton modèle.")
    except Exception as e:
        print(f"[!] Impossible de brancher l'espion : {e}")

    encoded = tokenizer.encode(prompt)
    input_ids = torch.tensor([encoded.ids], dtype=torch.long, device=device)

    temperatures = [0.4, 0.7, 1.0]
    print(f"\n[Prompt Initial] : '{prompt}'")
    
    for temp in temperatures:
        expert_activations = [] 
        print(f"\n" + "="*40)
        print(f" TEST À TEMPÉRATURE : {temp}")
        print("="*40)
        
        with torch.no_grad():
            generated_ids = model.generate(
                input_ids, 
                max_new_tokens=max_tokens, 
                temperature=temp, 
                top_k=top_k,
                top_p=0.9,
                repetition_penalty=1.25
            )
        
        generated_text = tokenizer.decode(generated_ids[0].tolist(), skip_special_tokens=True)
        print(f"[MUNTU] :\n{generated_text}\n")

        if hook_success and expert_activations:
            print("--- RÉPARTITION DES EXPERTS ---")
            total_tokens = len(expert_activations)
            for exp_id in range(4):
                count = expert_activations.count(exp_id)
                pct = (count / total_tokens) * 100 if total_tokens > 0 else 0
                print(f"   Expert {exp_id} : {count} tokens ({pct:.1f}%)")
        elif hook_success:
            print("[!] Aucun token n'a déclenché le hook. Vérifie la méthode forward de ton modèle.")

    if hook_success:
        handle.remove()

if __name__ == "__main__":
    run_inference(prompt="Le système de", max_tokens=50)
