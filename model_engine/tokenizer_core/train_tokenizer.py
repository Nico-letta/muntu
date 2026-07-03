import os
from tokenizers import ByteLevelBPETokenizer

def train_muntu_tokenizer():
    current_dir = os.path.dirname(os.path.abspath(__file__))

    root_dir = os.path.abspath(os.path.join(current_dir, "..", ".."))
    print(root_dir)
    corpus_path = os.path.join(root_dir, "data_engine", "_output", "corpus_pretrain.txt")
    output_dir = os.path.join(root_dir, "data_engine", "_output", "muntu_tokenizer")
    
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)
        
    print("[*] Initialisation du ByteLevelBPETokenizer...")
    
    tokenizer = ByteLevelBPETokenizer()
    
    print(f"[*] Entraînement en cours sur : {corpus_path}")
    tokenizer.train(
        files=[corpus_path],
        vocab_size=1495,
        min_frequency=2,
        special_tokens=["<s>", "</s>", "<pad>", "<unk>"]
    )
    
    tokenizer.save_model(output_dir)
    print(f"[+] Configuration sauvegardée dans : {output_dir}")

if __name__ == "__main__":
    train_muntu_tokenizer()