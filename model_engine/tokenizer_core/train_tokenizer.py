import os
from tokenizers import ByteLevelBPETokenizer

def build_muntu_tokenizer():
    root_dir = "/content/drive/MyDrive/muntu_project"

    corpus_path = os.path.join(root_dir, "data_engine", "_output", "corpus_pretrain.txt")
    output_dir = os.path.join(root_dir, "data_engine", "_output", "muntu_tokenizer")
    
    os.makedirs(output_dir, exist_ok=True)
    
    if not os.path.exists(corpus_path):
        raise FileNotFoundError(f"[-] Impossible de trouver le corpus à cet endroit : {corpus_path}")
        
    print(f"[*] Entraînement du ByteLevelBPETokenizer sur : {corpus_path}")
    
    tokenizer = ByteLevelBPETokenizer()

    tokenizer.train(
        files=[corpus_path],
        vocab_size=8000,
        min_frequency=2,
        special_tokens=["<s>", "<pad>", "</s>", "<unk>", "<mask>"]
    )
    
    tokenizer.save_model(output_dir)
    print(f" Tokenizer entraîné avec succès ! Vocabulaire de {tokenizer.get_vocab_size()} tokens sauvegardé dans : {output_dir}")

if __name__ == "__main__":
    build_muntu_tokenizer()