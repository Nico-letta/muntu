# MoMo Cash-In Congo — Parcours technique complet

> **Couche:** `35-business-flows` · **Expert MoE:** orchestration transactionnelle  
> **Contexte:** AfriWallet · MTN MoMo · Zone CEMAC · Devise prod XAF  
> **Sources:** `src/payments/payments.service.ts`, `src/providers/mtn.service.ts`, `src/webhooks/webhooks.service.ts`

---

## 1. Acteurs et preconditions

| Acteur | Role |
|--------|------|
| Client mobile | Confirme le debit MoMo sur USSD/App MTN |
| App AfriWallet | Envoie JWT + montant FCFA entier |
| API NestJS | Valide KYC, persiste Transaction PENDING |
| MTN MoMo Gateway | RequestToPay async HTTP 202 |
| Webhook MTN | Callback final SUCCESSFUL/FAILED (une seule fois) |
| Polling fallback | GET status si callback manquant |

**Preconditions obligatoires:**
- `user.kycStatus === VERIFIED` (sinon `400 KYC verification required`)
- `amountFcfa > 0` entier (pas de float, pas de centimes)
- MSISDN enregistre MTN MoMo avec fonds suffisants cote operateur
- En prod Congo: `X-Target-Environment: mtncongo`, currency `XAF`
- En sandbox: `sandbox` + `EUR` (documentation MTN)

---

## 2. Sequence nominale (happy path)

```
Client -> POST /payments/deposit/momo { phoneNumber, amountFcfa: 5000 }
  -> PaymentsService.initiateMomoDeposit()
    -> verify KYC VERIFIED
    -> MtnService.initiateDebit()
      -> POST /collection/v1_0/requesttopay
      -> Headers: Bearer, X-Reference-Id (UUID v4), X-Target-Environment
      -> Response HTTP 202 Accepted
    -> prisma.transaction.create()
      type: CASH_IN_MOMO
      status: PENDING
      providerTxId: referenceId (UUID)
  -> API response { status: PENDING, referenceId }

Client confirme sur telephone MTN (USSD ou app MoMo)

MTN -> PUT/POST /webhooks/mtn/requesttopay/{referenceId}
  -> WebhooksService.handleMtnRequestToPayCallback()
    -> webhookEvent.create eventKey=mtn:r2p:{referenceId}
    -> if status SUCCESSFUL:
         wallet.balanceFcfa += amountFcfa
         transaction.status = SUCCESS
```

---

## 3. Payload MTN RequestToPay (AfriWallet)

```typescript
const body = {
  amount: amountFcfa.toString(),
  currency: this.config.currency, // XAF prod, EUR sandbox
  externalId: referenceId,
  payer: {
    partyIdType: 'MSISDN',
    partyId: phoneNumber,
  },
  payerMessage: 'AfriWallet wallet top-up',
  payeeNote: 'AfriWallet wallet top-up',
};
```

Headers critiques:
- `Authorization: Bearer {collection_access_token}`
- `X-Reference-Id: {uuid_v4}` — DOIT etre unique, sinon `409 RESOURCE_ALREADY_EXIST`
- `Ocp-Apim-Subscription-Key: {collection_subscription_key}`
- `X-Callback-Url: {base}/webhooks/mtn/requesttopay/{referenceId}` (optionnel mais recommande)

---

## 4. Etats internes vs etats MTN

| MTN status | Transaction AfriWallet | Action wallet |
|------------|------------------------|---------------|
| (initial) | PENDING | Aucun mouvement |
| SUCCESSFUL / SUCCESS | SUCCESS | increment balanceFcfa |
| FAILED / REJECTED | FAILED | Aucun credit (cash-in) |
| PENDING | PENDING | Attendre callback ou poll |

**Regle d'or:** Ne jamais crediter le wallet sur seul `202 Accepted`. Le 202 signifie uniquement "requete validee et en file d'attente".

---

## 5. Polling fallback (client ou cron)

Endpoint: `GET /payments/deposit/momo/:referenceId/status`

```typescript
// payments.service.ts — syncMomoDepositStatus()
const status = await this.mtn.getRequestToPayStatus(referenceId);
const providerStatus = String(normalized?.status ?? '').toUpperCase();

if (providerStatus === 'SUCCESSFUL' || providerStatus === 'SUCCESS') {
  if (tx.status === TransactionStatus.PENDING) {
    await prisma.$transaction([
      wallet.update({ balanceFcfa: { increment: tx.amountFcfa } }),
      transaction.update({ status: SUCCESS, metadata: normalized }),
    ]);
  }
}
```

Intervalles recommandes (`getNextPollInMs`):
- `CREA`, `ACTC` -> 2000 ms
- `PENDING`, `PDNG`, `UNKNOWN` -> 10000 ms
- Autres -> 30000 ms

---

## 6. Scenarios d'echec et remediation

### 6.1 KYC non verifie
- **Symptome:** `400 KYC verification required before MoMo deposit`
- **Cause:** `kycStatus` PENDING ou REJECTED
- **Action:** Rediriger vers flux `/kyc/start` puis Smile ID webhook

### 6.2 MSISDN invalide ou non enregistre MoMo
- **Symptome MTN:** `PAYER_NOT_FOUND` ou `INTERNAL_PROCESSING_ERROR`
- **Action:** Verifier format MSISDN avec indicatif pays (+242...)
- **Sandbox test:** MSISDN `46733123455` simule PayerNotFound

### 6.3 Fonds insuffisants cote client MoMo
- **Symptome MTN:** `INTERNAL_PROCESSING_ERROR` (mapping generique)
- **Action:** Message UX "Verifiez votre solde MoMo et reessayez"
- **Transaction AfriWallet:** reste FAILED, wallet non credite

### 6.4 Timeout approbation (> 5 minutes)
- **Symptome MTN:** `COULD_NOT_PERFORM_TRANSACTION`
- **Action:** Nouvelle tentative avec nouveau `X-Reference-Id`
- **Sandbox test:** MSISDN `46733123463`

### 6.5 Callback manquant
- **Symptome:** Transaction bloquee en PENDING > 2 minutes
- **Action:** Polling GET status MTN
- **Cause racine frequente:** callback host mismatch (`500 INVALID_CALLBACK_URL_HOST`)

### 6.6 Duplicate referenceId
- **Symptome:** `409 RESOURCE_ALREADY_EXIST` ou Prisma P2002 sur providerTxId
- **Action:** Retourner resultat stocke, ne pas re-initier

### 6.7 mauvais X-Target-Environment
- **Symptome:** `500 NOT_ALLOWED_TARGET_ENVIRONMENT`
- **Congo prod:** utiliser `mtncongo`, pas `sandbox` ni `mtncameroon`

### 6.8 Devise incorrecte
- **Symptome:** `500 INVALID_CURRENCY`
- **Sandbox:** EUR obligatoire · **Prod Congo:** XAF

---

## 7. Idempotence multi-couche

1. **HTTP layer:** `X-Reference-Id` UUID v4 unique par tentative
2. **DB layer:** `Transaction.providerTxId @unique` = referenceId MTN
3. **Webhook layer:** `WebhookEvent.eventKey @unique` = `mtn:r2p:{referenceId}`

Si webhook duplique (P2002 sur eventKey): retourner `{ received: true }` sans double credit.

Si transaction deja SUCCESS/FAILED: ignorer callback, marquer webhook processedAt.

---

## 8. Journalisation support

Champs a remonter au support client:
- `referenceId` (providerTxId)
- `phoneNumber` (metadata)
- `amountFcfa` (BigInt -> Number en API)
- `providerStatus` brut dans metadata
- `eventKey` webhook
- `X-Target-Environment` utilise

---

## 9. Differences sandbox vs production Congo

| Parametre | Sandbox | Production Congo |
|-----------|---------|------------------|
| Base URL | sandbox.momodeveloper.mtn.com | momodeveloper.mtn.com |
| Target env | sandbox | mtncongo |
| Currency | EUR | XAF |
| MSISDN test | 467331234xx | MSISDN reel +242 |
| Provisioning | Sandbox Provisioning API | Partner Portal |

---

## 10. Anti-patterns LLM a eviter

- Traiter HTTP 202 comme SUCCESS -> double comptabilite ou fonds fantomes
- Crediter wallet avant callback/poll SUCCESSFUL
- Reutiliser X-Reference-Id sur retry -> 409
- Oublier KYC gate -> non-conformite COBAC
- Utiliser float pour FCFA -> perte precision BigInt
- Supposer sync type Stripe -> UX cassee en Afrique centrale
