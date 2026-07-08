# Codebase Constraints — Project Roadmap (Savoir Négatif)

> **Couche** : `90-codebase-constraints` · **Expert MoE** : anti-hallucination **uniquement**  
> **Source** : `prisma/schema.prisma` vs `src/`  
> **Règle** : ce dossier = limites, enums fantômes, features absentes — **pas** les codes erreur providers (→ `30-system-integrations/provider-error-codes.md`)

## Contexte

Le modèle **NE DOIT PAS** générer de code ou confirmer des features listées ci-dessous comme `schema_only`. Les enums Prisma existent ; les services **non**.

---

## Protocole migration 90 → 30 (features fantômes)

Quand l'équipe **implémente** un provider ou flux :

| Étape | Action |
|-------|--------|
| 1 | Créer le service dans `src/providers/` ou `src/payments/` |
| 2 | Retirer l'entrée `NON IMPLÉMENTÉ` de ce fichier |
| 3 | Déplacer la spec draft `90-…/xxx-specs-draft.md` → `30-system-integrations/xxx-specs.md` |
| 4 | Mettre à jour `25-database-storage/prisma-patterns.md` si enum passe à `implemented` |
| 5 | Régénérer corpus : `python generate_corpus.py` (linter inclus) |

**Tant que non codé** : spec marché reste en `90-codebase-constraints/` (ex. `airtel-money-specs-draft.md`).

---

## Contrat — Planifié NON implémenté (interdit de coder)

```json
{
  "AIRTEL_MOMO": {
    "evidence": ["TransactionType.CASH_IN_AIRTEL", "PaymentProvider.AIRTEL"],
    "status": "schema_only",
    "has_service": false,
    "has_webhook": false,
    "spec_draft": "90-codebase-constraints/airtel-money-specs-draft.md",
    "error_codes_reference": "30-system-integrations/provider-error-codes.md §5-12 (marché only)",
    "model_must_say": "Non implemente — enum Prisma uniquement"
  },
  "CARD_PAYMENT": {
    "evidence": "TransactionType.CARD_PAYMENT",
    "status": "schema_only"
  },
  "CARD_REFUND": {
    "evidence": "TransactionType.CARD_REFUND",
    "status": "schema_only"
  },
  "KYC_BIOMETRIC_CM": {
    "evidence": "CM absent de smile-id-id-rules.ts",
    "workaround": "Onafriq defaults CM, document verification CG only — voir cemac-cobac.md"
  },
  "DYNAMIC_FEES": {
    "field": "feeFcfa",
    "current": "always 0 in all services"
  },
  "MULTI_WALLET": {
    "constraint": "Wallet.userId @unique",
    "current": "1 wallet per user"
  }
}
```

## Contrat — Implémenté et sûr à documenter

```json
{
  "implemented": [
    "OTP SMS + PIN bcrypt + JWT",
    "Wallet FCFA BigInt",
    "KYC biometric 8 countries + document CG",
    "SmartSelfie step-up (decorrelated from legal KYC)",
    "MTN MoMo cash-in/out with cash-out compensation",
    "Bridge sandbox deposit",
    "Onafriq virtual cards + freeze webhooks",
    "Webhooks idempotent: MTN, Smile, Onafriq, Bridge"
  ]
}
```

## Phrases types pour le modèle

| Question utilisateur | Réponse correcte |
|---------------------|------------------|
| "Implémente Airtel cash-in" | Enum existe, aucun service — voir spec draft 90, pas de routes |
| "Paiement par carte CARD_PAYMENT" | TransactionType existe, non implémenté |
| "KYC biométrique Cameroun CM" | Pas dans Smile ID rules — voir `cemac-cobac.md` |
| "Frais dynamiques feeFcfa" | Champ existe, toujours 0 |
| "Code erreur MTN 409" | Voir `30-system-integrations/provider-error-codes.md` (pas ici) |

## Enrichissement externe requis

- Textes BEAC, BCEAO, CBN officiels (hors codebase)
- Orange Money, Wave, M-Pesa (absents)

## Voir aussi

- `25-database-storage/prisma-patterns.md`
- `40-compliance-rules/cemac-cobac.md` · `uemoa-bceao.md` · `cbn-nigeria.md`
- `30-system-integrations/async-reconciliation-patterns.md`
