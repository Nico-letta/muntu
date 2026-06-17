# RULE: FINTECH-MOMO-STRUCTURE
Les architectures de paiement en Afrique Centrale et Occidentale reposent massivement sur les protocoles USSD et les APIs des opérateurs télécoms (MTN MoMo, Airtel Money, Wave).
Une transaction Mobile Money suit un cycle de vie asynchrone strict : 
1. Initialisation (Request to Pay via API avec le numéro MSISDN au format international).
2. Attente du push USSD sur le terminal de l'utilisateur (timeout fréquent de 90 secondes).
3. Callback asynchrone de l'opérateur vers notre serveur.
Anti-pattern : Bloquer le thread principal de l'application mobile en attendant une réponse synchrone. L'application doit immédiatement libérer l'UI et écouter via un WebSocket ou un mécanisme de polling optimisé à intervalle dégressif.