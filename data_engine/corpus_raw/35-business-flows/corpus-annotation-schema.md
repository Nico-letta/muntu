# Schema d'annotation corpus — Fintech Afrique (MUNTU v4.1)

> **Couche:** `35-business-flows` · **Role:** contrat de normalisation pour tous les exemples annotés  
> **Sources autorisees:** `Momo documentation.txt`, `Airtel.txt`, code `{afriwallet_codebase}` (manifest.json)  
> **Interdit:** inventer codes HTTP, statuts provider, ou champs API non presents dans la doc officielle

---

## Objectif

Garantir un corpus de **tres haute qualite** pour entrainement MoE et fine-tuning :
- chaque exemple est **traceable** a une source officielle ;
- chaque decision est **justifiee** par une chaine de raisonnement explicite ;
- la structure est **identique** entre MTN et Airtel pour faciliter le routing expert.

---

## Champs metadata obligatoires (bloc table)

Chaque exemple annoté commence par ce bloc :

| Champ | Type | Description |
|-------|------|-------------|
| `id` | string | Identifiant unique `EX-{PROVIDER}-{NNN}` (ex. `EX-MTN-001`) |
| `provider` | enum | `MTN_MOMO` \| `AIRTEL_OPEN_API` \| `CROSS_PROVIDER` |
| `source_officielle` | path | Fichier racine : `Momo documentation.txt` ou `Airtel.txt` |
| `section_doc` | string | Section exacte dans la doc (ex. `Common Error Codes`, `POST /standard/v3/disbursements`) |
| `pays` | ISO + OpCo | ex. `CG / mtncongo`, `CG / X-Country:CG` |
| `devise` | code | `XAF`, `EUR` (sandbox MTN), `XAF` (Airtel CG) |
| `flux` | string | ex. `RequestToPay`, `Disbursement Transfer`, `Cash-In Enquiry` |
| `async_mode` | enum | `async_202` (MTN) \| `sync_200` (Airtel) \| `enquiry_required` |
| `difficulte` | enum | `basic` \| `intermediate` \| `advanced` |
| `afriwallet_status` | enum | `deploye` \| `spec_officielle_non_deployee` \| `cross_provider` |
| `tags` | list | mots-cles pour routing MoE (ex. `callback`, `idempotence`, `ambiguous`) |

---

## Sections obligatoires par exemple

### 1. Contexte metier
Description courte du cas reel (support, integration, audit).

### 2. Artefacts officiels
Extraits **verbatim** de la documentation (requete, reponse, tableau erreur).
Ne pas paraphraser les codes ou statuts.

### 3. Annotation semantique
Decodage champ par champ : headers, body, statuts finaux vs intermediaires.

### 4. Chaine de justification
Liste ordonnee du raisonnement :
1. Fait observable (HTTP, code, statut)
2. Regle officielle applicable
3. Conclusion operationnelle
4. Action recommandee (sans supposer de code AfriWallet non deploye)

### 5. Mapping AfriWallet (implementation)
Lien avec Prisma (`Transaction`, `WebhookEvent`), `eventKey`, variables env.
Pour Airtel : **toujours** preciser `spec_officielle_non_deployee` (enum `AIRTEL` schema_only).
Ne pas utiliser le nom MUNTU dans cette section — voir `00-core-principles/muntu-engineering-identity.md`.

### 6. Anti-patterns
Erreurs frequentes d'integrateurs avec justification du risque.

### 7. Liens corpus
References croisees vers :
- `debug-scenarios-production.md` (scenario narratif correspondant)
- `30-system-integrations/provider-official-error-matrix-normalized.md`
- `30-system-integrations/source-docs/` (doc brute)

---

## Regles de qualite (lint implicite)

| Regle | Justification |
|-------|---------------|
| ASCII uniquement dans les fichiers markdown corpus | Compatibilite `generate_corpus.py` Windows |
| Pas de `implement` / `implementation` pour Airtel dans `35-business-flows` | Evite warnings lint ghost feature |
| Distinguer `status` HTTP vs `status` body vs `transaction.status` Airtel | Evite confusion modele |
| MTN : toujours mentionner 202 + callback unique + GET fallback | Doc officielle Callback section |
| Airtel : enquiry obligatoire si TA/TIP/0000900/ROUTER117 | Doc officielle Error Codes |
| Montants FCFA : entiers, jamais centimes | Convention AfriWallet BigInt |
| Citer `eventKey` avec pattern documente | ex. `mtn:r2p:{referenceId}` |
| MUNTU uniquement en couche meta (00-, prompts) | Evite confusion moteur IA vs wallet AfriWallet |
| AfriWallet dans code, flux, Prisma, providers | Precision chirurgicale sur l'implementation reelle |

---

## Relation avec les autres fichiers

```
corpus-annotation-schema.md          <- ce fichier (contrat)
annotated-provider-examples-normalized.md  <- exemples conformes au schema
debug-scenarios-production.md        <- scenarios narratifs (non modifie)
debug-qa-deep-training.md            <- Q&A comportemental
30-system-integrations/provider-official-error-matrix-normalized.md  <- matrices erreur
30-system-integrations/source-docs/  <- docs brutes Momo + Airtel
```

Les scenarios narratifs (`debug-scenarios-production.md`) restent la couche **storytelling**.
Les exemples normalises (`annotated-provider-examples-normalized.md`) sont la couche **evidence + justification**.
Les golden snippets `.ts` (exportes via `expand_corpus_sources.py --config configs/*.json`) sont la couche **code signature**.

### Fichiers TypeScript golden (compiles)

| Chemin corpus_raw | Source AfriWallet |
|-------------------|-------------------|
| `20-backend-api/golden-snippets/webhook-idempotence.ts` | webhooks.service.ts |
| `20-backend-api/golden-snippets/momo-payments-financial-core.ts` | payments.service.ts |
| `30-system-integrations/providers/mtn-momo.service.ts` | mtn.service.ts |
| `25-database-storage/prisma-critical-models.ts` | schema.prisma |

Regle : extraits signature uniquement — pas de boilerplate NestJS generique.
Relancer `python data_engine/expand_corpus_sources.py --config data_engine/configs/afriwallet.json` apres modification du codebase AfriWallet.
