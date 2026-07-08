# Frontend Mobile — State Management

> **Couche** : `10-frontend-mobile`

## État global recommandé

```json
{
  "auth": {
    "accessToken": "JWT",
    "phoneNumber": "string",
    "expiresAt": "derived from 15m TTL"
  },
  "user": {
    "kycStatus": "PENDING | VERIFIED | REJECTED",
    "wallets": [{ "id": "string", "balanceFcfa": "number for display" }]
  },
  "pending_operations": {
    "momoReferenceId": "string?",
    "pollIntervalMs": "dynamic from provider status"
  }
}
```

## Règle async

Ne jamais mettre `balanceFcfa` à jour optimistically sur cash-out — attendre SUCCESS ou afficher réservation PENDING.

## Voir aussi

- `20-backend-api/execution-lifecycle/async-pipeline-jobs.md`
