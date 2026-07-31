# Policies — Compliance et Sécurité

> **Couche** : `40-compliance-rules` · **Contraintes non-négociables**  
> **Source** : `auth.service.ts`, `webhooks.service.ts`, `payments.service.ts`

## Règles compliance

### KYC avant mouvement d'argent

```json
{
  "rule": "kycStatus must be VERIFIED",
  "applies_to": [
    "POST /payments/deposit/momo",
    "POST /payments/withdraw/momo",
    "POST /payments/deposit/bridge",
    "POST /virtual-cards"
  ]
}
```

### Journal immuable

Les transactions ne sont pas supprimées — seul `status` et `metadata` évoluent.

### Compensation cash-out

Obligatoire si Disbursement FAILED après réservation solde.

## Contrat — OTP rate limiting

```json
{
  "cooldown_seconds": 60,
  "max_per_hour": 5,
  "max_per_day": 10,
  "max_attempts": 3,
  "ttl_minutes": 5,
  "production_sms_required": true
}
```

## Contrat — Rétention données

```json
{
  "otp_expired_days": 7,
  "webhooks_processed_days": 30,
  "cron": "every 2 hours"
}
```

## Hints réglementaires (non-juridiques)

| Zone | Régulateur | Contexte corpus |
|------|------------|-----------------|
| CEMAC | BEAC, COBAC | XAF, CM defaults |
| UEMOA | BCEAO | CI KYC |
| Nigeria | CBN, NIMC | NIN/BVN |

> Interprétation juridique définitive : consulter régulateur local.

## Voir aussi

- [Flux metier AfriWallet](../35-business-flows/afriwallet-business-flows.md)
- [Webhooks](../20-backend-api/input-boundaries/webhook-security.md)
