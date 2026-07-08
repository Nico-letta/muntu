# Nigeria — CBN, NIMC & KYC Tier (NG)

> **Couche** : `40-compliance-rules` · **Zone** : Nigeria · **Devise** : NGN (KYC) / sandbox MoMo EUR  
> **Expert MoE** : identité NIN/BVN — **ne jamais appliquer sur CM, CG ou CI**

## Régulateurs & identité

| Autorité | Rôle |
|----------|------|
| CBN | Régulation paiements, KYC tiers |
| NIMC | National Identification Number (NIN) |

```json
{
  "country": "NG",
  "regulators": ["CBN", "NIMC"],
  "mtn_opco_prod": "mtnnigeria",
  "id_formats": {
    "NIN": "^\\d{11}$",
    "NIN_V2": "^\\d{11}$",
    "BVN": "^\\d{11}$",
    "V_NIN": "^[A-Za-z0-9]{16}$"
  },
  "anti_cross_zone": {
    "rule": "Toute validation idNumber 11 digits NG est EXCLUSIVE au pays NG",
    "forbidden": "Rejeter ou accepter un NIN camerounais avec regex NG"
  }
}
```

## KYC biométrique Nigeria (AfriWallet)

- Template par défaut Smile : `NIN_V2` + 11 digits.
- Images : selfie (type 0) + 8 frames liveness (type 4).
- Webhook Smile met à jour `kycStatus` — distinct de SmartSelfie step-up.

## MoMo MTN Nigeria

- Prod : `X-Target-Environment: mtnnigeria`.
- Sandbox MTN Developer : currency `EUR`, env `sandbox` — **ne pas confondre** avec prod NGN/XAF wallet AfriWallet.
- Codes erreur MTN spécifiques : `provider-error-codes.md` §2 matrix.

## Compliance hints

- KYC tiering CBN : vérification registre via Smile ID avant cash-in/out significatif.
- Fraude : velocity + SIM swap cooling (voir `fraud-vectors-security.md`).

## Voir aussi

- `kyc-id-rules-by-country.md` — contrat JSON complet NG
- `cemac-cobac.md` / `uemoa-bceao.md` — autres zones
- `../30-system-integrations/provider-error-codes.md` — MTN mtnnigeria errors
