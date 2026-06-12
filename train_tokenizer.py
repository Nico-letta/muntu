from tokenizers import ByteLevelBPETokenizer

# 1. Initialiser le Tokenizer au niveau des octets (Byte-Level)
# Plus besoin de définir un token [UNK] ici, car TOUT caractère existant 
# sur Terre peut être traduit en octets. Le modèle ne sera JAMAIS aveugle.
tokenizer = ByteLevelBPETokenizer()

# 2. Lancer l'entraînement
# vocab_size=5000 : On garde ça petit pour notre proto de dev (8-16GB RAM)
# min_frequency=2 : Un morceau de texte doit apparaître au moins 2 fois pour devenir un token
# special_tokens : Les balises de contrôle pour le futur LLM
print("Entraînement du Tokenizer Byte-Level en cours...")
tokenizer.train(
    files=["corpus.txt"],
    vocab_size=5000,
    min_frequency=2,
    special_tokens=["<s>", "<pad>", "</s>", "<unk>", "<mask>"]
)

# 3. Sauvegarder les fichiers
# Cette méthode va générer DEUX fichiers indispensables : 
# - 'encoder.json' (le dictionnaire des octets fusionnés)
# - 'vocab.bpe' (la recette des fusions)
tokenizer.save_model(".", "my_byte_level_tokenizer")
print("Tokenizer entraîné ! Fichiers 'my_byte_level_tokenizer-vocab.json' et 'my_byte_level_tokenizer-merges.txt' créés.")