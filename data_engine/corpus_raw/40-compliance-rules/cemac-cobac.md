# CEMAC — BEAC, COBAC & Mobile Money (CM, CG)

> **Couche** : `40-compliance-rules` · **Zone** : CEMAC · **Devise** : XAF  
> **Expert MoE** : régulation Cameroun + Congo — **ne pas mélanger avec Nigeria (NG) ni UEMOA (XOF)**

## Périmètre AfriWallet

| Pays | ISO | Devise | OpCo MTN prod | KYC AfriWallet |
|------|-----|--------|---------------|----------------|
| Cameroun | CM | XAF | `mtncameroon` | **Pas** de registre biométrique Smile — defaults Onafriq |
| Congo-Brazzaville | CG | XAF | `mtncongo` | Document verification job_type 11 **uniquement** |

```json
{
  "regulators": ["BEAC", "COBAC"],
  "currency_rule": "BigInt entiers XAF — jamais centimes EUR",
  "anti_cross_zone": {
    "forbidden": "Appliquer NIN/BVN nigérian (11 digits) sur flux CM/CG",
    "forbidden_2": "Utiliser devise XOF ou headers UEMOA sur wallet XAF"
  }
}
```

## Cameroun (CM)

- Onboarding cartes Onafriq : defaults `country=CM`, `phone=237`, `city=Douala`, `currency=XAF`.
- KYC biométrique Smile ID : **CM absent** du registre `smile-id-id-rules.ts` — ne pas générer de flux NIN/selfie pour CM.
- MoMo MTN : `X-Target-Environment: mtncameroon`, currency prod `XAF`.

## Congo (CG)

- KYC : **document verification only** (pas biometric registry standard).
- Smile job_type `11`, id_types : `IDENTITY_CARD`, `PASSPORT`, `DRIVERS_LICENSE`, etc.
- MoMo MTN : `X-Target-Environment: mtncongo`.

## Plafonds & conformité (hints non-juridiques)

- COBAC encadre établissements de paiement CEMAC — KYC avant mouvements significatifs.
- Fraude agent / SIM swap : appliquer velocity limits (voir `fraud-vectors-security.md`).
- Interprétation juridique définitive : consulter BEAC/COBAC local.

## Voir aussi

- `kyc-id-rules-by-country.md` — section CG document verification
- `../30-system-integrations/provider-specs.md` — MTN + Onafriq
- `../90-codebase-constraints/project-roadmap.md` — KYC_BIOMETRIC_CM non supporté
