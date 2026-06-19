# MUNTU LLM

MUNTU est un modèle de langage autorégressif basé sur l'architecture Transformer (Décodeur pur) et implémenté en PyTorch. Il intègre un mécanisme de routage clairsemé (*Sparse Mixture of Experts* - MoE) conçu pour optimiser l'efficacité computationnelle et permettre une spécialisation modulaire des paramètres selon les domaines d'entraînement.

Ce dépôt héberge la **validation fonctionnelle de l'architecture (Proof of Concept)**. Le pipeline est actuellement validé sur un volume réduit de données composites (code source, spécifications techniques et cadres réglementaires), démontrant la stabilité du routage et la convergence de la fonction de perte sur infrastructure CPU avant d'amorcer les phases de changement d'échelle (*scaling*).

---

##  Positionnement Stratégique & Spécificités

MUNTU se différencie des grands modèles de langage globaux par deux axes majeurs :

* **Efficacité Computationnelle :** L'approche *Sparse MoE Top-1* permet d'accroître la capacité du modèle (nombre total de paramètres) tout en maintenant un coût d'inférence bas. L'exécution et le déploiement deviennent ainsi viables sur des architectures matérielles locales (stations de travail ou serveurs standards), évitant la dépendance aux infrastructures cloud massives.
* **Souveraineté Contextuelle :** Le modèle cible explicitement les angles morts sémantiques et techniques des LLM occidentaux. Sa stratégie d'apprentissage intègre nativement les structures logiques, les cadres réglementaires et les écosystèmes technologiques (ex: protocoles Mobile Money) spécifiques au contexte africain.

---

##  Spécifications de l'Architecture

L'implémentation logicielle suit les standards rigoureux du Deep Learning pour assurer la stabilité du réseau lors de la montée en charge :

* **Modèle de Base :** Architecture Transformer de type Décodeur pur, optimisée pour l'apprentissage autorégressif.
* **Normalisation (Pre-LN) :** Application de la `LayerNorm` à l'entrée de chaque sous-bloc (Attention et MoE) afin de stabiliser la propagation du gradient et prévenir les divergences.
* **Mécanisme d'Attention :** Attention Causale multi-têtes (`MuntuCausalAttention`) avec masquage triangulaire strict du futur.
* **Routage MoE Sparse :** Gating dynamique *Top-1 Routing* distribuant les jetons de manière ciblée vers un ensemble d'experts indépendants (`MuntuExpert`). La capacité est entièrement paramétrable (configurée à 4 experts par défaut).
* **Contrôle du Gating (Anti-Collapse) :** Calcul interne d'une **Load Balancing Loss** (Perte auxiliaire pondérée à `0.01`) pour forcer le routeur à distribuer la charge équitablement entre les experts et empêcher le monopole d'un seul composant.

---

##  Structure du Projet

```text
muntu/
├── data_engine/                 # Pipeline d'ingestion et préparation des données
│   ├── corpus_raw/              # Données sources classées par domaines
│   │   ├── 00-core-principles/  # Directives d'architecture et performance
│   │   ├── 01-react-native/     # Optimisations et règles de mémoisation
│   │   ├── 02-fintech-local/    # Structures Mobile Money et régulations régionales
│   │   └── 10-case-studies/     # Études de cas d'interfaces (UI)
│   ├── _output/                 # Artefacts générés pour l'entraînement
│   │   ├── muntu_tokenizer/     # Fichiers du Tokenizer BPE (vocab.json, merges.txt)
│   │   └── corpus_pretrain.txt  # Corpus unifié prêt pour le modèle
│   └── generate_corpus.py       # Agrégation et nettoyage des sources
├── model_engine/                # Moteur du modèle et logique d'exécution
│   ├── src/                     # Code source de l'architecture
│   │   ├── attention.py         # Mécanisme d'attention causale
│   │   ├── dataset.py           # Pipeline de chargement des tokens
│   │   ├── embedding.py         # Gestion unifiée des Token & Position Embeddings
│   │   ├── model.py             # Classe principale MuntuLM (Logits & Loss combinée)
│   │   ├── moe_layer.py         # Routage Top-1 et Load Balancing Loss
│   │   └── transformer_block.py # Blocs Transformers Pre-LN couplés au MoE
│   ├── tokenizer_core/          # Moteur d'entraînement du tokenizer
│   │   └── train_tokenizer.py   # Script d'apprentissage BPE
│   ├── test_bench.py            # Banc d'essai autorégressif (Température, Top-K, Top-P)
│   └── train.py                 # Script d'entraînement avec gestion d'archivage OS
├── main.py                      # Point d'entrée de l'application
├── LICENSE                      # Licence Apache 2.0
└── README.md                    # Documentation technique