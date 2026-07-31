# Scenarios de debug production — AfriWallet (FinTech Afrique)

> **Application:** AfriWallet · **Corpus entrainement:** MUNTU (voir `00-core-principles/muntu-engineering-identity.md`)

> **Couche:** `35-business-flows` · **Usage:** entrainement MoE troubleshooting + fine-tuning comportemental  
> **Stack:** NestJS · Prisma · PostgreSQL · MTN MoMo · Airtel Open API · Smile ID · Onafriq · Bridge  
> **Format:** symptome -> investigation -> cause racine -> remediation -> prevention

---

## Scenario 1 — Depot MoMo bloque en PENDING indefiniment

### Contexte incident
Un utilisateur camerounais (+237670000123) initie un depot de 15 000 FCFA via `POST /payments/deposit/momo`.
L'API retourne `{ "status": "PENDING", "referenceId": "a3f2c1b0-..." }`.
Apres 10 minutes, le solde wallet reste a 0. Le client insiste: "J'ai valide sur mon telephone MTN."

### Symptomes observes
- `Transaction.status = PENDING`, `type = CASH_IN_MOMO`
- `Transaction.providerTxId = referenceId` (UUID v4)
- Aucune ligne `WebhookEvent` avec `eventKey = mtn:r2p:{referenceId}`
- Polling `GET /payments/deposit/momo/{referenceId}/status` retourne `isFinal: false`

### Arbre de diagnostic

```
PENDING > 2 min ?
  |
  +-- WebhookEvent absent ?
  |     |
  |     +-- OUI -> callback jamais recu OU IP bloquee
  |     |         -> verifier MTN_MOMO_CALLBACK_BASE_URL (HTTPS public)
  |     |         -> verifier providerCallbackHost au provisioning API User
  |     |         -> INVALID_CALLBACK_URL_HOST si host mismatch
  |     |
  |     +-- NON -> webhook recu mais status non-final dans payload
  |               -> lire metadata transaction, providerStatus brut
  |
  +-- Polling MTN GET status ?
        |
        +-- 404 RESOURCE NOT FOUND -> POST initial n'a pas retourne 202
        +-- PENDING -> client n'a pas approuve USSD/App MoMo
        +-- SUCCESSFUL -> bug sync interne (webhook/poll handler)
```

### Causes racines frequentes (ordre de probabilite)

1. **Client n'a pas confirme** — RequestToPay exige approbation USSD/App dans les 5 minutes (`COULD_NOT_PERFORM_TRANSACTION` apres timeout).
2. **Callback URL inaccessible** — MTN envoie une seule fois, pas de retry. Firewall, certificat TLS invalide, ou host different du `providerCallbackHost`.
3. **Mauvais X-Target-Environment** — `sandbox` en prod ou `mtncameroon` au lieu de `mtncongo` pour le Congo.
4. **Devise incorrecte** — sandbox exige `EUR`, prod Congo `XAF`. Erreur `500 INVALID_CURRENCY`.
5. **KYC non VERIFIED** — bloque avant l'appel MTN (400), mais si bypass manuel en DB, MTN peut quand meme echouer.

### Investigation pas a pas (runbook support)

```bash
# 1. Verifier transaction en base
SELECT id, status, "providerTxId", amount_fcfa, metadata
FROM "Transaction"
WHERE "providerTxId" = 'a3f2c1b0-...';

# 2. Verifier webhook audit
SELECT "eventKey", "processedAt", error, payload
FROM "WebhookEvent"
WHERE "eventKey" = 'mtn:r2p:a3f2c1b0-...';

# 3. Poll MTN manuellement (Collection token)
curl -X GET "https://sandbox.momodeveloper.mtn.com/collection/v1_0/requesttopay/a3f2c1b0-..." \
  -H "Authorization: Bearer {token}" \
  -H "X-Target-Environment: sandbox" \
  -H "Ocp-Apim-Subscription-Key: {key}"
```

### Remediation
- Si MTN status = `SUCCESSFUL` et tx PENDING: declencher `syncMomoDepositStatus()` ou reprocesser webhook manuellement avec payload MTN.
- Si MTN status = `PENDING`: contacter client pour re-approuver ou re-initier avec nouveau `X-Reference-Id`.
- Si callback host mismatch: re-provisionner API User avec bon `providerCallbackHost`, redeployer listener HTTPS.

### Code de reference (sync fallback)

```typescript
// payments.service.ts — syncMomoDepositStatus()
if (providerStatus === 'SUCCESSFUL' || providerStatus === 'SUCCESS') {
  if (tx.status === TransactionStatus.PENDING) {
    await this.prisma.$transaction([
      this.prisma.wallet.update({
        where: { id: tx.walletId },
        data: { balanceFcfa: { increment: tx.amountFcfa } },
      }),
      this.prisma.transaction.update({
        where: { id: tx.id },
        data: { status: TransactionStatus.SUCCESS, metadata: normalized },
      }),
    ]);
  }
}
```

### Prevention
- Toujours implementer polling client-side en parallele du callback (intervalle 2s/10s/30s).
- Monitorer ratio `PENDING > 5 min` / total deposits.
- Alerting si `WebhookEvent` absent apres 120s post-initiation.

### MSISDN sandbox pour reproduction
| Scenario | MSISDN test |
|----------|-------------|
| PayerCouldNotPerformTransaction | 46733123463 |
| PayerNotFound | 46733123455 |
| PayerInternalProcessingError | 46733123461 |

---

## Scenario 2 — ESB000041 Duplicate External Transaction ID (Airtel)

### Contexte incident
Integrateur Airtel Congo tente un disbursement via `POST /standard/v3/disbursements`.
Headers: `X-Country: CG`, `X-Currency: XAF`, `Authorization: Bearer ...`
Reponse HTTP 200 avec body:
```json
{
  "status": {
    "success": false,
    "response_code": "ESB000041",
    "message": "Transaction with External Transaction ID already exists."
  }
}
```

### Interpretation metier
`transaction.id` (external transaction id cote partenaire) a deja ete utilise pour une requete precedente.
Airtel rejette la duplication — parallel exact de `409 RESOURCE_ALREADY_EXIST` cote MTN sur `X-Reference-Id`.

### Diagnostic
1. Chercher en base locale si `transaction.id` existe deja avec statut SUCCESS ou PENDING.
2. Si retry reseau (timeout HTTP 504): **ne pas regenerer le meme id** — faire transaction enquiry d'abord.
3. Verifier logs: double-click UI, retry automatique sans idempotency key, ou cron job duplique.

### Remediation
```typescript
// Pattern idempotent — avant POST Airtel
const externalId = idempotencyKey ?? `disb_${userId}_${Date.now()}`;
const existing = await prisma.transaction.findFirst({
  where: { idempotencyKey: externalId },
});
if (existing?.status === 'SUCCESS') {
  return mapStoredResult(existing); // pas de nouvel appel Airtel
}
// Sinon: nouveau UUID si echec confirme FAILED
```

### Enquiry obligatoire si ambigu
Codes associant etat ambigu: `0000900`, `ROUTER117`, `DP01000001000`, `DP02100001000`.
Toujours `GET /standard/v3/disbursements/{id}` ou `GET /standard/v1/payments/{id}` avant retry.

### Prevention
- `transaction.id` = UUID v4 ou `{prefix}_{cuid}_{timestamp}` jamais reutilise.
- Stocker mapping externalId -> reference_id Airtel des la premiere reponse.
- Idempotency-Key header cote API gateway interne.

---

## Scenario 3 — Cash-out MoMo FAILED sans compensation wallet

### Contexte incident (CRITIQUE — perte confiance client)
Utilisateur retire 50 000 FCFA. Solde passe de 100 000 a 50 000 immediatement (reservation).
MTN Disbursement echoue (`FAILED`). Solde reste a 50 000 au lieu de revenir a 100 000.

### Cause racine typique
- Webhook MTN recu avec `FAILED` mais handler n'a pas execute la branche compensation `CASH_OUT_MOMO`.
- Bug: handler traite uniquement `CASH_IN_MOMO` sur FAILED (pas de debit a annuler) mais oublie increment sur cash-out.
- Transaction deja marquee FAILED par polling avant webhook — race condition mal geree.

### Code canonique compensation

```typescript
// webhooks.service.ts — handleMtnRequestToPayCallback()
if (providerStatus === 'FAILED' || providerStatus === 'REJECTED') {
  if (tx.type === TransactionType.CASH_OUT_MOMO) {
    await this.prisma.$transaction([
      this.prisma.wallet.update({
        where: { id: tx.walletId },
        data: { balanceFcfa: { increment: tx.amountFcfa } },
      }),
      this.prisma.transaction.update({
        where: { id: tx.id },
        data: { status: FAILED, failureReason: reason, metadata: payload },
      }),
    ]);
  }
}
```

### Verification post-incident
```sql
SELECT t.id, t.status, t.amount_fcfa, w."balanceFcfa"
FROM "Transaction" t
JOIN "Wallet" w ON w.id = t."walletId"
WHERE t.type = 'CASH_OUT_MOMO'
  AND t.status = 'FAILED'
  AND t."createdAt" > NOW() - INTERVAL '24 hours';
-- Pour chaque FAILED cash-out: verifier que solde client = solde_avant_initiation
```

### Remediation manuelle ops
```typescript
await prisma.$transaction([
  prisma.wallet.update({ where: { id: walletId }, data: { balanceFcfa: { increment: 50000n } } }),
  prisma.transaction.update({ where: { id: txId }, data: { metadata: { manualCompensation: true } } }),
]);
// + ticket support + audit log
```

### Prevention
- Test E2E obligatoire: MSISDN sandbox `46733123450` (PayeeFailed) -> assert balance restored.
- Monitor: `CASH_OUT_MOMO FAILED` sans increment wallet dans la meme seconde = alerte P1.

---

## Scenario 4 — ROUTER001 Wallet not configured (Airtel UAT)

### Symptome
Appel `POST /auth/oauth2/token` reussit. Premier appel metier retourne:
```json
{ "response_code": "ROUTER001", "message": "Wallet is not configured" }
```

### Cause
Le portail developpeur Airtel (`openapiuat.airtel.cg`) n'a pas de **Application Wallet** configure pour le produit souscrit (Collection, Disbursement, etc.).

### Remediation
1. Se connecter au dashboard Airtel Africa Developer Portal.
2. Application Settings -> activer/configure wallet pour le produit (staging).
3. Verifier souscription produit approuvee (Merchant Collection, Disbursement v3, etc.).
4. Regenerer credentials si migration sandbox -> prod.

### Distinction ROUTER001 vs ROUTER007
| Code | Signification |
|------|---------------|
| ROUTER001 | Wallet application non configure cote Airtel |
| ROUTER007 | Compte developpeur non autorise pour le pays (CG) |
| ROUTER005 | Route pays non configuree — contacter support Airtel |

---

## Scenario 5 — Remboursement Airtel TR + DP03520001001

### Contexte
Appel `POST /imt/v1/refund` avec headers `x-country: CG`, `x-currency: XAF`.
Reponse succes:
```json
{
  "data": {
    "transaction": {
      "status": "TR",
      "message": "Transaction Reversed",
      "airtel_money_id": "REMX-ASBDGHKL-1754303725"
    }
  },
  "status": {
    "response_code": "DP03520001001",
    "success": true
  }
}
```

### Interpretation pour le modele
- `TR` = Transaction Reversed (renversement confirme).
- `DP03520001001` = code produit succes remittance refund — **ne pas confondre avec une erreur**.
- Le LLM doit mapper: HTTP 200 + success true + status TR = remboursement complete.

### Handler interne recommande (futur airtel.service.ts)
```typescript
if (payload.data?.transaction?.status === 'TR') {
  await finalizeRefund(txId, {
    providerCode: 'DP03520001001',
    airtelMoneyId: payload.data.transaction.airtel_money_id,
  });
}
```

---

## Scenario 6 — INVALID_CALLBACK_URL_HOST (MTN)

### Symptome
`POST /collection/v1_0/requesttopay` retourne `500` avec:
`INVALID_CALLBACK_URL_HOST — Callback URL with different host name to configured for API User`

### Cause
Header `X-Callback-Url: https://api.monapp.com/webhooks/mtn/...` mais `providerCallbackHost` enregistre = `webhooks.monapp.com` ou `monapp.com`.

### Regles MTN
- Host callback URL **doit matcher** host configure au provisioning API User.
- Utiliser **hostname**, jamais IP publique.
- HTTPS obligatoire sandbox et production.

### Fix
```http
POST /apiuser HTTP/1.1
{"providerCallbackHost": "api.monapp.com"}

X-Callback-Url: https://api.monapp.com/webhooks/mtn/requesttopay/{referenceId}
```

Sandbox test MSISDN: `46733123459` simule InvalidCallbackUrlHost.

---

## Scenario 7 — KYC bloque PENDING apres webhook Smile ID

### Symptome
Utilisateur complete biometric KYC Nigeria NIN_V2. `kycStatus` reste `PENDING`.
`WebhookEvent` existe avec `provider = SMILE_ID` et `processedAt` null ou `error` renseigne.

### Diagnostic
1. Verifier signature HMAC + timestamp +/- 5 min (`ForbiddenException: Expired signature`).
2. Verifier `job_success` dans payload: true -> VERIFIED, false -> REJECTED.
3. Verifier `result.PartnerParams.user_id` present — sans user_id: audit only, pas de mutation.
4. Verifier idempotence: KYC deja VERIFIED -> webhook ignore (comportement normal).

### Cas edge: job_id duplique
Smile error `2215` = job_id deja existant. Solution: nouveau jobId ou `retry: true`.

### Code reference

```typescript
// webhooks.service.ts — handleSmileIdWebhook()
if (body.job_success === true) {
  await this.kycService.markKycVerified(userId, user.kycReference);
} else {
  await this.kycService.markKycRejected(userId, user.kycReference);
}
```

### Distinction KYC vs SmartSelfie
SmartSelfie met a jour `smartSelfieLastAuthSuccess` — **ne modifie pas** `kycStatus`.
Confusion frequente en support L1.

---

## Scenario 8 — Depot Bridge RJCT (rejet banque)

### Contexte
`POST /payments/deposit/bridge` -> `paymentRequestId` + URL banque Demo.
Webhook `POST /webhooks/bridge/payments`:
```json
{
  "type": "payment.transaction.updated",
  "content": {
    "payment_request_id": "pr_abc123",
    "status": "RJCT",
    "status_reason": "INSUFFICIENT_FUNDS"
  }
}
```

### Comportement attendu AfriWallet
- Transaction reste ou passe a `FAILED`.
- **Pas de credit wallet** (contrairement a ACSC = SUCCESS).
- `failureReason` = status_reason du payload.

### Verification signature
Header `bridgeapi-signature` HMAC-SHA256 sur **raw body** (pas JSON re-serialise).
NestJS requiert middleware `rawBody` sur route webhook.

### Statuts Bridge normalises
| Bridge | AfriWallet |
|--------|------------|
| ACSC | SUCCESS (+ credit wallet) |
| RJCT | FAILED |
| PDNG | PENDING |

---

## Scenario 9 — NOT_ALLOWED_TARGET_ENVIRONMENT (Congo vs Cameroun)

### Symptome
Integrateur au Congo Brazzaville utilise credentials MTN avec:
`X-Target-Environment: mtncameroon`
Erreur: `500 NOT_ALLOWED_TARGET_ENVIRONMENT`

### Matrice OpCo correcte
| Pays deployment | Header value |
|-----------------|--------------|
| Congo (CG) | `mtncongo` |
| Cameroun (CM) | `mtncameroon` |
| Nigeria (NG) | `mtnnigeria` |
| Sandbox tests | `sandbox` |

### Variable env AfriWallet
```env
MTN_MOMO_TARGET_ENVIRONMENT=mtncongo   # prod Congo
MTN_MOMO_CURRENCY=XAF
```

Sandbox:
```env
MTN_MOMO_TARGET_ENVIRONMENT=sandbox
MTN_MOMO_CURRENCY=EUR
```

MSISDN test: `46733123458` = NotAllowedTargetEnvironment.

---

## Scenario 10 — OTP spam / code expose en production

### Symptome securite
Reponse API contient `{ "otp": "482917" }` en production. Ou: 50 SMS/min vers meme numero.

### Cause
- `NODE_ENV !== 'production'` par erreur sur serveur prod.
- `SmsService.isConfigured()` false -> pas d'exception en prod si bug deploy.
- Attaquant brute-force `/auth/otp/request`.

### Comportement correct (auth.service.ts)

```typescript
const isProd = process.env.NODE_ENV === 'production';
if (isProd && !this.sms.isConfigured()) {
  throw new InternalServerErrorException('SMS provider is required in production');
}
return isProd ? { phoneNumber, sent: true } : { phoneNumber, otp: code };
```

### Rate limits
- Cooldown 60s entre demandes OTP meme MSISDN.
- Max 5/heure, 10/jour.
- Max 3 tentatives saisie par code OTP.
- Throttle NestJS: 5 req/min/IP sur routes OTP.

### Remediation incident
- Rotater secrets Twilio si fuite OTP logs.
- Purger `OtpRequest` table pour numero cible.
- Activer WAF rate limit sur `/auth/otp/*`.

---

## Scenario 11 — Carte Onafriq geles (cardStatus IA/LC)

### Contexte webhook
```json
{
  "notificationType": "cardStatusChange",
  "customerId": "987654321",
  "cardStatus": "LC",
  "lastFourDigits": "4521"
}
```

### Mapping freeze
Statuts declenchant `isFrozen = true`: `IA`, `LC`, `SC`, `DEACTIVATED`, `EX`, `INACTIVE`, `LOSTORSTOLEN`.
Statut `AC` (Active) -> `isFrozen = false`.

### Idempotence
`eventKey = onafriq:{notificationType}:{requestId}:{transactionId|customerId}`

### Signature
Header `x-webhook-signature` — AES256 decrypt doit egaler `ONAFRIQ_WEBHOOK_SECRET`.

---

## Scenario 12 — Etat ambigu Airtel TA / TIP / 0000900

### Symptome
Cash-In ou B2W retourne status `TIP` (Transaction in Progress) ou `TA` (Transaction Ambiguous).
Code ESB: `0000900` — "Transaction might be in ambiguous state."

### Regle absolue
**Ne jamais crediter ou debiter le wallet client sur TIP/TA.**
Attendre statut final TS ou TF via transaction enquiry.

### Enquiry endpoints
- `GET /standard/v1/payments/{id}` — Cash-In
- `GET /bank-to-wallet/v1/payments/{id}` — B2W
- Attendre >= 1 minute apres POST payment (doc Airtel)

### Mapping statuts Airtel
| Status | Action |
|--------|--------|
| TS | Final success — crediter si cash-in |
| TF | Final failed — ne pas crediter |
| TIP | Poll — pas d'action |
| TA | Poll — pas d'action |
| TR | Reversed — traiter remboursement |

### airtel_money_id
Genere **uniquement** si status = TS (ou TR pour refund). Absent sur TIP/TF — normal.

---

## Scenario 13 — 409 RESOURCE_ALREADY_EXIST (MTN X-Reference-Id)

### Symptome
Retry automatique apres timeout HTTP reutilise le meme `X-Reference-Id`.
MTN retourne `409 RESOURCE_ALREADY_EXIST`.

### Remediation
- Si original a recu 202: poll GET status avec **meme** referenceId — ne pas regenerer.
- Si original inconnu: generer nouveau UUID v4 et nouvelle tentative.

### Code MTN (initiateDebit)

```typescript
const referenceId = randomUUID(); // toujours nouveau par tentative metier
// Stocker referenceId en DB AVANT appel MTN si possible (outbox pattern)
```

---

## Scenario 14 — Fonds insuffisants masques par INTERNAL_PROCESSING_ERROR

### Symptome MTN
Callback ou poll retourne reason `INTERNAL_PROCESSING_ERROR` sans detail.

### Interpretation
MTN utilise ce code generique pour:
- Fonds insuffisants payer (cash-in)
- Fonds insuffisants payee (cash-out)
- Wallet plateforme indisponible

### UX recommande
Message client: "Verifiez votre solde MoMo et reessayez."
Ne pas exposer le code brut MTN en UI.

### Sandbox
`46733123455` TransferPayeeNotEnoughFunds simule ce cas.

---

## Scenario 15 — BigInt precision — montant affiche incorrect

### Symptome
Wallet affiche 9999999999999000 au lieu de 10000000000000000 FCFA.

### Cause
Conversion prematuree BigInt -> Number JavaScript (> 2^53 perd precision).
Ou division par 100 erronee (FCFA deja en unites entieres, pas centimes).

### Fix

```typescript
// CORRECT
return { balanceFcfa: Number(wallet.balanceFcfa) };

// INCORRECT — jamais
return { balanceFcfa: wallet.balanceFcfa / 100n };
return { balanceFcfa: parseFloat(wallet.balanceFcfa.toString()) };
```

### Prisma schema
```prisma
balanceFcfa BigInt @default(0)  // entiers FCFA uniquement
```

---

## Matrice rapide cross-provider — "Que faire en premier ?"

| Signal | MTN | Airtel | Action immediate |
|--------|-----|--------|------------------|
| HTTP 202 | Requete acceptee, PENDING | N/A (sync 200) | Attendre callback/poll |
| Duplicate ID | 409 RESOURCE_ALREADY_EXIST | ESB000041 | Enquiry, pas retry aveugle |
| Timeout | COULD_NOT_PERFORM_TRANSACTION | ROUTER117 / 504 | Transaction enquiry |
| Ambiguous | PENDING long | TA / TIP / 0000900 | Poll, ne pas finaliser |
| Wrong country | NOT_ALLOWED_TARGET_ENVIRONMENT | ROUTER006/007 | Fix header/env OpCo |
| Callback issue | INVALID_CALLBACK_URL_HOST | N/A | Fix providerCallbackHost |
| Cash-out fail | FAILED + compensation | N/A MTN | Verify wallet increment |

---

## Prompt systeme recommande pour le modele MUNTU (debug mode)

Quand un developpeur decrit un incident fintech Afrique:
1. Identifier le provider (MTN / Airtel / Smile / Onafriq / Bridge).
2. Demander `referenceId`, `providerTxId`, `eventKey`, statut DB.
3. Distinguer async (MoMo 202) vs sync (Airtel 200).
4. Proposer enquiry avant retry si idempotence en jeu.
5. Verifier compensation cash-out sur tout FAILED disbursement.
6. Citer codes erreur exacts (ROUTER001, ESB000041, DP03520001001+TR).
7. Ne jamais recommander credit wallet sur TIP/TA/PENDING sans statut final.

---

## Voir aussi (corpus normalise)

- **Schema annotation :** `corpus-annotation-schema.md`
- **Exemples officiels annotés :** `annotated-provider-examples-normalized.md`
- **Matrice erreurs officielle :** `30-system-integrations/provider-official-error-matrix-normalized.md`
- **Docs brutes :** `30-system-integrations/source-docs/momo-api-documentation.txt`, `airtel-api-documentation.txt`
