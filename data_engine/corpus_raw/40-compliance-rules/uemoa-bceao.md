# UEMOA — BCEAO & Mobile Money (CI, XOF)

> **Couche** : `40-compliance-rules` · **Zone** : UEMOA · **Devise** : XOF  
> **Expert MoE** : Côte d'Ivoire et pays BCEAO — **distinct de CEMAC (XAF) et Nigeria (NGN)**

## Périmètre

| Élément | Valeur corpus AfriWallet |
|---------|--------------------------|
| Pays KYC biometric | CI (Côte d'Ivoire) dans registre Smile |
| Devise zone | XOF (Franc CFA BCEAO) |
| Régulateur | BCEAO |
| Canal dominant | USSD ~89% volumes MoMo (BCEAO) |

```json
{
  "regulators": ["BCEAO"],
  "currency": "XOF",
  "anti_cross_zone": {
    "forbidden": "Appliquer règles CEMAC/COBAC (XAF, mtncameroon) sur onboarding CI",
    "forbidden_2": "Confondre ISO CI (UEMOA) avec CG (CEMAC) — acronymes proches, zones différentes"
  }
}
```

## KYC Côte d'Ivoire (CI)

- Smile ID biometric : `NATIONAL_ID_NO_PHOTO` regex `^(?:\d{11}|[A-Za-z]\d{10})$`.
- Flux REST : upload-url → ZIP selfie + liveness → webhook `job_success`.
- **Obligatoire** `kycStatus=VERIFIED` avant MoMo ou cartes (règle globale AfriWallet).

## Mobile Money UEMOA

- MTN OpCo exemple : `mtnivorycoast` (voir matrice env dans `provider-error-codes.md`).
- Même pattern **async** que CEMAC : HTTP 202 → PENDING → webhook/polling.
- Headers géo doivent refléter le pays cible — pas de `mtncameroon` pour un MSISDN CI.

## Macro marché (contexte modèle)

- USSD reste couche fallback obligatoire (< 48% smartphones en Afrique subsaharienne).
- Volumes MoMo UEMOA : voir `macro-metrics.md`.

## Voir aussi

- `kyc-id-rules-by-country.md` — section CI
- `../35-business-flows/afriwallet-business-flows.md` — cinématique MoMo
- `cemac-cobac.md` — zone XAF (ne pas fusionner)
