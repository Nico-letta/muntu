# Q&A Debug Approfondi — Entrainement fine-tuning (modele MUNTU)

> **Application decrite:** AfriWallet · **Identite modele:** MUNTU — voir `00-core-principles/muntu-engineering-identity.md`

> **Couche:** `35-business-flows` · **Format:** question developpeur -> reponse expert avec code  
> **Objectif:** ancrages anti-overfitting sur patterns async Afrique

---

## Q1. Mon RequestToPay MTN retourne 202 mais le wallet ne credite jamais. Par ou commencer ?

**Reponse expert:**

HTTP `202 Accepted` sur `POST /collection/v1_0/requesttopay` signifie uniquement que MTN a valide syntactiquement la requete et l'a mise en file. Ce n'est **pas** un succes financier.

Checklist ordonnee:

1. **Confirmer KYC** — `user.kycStatus === VERIFIED` avant l'appel (sinon rejet amont).
2. **Verifier transaction DB** — `CASH_IN_MOMO`, `PENDING`, `providerTxId = X-Reference-Id`.
3. **Chercher webhook** — `WebhookEvent.eventKey = mtn:r2p:{referenceId}`. Absent apres 2 min = probleme callback ou client n'a pas approuve.
4. **Poll MTN** — `GET /collection/v1_0/requesttopay/{referenceId}`. Si `SUCCESSFUL`, appeler `syncMomoDepositStatus()`.
5. **Verifier env** — sandbox + EUR vs prod `mtncongo` + XAF.

Le client **doit** approuver sur USSD/App MoMo dans les 5 minutes. Sinon: `COULD_NOT_PERFORM_TRANSACTION`.

Code polling AfriWallet:
```typescript
private getNextPollInMs(providerStatus: string): number {
  if (['CREA', 'ACTC'].includes(s)) return 2000;
  if (['PDNG', 'PENDING', 'UNKNOWN'].includes(s)) return 10000;
  return 30000;
}
```

---

## Q2. Difference entre ESB000041 Airtel et 409 RESOURCE_ALREADY_EXIST MTN ?

**Reponse expert:**

Les deux signalent une **violations d'idempotence** — reutilisation d'un identifiant de transaction deja consomme.

| | MTN MoMo | Airtel Money |
|---|----------|--------------|
| Code | `409 RESOURCE_ALREADY_EXIST` | `ESB000041` |
| Champ | `X-Reference-Id` (header UUID) | `transaction.id` (body) |
| Action | Poll GET avec meme ID si 202 recu | `GET /payments/{id}` enquiry |

**Erreur fatale:** regenerer un nouvel ID et re-debiter le client sans verifier l'etat de la premiere tentative.

Pattern correct:
```typescript
catch (err) {
  if (err.code === 'P2002') return storedResult; // Prisma unique providerTxId
}
```

---

## Q3. Un retrait MoMo a echoue mais l'argent a disparu du wallet. Bug ou feature ?

**Reponse expert:**

C'est un **bug P0** si le statut final est `FAILED`/`REJECTED` sans recredit.

Design intentionnel AfriWallet:
- **Initiation:** `wallet.balanceFcfa -= amount` (reservation immediate)
- **Succes MTN:** statut SUCCESS, pas de mouvement supplementaire
- **Echec MTN:** `wallet.balanceFcfa += amount` (compensation)

Verifier `webhooks.service.ts` branche `CASH_OUT_MOMO` + `FAILED`.

Si webhook manquant mais poll detecte FAILED: `syncMomoWithdrawStatus()` doit aussi compenser.

Test sandbox: MSISDN `46733123450` (TransferPayeeFailed).

---

## Q4. Que signifie DP03520001001 avec status TR sur un refund Airtel ?

**Reponse expert:**

C'est un **succes de renversement**, pas une erreur.

```json
{
  "data": { "transaction": { "status": "TR", "message": "Transaction Reversed" } },
  "status": { "response_code": "DP03520001001", "success": true }
}
```

- `TR` = Transaction Reversed
- `DP03520001001` = code produit remittance refund success
- Action: marquer remboursement complete en base, notifier partenaire

Le modele ne doit pas suggerer un retry sur ce pattern.

---

## Q5. ROUTER001 vs ROUTER119 — comment les distinguer rapidement ?

**Reponse expert:**

| Code | Message type | Fix |
|------|--------------|-----|
| `ROUTER001` | Wallet application not configured | Dashboard Airtel -> config wallet produit |
| `ROUTER119` | Invalid/Missing Currency | Ajouter header `X-Currency: XAF` ou `x-currency: XAF` |
| `ROUTER006` | Invalid Country | `X-Country: CG` pour Congo-Brazzaville |
| `ROUTER115` | Incorrect Pin | PIN clair incorrect cote utilisateur |
| `ROUTER116` | Incorrect Encrypted Pin | Revoir chiffrement RSA OAEP 2048 |

ROUTER001 = probleme **provisioning portail Airtel**.
ROUTER119 = probleme **headers HTTP** sur la requete courante.

---

## Q6. Pourquoi mon callback MTN n'arrive jamais ?

**Reponse expert:**

MTN n'envoie le callback **qu'une seule fois**, sans retry.

Causes top 5:
1. `providerCallbackHost` != host de `X-Callback-Url`
2. Certificat TLS non approuve (CA intermediaire)
3. Firewall bloque IP MTN
4. Endpoint n'accepte pas PUT (MTN peut utiliser PUT ou POST)
5. HTTP au lieu de HTTPS (interdit sandbox/prod)

Config provisioning:
```json
{ "providerCallbackHost": "api.tondomaine.com" }
```

Callback URL:
```
https://api.tondomaine.com/webhooks/mtn/requesttopay/{referenceId}
```

Fallback obligatoire: polling GET status.

IP allowlist optionnelle: `MTN_MOMO_WEBHOOK_IP_ALLOWLIST=1.2.3.4,5.6.7.8`

---

## Q7. KYC VERIFIED mais SmartSelfie echoue — l'utilisateur peut-il payer ?

**Reponse expert:**

**Oui** pour les paiements standard. SmartSelfie est **decouple** du KYC legal.

| | KYC legal | SmartSelfie |
|---|-----------|-------------|
| Champ DB | `kycStatus` | `smartSelfieLastAuthSuccess` |
| Requis pour MoMo | OUI (VERIFIED) | NON (sauf policy interne large_withdrawal) |
| Job Smile | type 1 ou 11 | type 2 ou 4 |

SmartSelfie reasons: `large_withdrawal`, `pin_reset`, `high_risk_device`, `wallet_recovery`.

Un echec SmartSelfie ne doit pas remettre `kycStatus` a PENDING.

---

## Q8. Comment debugger un statut TA (Transaction Ambiguous) Airtel ?

**Reponse expert:**

`TA` et `TIP` sont des etats **non-finaux**. Interdiction de crediter/debiter.

Procedure:
1. Attendre minimum 60 secondes apres POST (doc Airtel payment API).
2. Appeler transaction enquiry: `GET /standard/v1/payments/{externalId}`.
3. Si toujours TA/TIP apres 5 min: escalade support Airtel avec `transaction.id` + `reference_id`.
4. Code ESB `0000900` confirme ambiguite — meme procedure.

Cash-In codes DP01:
- `DP01000001000` = Ambiguous -> enquiry
- `DP01000001001` = Success -> final
- `DP01000001005` = Failed -> final

Ne jamais traiter TA comme SUCCESS par defaut.

---

## Q9. Quel OpCo MTN pour Brazzaville vs Douala ?

**Reponse expert:**

Ne pas confondre geographie politique et OpCo MTN:

- **Congo-Brazzaville (CG):** `X-Target-Environment: mtncongo`, devise `XAF`
- **Cameroun (CM):** `X-Target-Environment: mtncameroon`, devise `XAF`
- **Sandbox global:** `sandbox`, devise souvent `EUR`

AfriWallet `.env` prod Congo:
```env
MTN_MOMO_TARGET_ENVIRONMENT=mtncongo
MTN_MOMO_CURRENCY=XAF
```

Erreur si inverse: `500 NOT_ALLOWED_TARGET_ENVIRONMENT`.

Airtel Congo headers:
```http
X-Country: CG
X-Currency: XAF
```

---

## Q10. Webhook Smile ID recu 3 fois — risque triple VERIFIED ?

**Reponse expert:**

Non, si idempotence correcte.

```typescript
const eventKey = jobId ?? `smile:${userId}:${timestamp}:${signature}`;
await prisma.webhookEvent.create({ data: { eventKey, ... } });
// P2002 duplicate -> return { received: true }

if (user.kycStatus === 'VERIFIED' || user.kycStatus === 'REJECTED') {
  return { received: true }; // deja final
}
```

Triple delivery est normal (retry reseau partenaire). La table `WebhookEvent` est le garde-fou.

Verifier aussi anti-replay timestamp +/- 5 minutes sur signature HMAC.

---

## Q11. Bridge deposit ACSC vs RJCT — impact wallet ?

**Reponse expert:**

| Status Bridge | Transaction AfriWallet | Wallet |
|---------------|------------------------|--------|
| ACSC | SUCCESS | +amountFcfa |
| RJCT | FAILED | aucun credit |
| PDNG | PENDING | aucun mouvement |

Webhook `bridgeapi-signature` sur raw body. Transaction type `ADJUSTMENT`, provider `BRIDGE`.

Polling: `GET /payments/deposit/bridge/{paymentRequestId}/status`.

Sandbox: Demo Bank provider_id 574, currency EUR.

---

## Q12. Pourquoi Prisma BigInt et pas Decimal pour le FCFA ?

**Reponse expert:**

FCFA CEMAC/UEMOA s'utilise en **unites entieres** (pas de centimes au quotidien). BigInt evite:
- Erreurs float (`0.1 + 0.2 !== 0.3`)
- Perte precision au-dela de `Number.MAX_SAFE_INTEGER` (2^53-1)

```prisma
balanceFcfa BigInt @default(0)
amountFcfa  BigInt
```

Frontiere API JSON:
```typescript
balanceFcfa: Number(wallet.balanceFcfa) // OK pour montants wallet < 2^53
```

Jamais `amountFcfa / 100` — le FCFA n'est pas structure comme EUR cents.

---

## Q13. Comment tester tous les echecs MTN sans prod ?

**Reponse expert:**

Sandbox MSISDN magiques (extrait):

| Use case | MSISDN |
|----------|--------|
| RequestToPayPayerRejected | 46733123451 |
| RequestToPayPayerNotFound | 46733123455 |
| RequestToPayPayerInvalidCurrency | 46733123460 |
| RequestToPayPayerCouldNotPerformTransaction | 46733123463 |
| TransferPayeeNotEnoughFunds | 46733123455 |
| TransferPayeeNotFound | 46733123457 |

Payment amounts (Aggregator):
| Amount | Result |
|--------|--------|
| 1000 | Success |
| 2000 | Failed |
| 3000 | Pending then Success |

Provisioning sandbox obligatoire — comptes Partner GUI prod **incompatibles** sandbox.

---

## Q14. Airtel disbursement v3 exige x-signature et x-key — ou ca casse ?

**Reponse expert:**

Disbursement API v3 et ATM Withdrawal v2 utilisent **message signing**:
- `x-signature`: payload chiffre
- `x-key`: paire AES key:iv chiffree RSA

Sans ces headers: rejet ou `ROUTER003` Missing params.

PIN dans body toujours chiffre RSA 2048 OAEP SHA-256.

OAuth2 prealable:
```http
POST /auth/oauth2/token
{ "client_id", "client_secret", "grant_type": "client_credentials" }
```

Token TTL ~180 secondes — refresh proactif.

---

## Q15. Quelle est la surface webhook publique complete AfriWallet ?

**Reponse expert:**

| Route | Provider | Methode | Securite |
|-------|----------|---------|----------|
| `/webhooks/mtn/requesttopay/:referenceId` | MTN | POST + PUT | IP allowlist optionnelle |
| `/webhooks/smile-id` | Smile ID | POST | HMAC + timestamp +/-5min |
| `/webhooks/onafriq/cards` | Onafriq | POST | x-webhook-signature AES256 |
| `/webhooks/bridge/payments` | Bridge | POST | bridgeapi-signature HMAC raw body |

Throttling: MTN 300/min, Onafriq 120/min, Bridge 180/min.

Tous: idempotence via `WebhookEvent.eventKey` unique.

---

## Q16. Le modele recommande Stripe sync pour MoMo — comment corriger ?

**Reponse expert:**

Education pattern Afrique:

**Stripe (sync occidental):**
```
POST /charge -> 200 SUCCESS ou 402 DECLINED -> etat final immediat
```

**MTN MoMo (async africain):**
```
POST /requesttopay -> 202 PENDING -> client USSD -> callback SUCCESSFUL/FAILED
```

Implications architecture:
- UI: spinner "Confirmez sur votre telephone" (pas success immediate)
- Backend: jamais crediter sur 202
- Idempotence: referenceId + eventKey webhook
- Compensation: cash-out FAILED recredit obligatoire
- Polling: fallback si callback unique MTN manque

C'est la **souverainete contextuelle** que MUNTU doit internaliser.

---

## Q17. Congo CG — Airtel actif dans AfriWallet ?

**Reponse expert:**

**Non.** Etat actuel codebase AfriWallet:

```prisma
enum PaymentProvider {
  MTN_MOMO   // deploye — src/providers/mtn.service.ts
  AIRTEL     // schema_only — PAS de service
  ...
}
enum TransactionType {
  CASH_IN_AIRTEL // schema_only
}
```

Specs Airtel dans `90-codebase-constraints/airtel-money-specs-draft.md` (negative knowledge + prep integration).

Le modele doit **ne pas** generer `src/providers/airtel.service.ts` comme existant — c'est roadmap.

Headers a preparer pour future integration: `X-Country: CG`, `X-Currency: XAF`, OAuth2 bearer.

---

## Q18. Comment correler un ticket support avec les logs ?

**Reponse expert:**

Minimum viable correlation set:

```json
{
  "request_id": "uuid interne gateway",
  "X-Reference-Id": "uuid MTN",
  "providerTxId": "identique referenceId MoMo",
  "transaction.id": "external id Airtel",
  "eventKey": "mtn:r2p:... | smile:... | onafriq:... | bridge:...",
  "airtel_money_id": "present si TS Airtel",
  "response_code": "DP03520001001 | ESB000041 | ROUTER001",
  "route_country": "CG | CM | NG",
  "integration_stage": "sandbox | production"
}
```

Requete SQL support type:
```sql
SELECT t.*, w."balanceFcfa", u."phoneNumber", u."kycStatus"
FROM "Transaction" t
JOIN "Wallet" w ON w.id = t."walletId"
JOIN "User" u ON u.id = w."userId"
WHERE t."providerTxId" = $1;
```

---

## Q19. OTP expire en 410 Gone — UX ou bug ?

**Reponse expert:**

**Feature securite**, pas bug. `auth.service.ts`:

```typescript
if (otpRecord.expiresAt < new Date()) {
  await prisma.otpRequest.deleteMany({ where: { phoneNumber } });
  throw new HttpException('Le code OTP a expire...', HttpStatus.GONE); // 410
}
```

410 = "existait mais plus valide" (distinct de 401/404).

TTL defaut: 5 minutes (`OTP_TTL_MINUTES`).

UX: proposer "Renvoyer un code" (respecter cooldown 60s).

---

## Q20. Checklist pre-production integrateur MoMo + Airtel Congo

**Reponse expert:**

**MTN MoMo:**
- [ ] Subscription keys Collection + Disbursement separees
- [ ] API User + Key provisionnes (sandbox puis Partner Portal prod)
- [ ] `providerCallbackHost` = domaine prod HTTPS
- [ ] Listener accepte PUT + POST
- [ ] `MTN_MOMO_TARGET_ENVIRONMENT=mtncongo`
- [ ] `MTN_MOMO_CURRENCY=XAF`
- [ ] IP publique whitelist Disbursement
- [ ] Polling fallback deploye
- [ ] Compensation cash-out testee

**Airtel (preparation):**
- [ ] Compte openapiuat.airtel.cg + prod openapi.airtel.cg
- [ ] OAuth2 client_id/secret
- [ ] Wallet produit configure (eviter ROUTER001)
- [ ] RSA PIN encryption 2048
- [ ] Headers CG/XAF systematiques
- [ ] Transaction enquiry sur TA/TIP/0000900
- [ ] Mapping TR + DP03520001001

**Commun AfriWallet:**
- [ ] KYC gate avant tout mouvement
- [ ] BigInt FCFA partout
- [ ] WebhookEvent idempotence
- [ ] SMS OTP prod sans fuite code API
