# PostgreSQL — Politiques AfriWallet

> **Couche** : `25-database-storage` · **Stack** : PostgreSQL 16, Docker  
> **Source** : `docker-compose.yml`, `prisma/schema.prisma`

## Contexte

AfriWallet utilise PostgreSQL via Prisma. Les montants FCFA sont des **BigInt entiers** — jamais DECIMAL/FLOAT pour éviter les erreurs d'arrondi.

## Contrat — Configuration

```json
{
  "database": "PostgreSQL 16",
  "provider": "postgresql",
  "connection": "DATABASE_URL env",
  "schema": "public"
}
```

## Contrat — Indexation

```json
{
  "Transaction": ["walletId + createdAt"],
  "OtpRequest": ["phoneNumber + createdAt"],
  "unique_constraints": [
    "User.phoneNumber",
    "Wallet.userId",
    "Transaction.providerTxId",
    "Transaction.idempotencyKey",
    "WebhookEvent.eventKey"
  ]
}
```

## Contrat — Rétention (maintenance cron 2h)

```json
{
  "OtpRequest_expired": "purge after 7 days (OTP_RETENTION_DAYS)",
  "WebhookEvent_processed": "purge after 30 days (WEBHOOK_RETENTION_DAYS)",
  "Transaction": "never deleted — immutable journal"
}
```

## Règles

- Toute mutation solde wallet = transaction Prisma atomique avec enregistrement `Transaction`.
- Pas de multi-wallet : `Wallet.userId @unique`.

## Voir aussi

- `25-database-storage/prisma-patterns.md`
