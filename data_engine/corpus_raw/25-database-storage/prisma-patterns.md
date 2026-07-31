# Prisma — Patterns & Schéma AfriWallet

> **Couche** : `25-database-storage` · **ORM** : Prisma Client  
> **Source** : `prisma/schema.prisma`

## Contexte

Le schéma Prisma encode les invariants métier. Le modèle **ne doit pas** être étendu avec des features non implémentées sans mise à jour de `90-codebase-constraints/project-roadmap.md`.

## Contrat — User

```json
{
  "User": {
    "phoneNumber": "String @unique",
    "pinHash": "String bcrypt",
    "kycStatus": "KycStatus default PENDING",
    "kycReference": "String?",
    "smartSelfieLastAuthSuccess": "Boolean? — decorrelated from kycStatus"
  }
}
```

## Contrat — Wallet

```json
{
  "Wallet": {
    "userId": "String @unique — one wallet per user",
    "balanceFcfa": "BigInt @default(0) — integer FCFA only"
  }
}
```

## Contrat — Transaction (journal immuable)

```json
{
  "Transaction": {
    "amountFcfa": "BigInt",
    "feeFcfa": "BigInt @default(0) — always 0 in current impl",
    "currency": "String @default XAF",
    "type": "TransactionType",
    "status": "TransactionStatus",
    "providerTxId": "String? @unique",
    "metadata": "Json? — webhook payload, card passCode"
  },
  "mutable_fields_only": ["status", "failureReason", "metadata"]
}
```

## Contrat — Enums avec statut implémentation

```json
{
  "PaymentProvider": {
    "MTN_MOMO": "implemented",
    "ONAFRIQ": "implemented",
    "SMILE_ID": "implemented",
    "BRIDGE": "implemented",
    "AIRTEL": "schema_only — NO service in src/"
  },
  "TransactionType": {
    "CASH_IN_MOMO": "implemented",
    "CASH_OUT_MOMO": "implemented",
    "CARD_ISSUANCE_FEE": "implemented",
    "ADJUSTMENT": "implemented Bridge",
    "CASH_IN_AIRTEL": "schema_only",
    "CARD_PAYMENT": "schema_only",
    "CARD_REFUND": "schema_only"
  }
}
```

## Patterns Prisma obligatoires

- Mutation solde + Transaction = `$transaction([...])` atomique.
- Webhook idempotence = `webhookEvent.create` avec catch P2002.
- BigInt API response = `Number(balanceFcfa)` pour JSON uniquement.

---

## Golden Snippets — BigInt FCFA (pas de float)

JavaScript `number` perd la précision au-delà de 2^53. AfriWallet stocke les montants FCFA en **entiers BigInt** côté Prisma ; conversion explicite à la frontière API.

### Schéma Prisma (source de vérité)

```prisma
// prisma/schema.prisma
model Wallet {
  /// Solde disponible en FCFA (unités entières, jamais de centimes EUR).
  balanceFcfa  BigInt  @default(0)
}

model Transaction {
  amountFcfa     BigInt
  feeFcfa        BigInt  @default(0)
  providerTxId   String? @unique  // UUID MTN pour idempotence
}

model WebhookEvent {
  eventKey  String  @unique  // job_id Smile, mtn:r2p:{id}, etc.
  payload   Json
}
```

### Écriture — `number` API → `BigInt` Prisma

```typescript
// src/payments/payments.service.ts
const amountBigInt = BigInt(amountFcfa);
if (wallet.balanceFcfa < amountBigInt) {
  throw new BadRequestException('Insufficient wallet balance');
}

await this.prisma.wallet.update({
  where: { id: wallet.id },
  data: { balanceFcfa: { increment: amountBigInt } }, // ou decrement
});
```

### Lecture — `BigInt` Prisma → `number` JSON

```typescript
// src/wallets/wallets.service.ts — sérialisation réponse API
return {
  balanceFcfa: Number(wallet.balanceFcfa),
  transactions: txs.map((tx) => ({
    amountFcfa: Number(tx.amountFcfa),
  })),
};
```

> **Invariant** : jamais `amountFcfa / 100` ni `parseFloat` sur un montant wallet — le FCFA CEMAC est déjà en unités entières.

## Voir aussi

- `90-codebase-constraints/project-roadmap.md`
- `25-database-storage/postgres-policies.md`
