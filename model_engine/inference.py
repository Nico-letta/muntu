import os
import torch
from tokenizers import ByteLevelBPETokenizer
from src.model import MuntuLM

expert_activations = []

def router_hook(module, input, output):
    global expert_activations
    last_token_logits = output[-1, :]
    selected_expert = torch.argmax(last_token_logits, dim=-1).item()
    expert_activations.append(selected_expert)

def run_inference(prompt: str, max_tokens: int = 50, top_k: int = 40):
    global expert_activations
    
    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    print(f"[*] Inférence lancée sur : {device}")

    tokenizer_path = "data_engine/_output/muntu_tokenizer" 
    model_path = "model_engine/muntu_pretrained.pt"

    tokenizer = ByteLevelBPETokenizer(
        os.path.join(tokenizer_path, "vocab.json"),
        os.path.join(tokenizer_dir := tokenizer_path, "merges.txt")
    )
    vocab_size = tokenizer.get_vocab_size()

    state_dict = torch.load(model_path, map_location=device)
    
    saved_vocab_size = state_dict['embedding.token_embedding.weight'].shape[0]
    if vocab_size != saved_vocab_size:
        vocab_size = saved_vocab_size

    model = MuntuLM(vocab_size=vocab_size, d_model=256, max_seq_len=4096, n_layers=4)
    model.max_seq_len = 4096
    model.load_state_dict(state_dict)
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
                top_p=0.9
            )
        
        generated_text = tokenizer.decode(generated_ids[0].tolist(), skip_special_tokens=True)
        print(f"[MUNTU] :\n{generated_text}\n")

        if hook_success and expert_activations:
            print("--- RÉPARTITION DES EXPERTS ---")
            total_tokens = len(expert_activations)
            for exp_id in range(4):
                count = expert_activations.count(exp_id)
                pct = (count / total_tokens) * 100 if total_tokens > 0 else 0
                print(f"  Expert {exp_id} : {count} tokens ({pct:.1f}%)")

    if hook_success:
        handle.remove()

if __name__ == "__main__":
    run_inference(prompt="Le système de", max_tokens=50)