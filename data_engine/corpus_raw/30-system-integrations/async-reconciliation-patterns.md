# Async Reconciliation — Machine à états Mobile Money

> **Couche** : `30-system-integrations` · **Expert MoE** : asynchronisme FinTech (≠ REST sync type Stripe)  
> **Source** : `src/payments/payments.service.ts`, `src/webhooks/webhooks.service.ts`, `src/providers/mtn.service.ts`

## Contexte — le piège des LLM génériques

Un **RequestToPay** MTN renvoie `HTTP 202 Accepted` — **pas** un succès financier. Le wallet reste inchangé jusqu'à preuve `SUCCESSFUL`/`SUCCESS` via **webhook** ou **polling de secours**. Confondre 202 avec 200 = double crédit ou solde fantôme.

```
[SYNC FAUX — Stripe-like]     POST → 200 → wallet crédité     
[ASYNC AfriWallet — MoMo]     POST → 202 → PENDING → webhook → SUCCESS → crédit  
```

---

## Machine à états — Transaction MoMo

```json
{
  "states": {
    "INIT": "Validation KYC + montant > 0",
    "PENDING": "Transaction créée, providerTxId = UUID MTN",
    "SUCCESS": "Webhook/poll confirme SUCCESSFUL — mutation wallet finalisée",
    "FAILED": "Webhook/poll FAILED/REJECTED — compensation si CASH_OUT"
  },
  "transitions": {
    "CASH_IN": {
      "INIT→PENDING": "MTN RequestToPay 202, pas de crédit wallet",
      "PENDING→SUCCESS": "increment balanceFcfa",
      "PENDING→FAILED": "tx FAILED, wallet inchangé (jamais crédité)"
    },
    "CASH_OUT": {
      "INIT→PENDING": "decrement balanceFcfa IMMÉDIAT (réservation)",
      "PENDING→SUCCESS": "tx SUCCESS, solde déjà débité",
      "PENDING→FAILED": "COMPENSATION increment balanceFcfa + tx FAILED"
    }
  }
}
```

---

## Phase 1 — Création & réservation

### Cash-in (pas de débit/crédit avant SUCCESS)

```typescript
// src/payments/payments.service.ts — initiateMomoDeposit()
const { referenceId, status } = await this.mtn.initiateRequestToPay({ phoneNumber, amountFcfa });
// HTTP 202 côté MTN — status souvent PENDING

await this.prisma.transaction.create({
  data: {
    amountFcfa: BigInt(amountFcfa),
    type: TransactionType.CASH_IN_MOMO,
    status: TransactionStatus.PENDING,
    providerTxId: referenceId, // clé corrélation webhook
  },
});
// wallet.balanceFcfa INCHANGÉ jusqu'à SUCCESS
```

### Cash-out (réservation immédiate)

```typescript
const amountBigInt = BigInt(amountFcfa);
await this.prisma.$transaction([
  this.prisma.wallet.update({
    data: { balanceFcfa: { decrement: amountBigInt } },
  }),
  this.prisma.transaction.create({
    data: { amountFcfa: amountBigInt, type: CASH_OUT_MOMO, status: PENDING, providerTxId: referenceId },
  }),
]);
```

---

## Phase 2 — Réconciliation webhook (chemin nominal)

Ordre strict dans `handleMtnRequestToPayCallback()` :

1. Résoudre tx par `providerTxId === referenceId`
2. `WebhookEvent.create({ eventKey: 'mtn:r2p:{referenceId}' })` — catch P2002 → stop
3. Si tx déjà SUCCESS/FAILED → idempotent return
4. Appliquer transition selon `providerStatus`

Voir golden snippets complets : `../20-backend-api/input-boundaries/webhook-security.md`

---

## Phase 3 — Polling de secours (callback manquant)

Si MTN ne rappelle pas dans le délai UX :

```json
{
  "intervals_ms": { "CREA": 2000, "PENDING": 10000, "default": 30000 },
  "endpoints": {
    "deposit": "GET /payments/deposit/momo/:referenceId/status",
    "withdraw": "GET /payments/withdraw/momo/:referenceId/status"
  },
  "rule": "Ne jamais supposer succès sur seul 202 Accepted — GET status obligatoire"
}
```

Compensation polling cash-out (même logique que webhook) :

```typescript
// src/payments/payments.service.ts — syncMomoWithdrawStatus()
if (providerStatus === 'FAILED' || providerStatus === 'REJECTED') {
  if (tx.status === TransactionStatus.PENDING) {
    await this.prisma.$transaction([
      this.prisma.wallet.update({ data: { balanceFcfa: { increment: tx.amountFcfa } } }),
      this.prisma.transaction.update({ data: { status: TransactionStatus.FAILED } }),
    ]);
  }
}
```

---

## Phase 4 — Edge cases & idempotence

| Scénario | Comportement AfriWallet |
|----------|-------------------------|
| Webhook dupliqué | `eventKey` unique → P2002 → 200 silencieux |
| Webhook après poll SUCCESS | tx déjà finalisée → skip mutation |
| referenceId inconnu | log warn + 200 (éviter retry storm MTN) |
| Timeout MTN > 5 min | `COULD_NOT_PERFORM_TRANSACTION` → FAILED + compensation cash-out |
| Cash-in FAILED | wallet jamais crédité — tx FAILED only |

---

## Statuts provider normalisés

```json
{
  "success": ["SUCCESSFUL", "SUCCESS", "ACSC"],
  "failed": ["FAILED", "REJECTED", "RJCT", "CANC", "CANCELLED"],
  "pending": ["CREA", "ACTC", "PDNG", "PENDING", "UNKNOWN"]
}
```

## Voir aussi

- `provider-error-codes.md` — codes MTN/Airtel pour blocs catch TypeScript
- `provider-specs.md` — headers & endpoints
- `../20-backend-api/error-resilience/error-boundaries.md` — compensation détaillée
- `../35-business-flows/afriwallet-business-flows.md` — flux métier utilisateur
