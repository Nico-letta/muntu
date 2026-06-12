from tokenizers import ByteLevelBPETokenizer

# Charger les deux fichiers générés
tokenizer = ByteLevelBPETokenizer(
    "my_byte_level_tokenizer-vocab.json",
    "my_byte_level_tokenizer-merges.txt"
)

# On pousse le modèle à bout avec des caractères spéciaux, du code et de la fintech
phrase_test = "const échec = await MoMo.pay(👉 *126# );"
output = tokenizer.encode(phrase_test)

print("Texte :", phrase_test)
print("Tokens :", output.tokens)
print("IDs :", output.ids)