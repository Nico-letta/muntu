# Configurations projet — MUNTU Data Engine

Le moteur `expand_corpus_sources.py` est **aveugle** : il lit uniquement un fichier JSON de configuration.

## Demarrage rapide (AfriWallet)

```bash
# 1. Copier le template et ajuster les chemins locaux
cp data_engine/configs/afriwallet.example.json data_engine/configs/afriwallet.json

# 2. Editer source_path et corpus_staging dans afriwallet.json

# 3. Extraire + compiler
python data_engine/expand_corpus_sources.py --config data_engine/configs/afriwallet.json
python data_engine/generate_corpus.py
```

Sans argument `--config`, le script cherche `configs/afriwallet.json`, puis `afriwallet.example.json`.

## AI-MESSAGE-PIPELINE

```bash
python data_engine/expand_corpus_sources.py --config data_engine/configs/ai-message-pipeline.json
python data_engine/generate_corpus.py
```

Template versionne : `ai-message-pipeline.example.json` — copier vers `ai-message-pipeline.json` et ajuster `source_path`.

## Securite Git

Les fichiers `*.json` locaux avec chemins prives sont **gitignores** :

- `data_engine/configs/afriwallet.json`
- `data_engine/configs/ai-message-pipeline.json`
- `data_engine/configs/*.local.json`

Seuls les templates `*.example.json` et ce README sont versionnes.

## Nouveau projet

1. Copier `afriwallet.example.json` -> `mon_projet.json`
2. Modifier : `project_id`, `project_name`, `source_path`, `features`
3. Lancer : `python expand_corpus_sources.py --config configs/mon_projet.json`

## Structure config

| Cle | Role |
|-----|------|
| `project_name` | Application cible (ex. AfriWallet) — niveau metier |
| `engine_name` | Moteur IA (MUNTU) — niveau meta |
| `codebase_ref` | Reference portable dans le corpus (`afriwallet_codebase`) |
| `source_path` | Racine du repo code a extraire |
| `corpus_staging` | JSONL training, legacy knowledge |
| `corpus_output` | Dossier `corpus_raw` de destination |
| `branding` | Aliases de chemins + remplacements texte a l'export |
| `features.*` | Extracteurs actives (voir afriwallet.example.json) |

## Architecture

```
expand_corpus_sources.py     # CLI
corpus_extractor/
  config.py                    # Chargement JSON
  engine.py                    # Extracteurs generiques
  plugins/fintech.py           # Runbooks MTN/Airtel, corpus synthetique
configs/
  afriwallet.example.json      # Template versionne
  afriwallet.json              # Local (gitignore)
```
