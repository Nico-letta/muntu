import os
import sys
import torch
import torch.nn.functional as F
from tokenizers import ByteLevelBPETokenizer
from src.model import MuntuLM

expert_activations = []

def router_hook(module, input, output):
    """
    Ce hook intercepte la sortie directe de tself.router.
    L'output (router_logits) a une forme : (Total_Tokens, num_experts)
    """
    global expert_activations
    router_logits = output
    

    last_token_logits = router_logits[-1, :]
    selected_expert = torch.argmax(last_token_logits, dim=-1).item()
    
    expert_activations.append(selected_expert)

def run_inference(prompt: str, max_tokens: int = 50, temperature: float = 0.7, top_k: int = 40):
    global expert_activations
    expert_activations = []
    
    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    print(f"[*] Inference running on device: {device}")

    tokenizer_path = "data_engine/_output/muntu_tokenizer"
    tokenizer = ByteLevelBPETokenizer(
        os.path.join(tokenizer_path, "vocab.json"),
        os.path.join(tokenizer_path, "merges.txt")
    )
    vocab_size = tokenizer.get_vocab_size()

    model_path = "model_engine/muntu_pretrained.pt"
    if not os.path.exists(model_path):
        raise FileNotFoundError(f"Impossible de trouver le fichier {model_path}")
    state_dict = torch.load(model_path, map_location=device)
    
    saved_vocab_size = state_dict['embedding.token_embedding.weight'].shape[0]
    if vocab_size != saved_vocab_size:
        print(f"[!] Warning: Taille du tokenizer ({vocab_size}) décalée des poids ({saved_vocab_size}). Alinement forcé.")
        vocab_size = saved_vocab_size

    model = MuntuLM(vocab_size=vocab_size, d_model=256, max_seq_len=512, n_layers=4)
    model.load_state_dict(state_dict)
    print(f"[+] Configuration validée et poids injectés ({vocab_size} tokens).")
        
    model.to(device)
    model.eval()

    hook_success = False
    try:
        last_block = model.blocks[-1]
        router_module = None
        
        for name, module in last_block.named_modules():
            if name.endswith('router'):
                router_module = module
                break
                
        if router_module is not None:
            handle = router_module.register_forward_hook(router_hook)
            hook_success = True
            print("[+] Espion connecté avec succès sur le routeur MoE de la dernière couche !")
        else:
            print("[!] Routeur introuvable dans les modules du bloc.")
    except Exception as e:
        print(f"[!] Impossible de brancher l'espion : {e}")

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

    if hook_success:
        handle.remove() 
        if expert_activations:
            print(" --- REPARTITION DES EXPERTS (Dernière Couche) ---")
            total_tokens = len(expert_activations)
            for exp_id in range(4):
                count = expert_activations.count(exp_id)
                percentage = (count / total_tokens) * 100 if total_tokens > 0 else 0
                print(f"  Expert {exp_id} : {count} tokens ({percentage:.1f}%)")

if __name__ == "__main__":
    run_inference(prompt="Notre collectif accompagne", max_tokens=40, temperature=0.7, top_k=40)