# MoMo Cash-Out — Reservation, disbursement et compensation

> **Couche:** `35-business-flows` · **Pattern critique:** hold immédiat + recrédit si echec provider  
> **Sources:** `src/payments/payments.service.ts`, `src/webhooks/webhooks.service.ts`

---

## 1. Pourquoi la compensation est non-negociable

En cash-out MoMo, AfriWallet **decremente le wallet immédiatement** lors de l'initiation (reservation), avant confirmation MTN Disbursement.

Si MTN retourne FAILED/REJECTED apres coup, le client perdrait de l'argent sans compensation.

**Pattern implemente:**
```
Initiation -> wallet -= amount (PENDING)
Echec provider -> wallet += amount (FAILED)  // COMPENSATION
Succes provider -> wallet inchange (deja decremente) -> SUCCESS
```

---

## 2. Sequence nominale

```
POST /payments/withdraw/momo { phoneNumber, amountFcfa: 10000 }
  -> verify KYC VERIFIED
  -> verify wallet.balanceFcfa >= amountFcfa
  -> MtnService.initiateTransfer()  // Disbursement API
  -> prisma.$transaction([
       wallet.decrement(balanceFcfa),
       transaction.create(CASH_OUT_MOMO, PENDING, providerTxId=referenceId)
     ])
  -> return { status: PENDING, referenceId }

MTN traite transfer vers MSISDN payee

Webhook SUCCESSFUL:
  -> transaction.status = SUCCESS (wallet deja decremente)

Webhook FAILED/REJECTED:
  -> prisma.$transaction([
       wallet.increment(amountFcfa),  // COMPENSATION
       transaction.update(FAILED, failureReason)
     ])
```

---

## 3. Code compensation webhook (extrait canonique)

```typescript
if (providerStatus === 'FAILED' || providerStatus === 'REJECTED') {
  if (tx.type === TransactionType.CASH_OUT_MOMO) {
    await this.prisma.$transaction([
      this.prisma.wallet.update({
        where: { id: tx.walletId },
        data: { balanceFcfa: { increment: tx.amountFcfa } },
      }),
      this.prisma.transaction.update({
        where: { id: tx.id },
        data: {
          status: TransactionStatus.FAILED,
          failureReason: reason,
          metadata: payload,
        },
      }),
    ]);
  }
}
```

Meme logique dans `syncMomoWithdrawStatus()` pour le polling fallback.

---

## 4. Scenarios d'echec disbursement

| Scenario MTN | MSISDN sandbox | Effet wallet |
|--------------|----------------|--------------|
| PayeeNotEnoughFunds | 46733123455 | Compensation si FAILED |
| PayeeNotFound | 46733123457 | Compensation |
| PayeeInternalProcessingError | 46733123462 | Compensation |
| Forbidden IP | N/A (config) | Compensation si echec HTTP |
| Timeout 5 min | 46733123463 | Poll puis compensation si FAILED |

---

## 5. Race conditions

### Webhook + Poll simultanes
- Les deux chemins verifient `tx.status === PENDING` avant mutation
- Transaction deja SUCCESS/FAILED -> idempotent, pas de double compensation

### Double webhook MTN
- eventKey `mtn:r2p:{referenceId}` + P2002 -> ignore silencieusement
- Transaction finalisee -> return early

### Initiation dupliquee meme referenceId
- Prisma P2002 sur providerTxId -> retour idempotent `{ status, referenceId }`

---

## 6. Invariants comptables

A tout instant:
```
sum(wallet.balanceFcfa) + sum(pending_cash_out_reservations)
  == solde theorique client
```

Apres compensation FAILED:
- Solde client = solde avant initiation (integrite preservee)

Apres SUCCESS:
- Solde client = solde avant - amount (fonds arrives sur MoMo MSISDN)

---

## 7. UX recommandations

1. Afficher "Retrait en cours" des l'initiation PENDING
2. Ne pas permettre nouveau retrait si un CASH_OUT_MOMO PENDING existe (future regle metier)
3. Sur FAILED: message clair + solde recredite automatiquement
4. SmartSelfie step-up recommande pour `large_withdrawal` (decorrele KYC legal)

---

## 8. Headers Disbursement vs Collection

Cash-out utilise un **token disbursement separe**:
- Collection token: `/collection/token/` ou `/oauth2/v1_0/token`
- Disbursement token: `/disbursement/token/`

Subscription key Disbursement != Collection key (produits MTN separes).

IP publique doit etre whiteliste pour Disbursement (`403 FORBIDDEN IP` sinon).

---

## 9. Checklist debug production

1. referenceId existe en DB avec type CASH_OUT_MOMO ?
2. Wallet a ete decremente a l'initiation ?
3. Webhook recu ? eventKey dans WebhookEvent ?
4. providerStatus dans metadata ?
5. Si FAILED: compensation increment visible dans historique Transaction ?
6. X-Target-Environment = mtncongo ?
7. Subscription key Disbursement correcte ?
