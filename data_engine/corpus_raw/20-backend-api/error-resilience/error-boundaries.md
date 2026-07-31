# Résilience — Error Boundaries & Compensation

> **Couche** : `20-backend-api/error-resilience` · **Axe** : pannes propres, pas de perte de fonds  
> **Source** : `src/webhooks/webhooks.service.ts`, `src/auth/auth.service.ts`

## Contexte

Le backend NestJS AfriWallet privilégie : réponses HTTP explicites, journal immuable, compensation cash-out, pas de fuite OTP en prod.

## Contrat — Exceptions auth (UX FR)

```json
{
  "403": "Ce numero est deja active. Utilisez le PIN pour vous connecter.",
  "410": "Le code OTP a expire. Veuillez en demander un nouveau.",
  "429": "Trop de demandes de code. Reessayez dans une heure.",
  "401": "Invalid credentials (PIN)"
}
```

## Contrat — Idempotence transaction

```json
{
  "providerTxId": "@unique — MTN referenceId UUID",
  "on_duplicate_P2002": "return existing referenceId, no second MTN call",
  "journal_rule": "Transaction immutable — only status/metadata update"
}
```

## Contrat — Compensation cash-out

```json
{
  "trigger": "providerStatus FAILED or REJECTED",
  "action": "wallet.balanceFcfa increment by tx.amountFcfa",
  "transaction_status": "FAILED",
  "reason": "Consumer protection — funds never lost on provider failure"
}
```

## Contrat — Webhook processing failure

```json
{
  "on_error": "WebhookEvent.error = message, rethrow or log",
  "on_unknown_tx": "MTN callback unknown referenceId → 200 received (avoid retries storm)"
}
```

---

## Golden Snippets — compensation cash-out MoMo

Le solde est **décrémenté à l'initiation** (réservation PENDING). Si MTN renvoie `FAILED`/`REJECTED`, recrédit atomique — protection consommateur.

### Réservation solde à l'initiation

```typescript
// src/payments/payments.service.ts — initiateMomoWithdraw()
const amountBigInt = BigInt(amountFcfa);
if (wallet.balanceFcfa < amountBigInt) {
  throw new BadRequestException('Insufficient wallet balance');
}

const { referenceId } = await this.mtn.initiateTransfer({ phoneNumber, amountFcfa });

// Décrément immédiat en PENDING (réserve le FCFA)
await this.prisma.$transaction([
  this.prisma.wallet.update({
    where: { id: wallet.id },
    data: { balanceFcfa: { decrement: amountBigInt } },
  }),
  this.prisma.transaction.create({
    data: {
      amountFcfa: amountBigInt,
      type: TransactionType.CASH_OUT_MOMO,
      status: TransactionStatus.PENDING,
      providerTxId: referenceId, // UUID MTN = clé idempotence
    },
  }),
]);
```

### Compensation webhook (chemin principal)

```typescript
// src/webhooks/webhooks.service.ts
if (providerStatus === 'FAILED' || providerStatus === 'REJECTED') {
  if (tx.type === TransactionType.CASH_OUT_MOMO) {
    await this.prisma.$transaction([
      this.prisma.wallet.update({
        where: { id: tx.walletId },
        data: { balanceFcfa: { increment: tx.amountFcfa } },
      }),
      this.prisma.transaction.update({
        where: { id: tx.id },
        data: { status: TransactionStatus.FAILED, failureReason: reason },
      }),
    ]);
  }
}
```

### Compensation polling (fallback si webhook perdu)

```typescript
// src/payments/payments.service.ts — syncMomoWithdrawStatus()
if (providerStatus === 'FAILED' || providerStatus === 'REJECTED') {
  if (tx.status === TransactionStatus.PENDING) {
    await this.prisma.$transaction([
      this.prisma.wallet.update({
        where: { id: tx.walletId },
        data: { balanceFcfa: { increment: tx.amountFcfa } },
      }),
      this.prisma.transaction.update({
        where: { id: tx.id },
        data: { status: TransactionStatus.FAILED },
      }),
    ]);
  }
}
```

## Retry policies (HTTP outbound)

```json
{
  "ONAFRIQ": {
    "timeout_ms": 10000,
    "retry_count": 2,
    "backoff_ms": 400,
    "retriable": [408, 429, "5xx"]
  }
}
```

## Voir aussi

- `30-system-integrations/provider-error-codes.md`
- `90-codebase-constraints/project-roadmap.md`
