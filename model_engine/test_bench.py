import os
import torch
from tokenizers import ByteLevelBPETokenizer

# Importations de tes modules de src
from src.embedding import MuntuEmbedding
from src.transformer_block import MuntuTransformerBlock

def run_test_bench():
    # --- STAGE 1 : INIT ---
    base_dir = os.path.dirname(os.path.abspath(__file__))
    root_dir = os.path.abspath(os.path.join(base_dir, ".."))
    tokenizer_dir = os.path.join(root_dir, "data_engine", "_output", "muntu_tokenizer")
    
    tokenizer = ByteLevelBPETokenizer(
        os.path.join(tokenizer_dir, "vocab.json"),
        os.path.join(tokenizer_dir, "merges.txt")
    )

    sample_text = "const MuntuApp = () => { return <div className='p-4'>Performance first</div> }"
    
    # --- STAGE 2 : TOKENISATION ---
    print("\n=== STAGE 1 : TOKENISATION ===")
    encoded = tokenizer.encode(sample_text)
    input_tensor = torch.tensor([encoded.ids], dtype=torch.long)
    print(f"Shape entrée : {input_tensor.shape}")

    # --- STAGE 3 : EMBEDDING ---
    print("\n=== STAGE 2 : EMBEDDING ===")
    d_model = 256
    embedding_layer = MuntuEmbedding(vocab_size=1500, d_model=d_model, max_seq_len=512)
    
    with torch.no_grad():
        embeddings = embedding_layer(input_tensor)
    print(f"Shape après Embedding : {embeddings.shape}")

    # --- STAGE 4 : TRANSFORMER BLOCK ---
    print("\n=== STAGE 3 : BLOC TRANSFORMER ENTIER ===")
    transformer_block = MuntuTransformerBlock(d_model=d_model)
    
    with torch.no_grad():
        block_output = transformer_block(embeddings)
    print(f"Shape après Transformer Block : {block_output.shape}")
    
    if block_output.shape == embeddings.shape:
        print(" Succès critique : Le bloc Transformer complet a traité les données avec succès.")
        print("Toutes les connexions résiduelles et normalisations fonctionnent sans erreur de dimension.")
    else:
        print(" Erreur : Problème de dimensions dans le bloc Transformer.")

if __name__ == "__main__":
    run_test_bench()