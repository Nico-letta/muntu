# Parcours complet — Numero de telephone au premier depot MoMo

> **Couche:** `35-business-flows` · **Duree typique:** 5-15 minutes (hors delai KYC Smile ID)  
> **Marche cible:** Afrique centrale / AfriWallet stack

---

## Etape 0 — Contexte produit

AfriWallet est MSISDN-first: le numero de telephone EST l'identifiant principal.
Pas d'email obligatoire. Pas de mot de passe — OTP SMS + PIN numerique bcrypt.

Monnaie wallet: FCFA entiers (BigInt), currency par defaut XAF.

---

## Etape 1 — Demande OTP (nouveau utilisateur)

**Endpoint:** `POST /auth/otp/request`

**Body:** `{ "phoneNumber": "+242051234567" }`

**Validations serveur:**
- phoneNumber requis
- Utilisateur existant -> `403 Ce numero est deja active`
- Cooldown 60s entre demandes
- Max 5 OTP/heure, 10 OTP/jour par numero

**Emission OTP:**
```typescript
const code = (Math.floor(100000 + Math.random() * 900000)).toString();
await prisma.otpRequest.create({ phoneNumber, code, expiresAt: now + 5min });
await sms.sendSms({ to: phoneNumber, body: `Votre code AfriWallet est: ${code}` });
return isProd ? { sent: true } : { otp: code }; // dev only
```

**Production:** code JAMAIS dans la reponse HTTP — Twilio SMS obligatoire.

---

## Etape 2 — Verification OTP + creation PIN

**Endpoint:** `POST /auth/otp/verify`

**Body:** `{ "phoneNumber", "otp", "pin" }`

**Validations:**
- OTP expire -> `410 Gone`
- OTP incorrect -> increment attempts, max 3 -> `403 bloque`
- OTP valide -> bcrypt pin, create User + Wallet(balance=0)

**Reponse:**
```json
{
  "id": "cuid...",
  "phoneNumber": "+242051234567",
  "wallets": [{ "id": "...", "balanceFcfa": 0 }],
  "accessToken": "jwt..."
}
```

JWT payload: `{ sub: userId, phoneNumber }`, TTL ~15 minutes.

---

## Etape 3 — Demarrage KYC legal

**Endpoint:** `POST /kyc/start` (JWT requis)

**Effet:** `kycStatus = PENDING`, `kycReference = kyc_{userId}_{timestamp}`

Sans KYC VERIFIED: **aucun** mouvement d'argent (deposit, withdraw, carte).

---

## Etape 4 — KYC biométrique (exemple Nigeria NIN_V2)

**Endpoints:**
1. `POST /kyc/biometric/upload-url` — URL S3 pre-signee + jobId
2. Upload ZIP: info.json + selfie (type 0) + 8 liveness (type 4)
3. `POST /kyc/biometric/upload-zip`

**Validation ID (smile-id-id-rules.ts):**
```typescript
NG/NIN_V2: regex /^\d{11}$/
```

**Webhook Smile ID:** `POST /webhooks/smile-id`
- Signature HMAC + timestamp +/- 5 min
- `job_success: true` -> kycStatus VERIFIED
- `job_success: false` -> kycStatus REJECTED
- eventKey = job_id (idempotent)

---

## Etape 5 — KYC document Congo (alternative CG)

Congo (CG) n'est PAS dans le biometric registry Smile ID.
Flux document job_type 11 uniquement:
- Types: IDENTITY_CARD, PASSPORT, DRIVERS_LICENSE, etc.
- `POST /kyc/document-verification/upload-url`
- ZIP avec id_front (type 1) + id_back (type 5) + selfie

---

## Etape 6 — Premier depot MoMo (cash-in)

**Precondition:** `kycStatus === VERIFIED`

**Endpoint:** `POST /payments/deposit/momo`

**Body:** `{ "phoneNumber": "+242051234567", "amountFcfa": 5000 }`

**Backend:**
1. MTN RequestToPay -> referenceId UUID
2. Transaction CASH_IN_MOMO PENDING
3. Client confirme sur telephone MTN
4. Webhook SUCCESS -> wallet += 5000 FCFA

**Polling fallback:** `GET /payments/deposit/momo/{referenceId}/status`

---

## Etape 7 — Consultation solde

**Endpoint:** `GET /wallets/me` (JWT)

**Reponse:**
```json
{ "balanceFcfa": 5000, "transactions": [...] }
```

BigInt converti en Number pour JSON — jamais de division par 100.

---

## Etape 8 (optionnel) — Carte virtuelle Onafriq

**Preconditions:** KYC VERIFIED + solde >= amountFcfa

**Endpoint:** `POST /virtual-cards`

**Flux:**
1. OAuth2 Onafriq client_credentials
2. POST /rest/api/v1/accounts/personalized (defaults CM, XAF, Douala)
3. Wallet decrement + VirtualCard create + Transaction CARD_ISSUANCE_FEE SUCCESS
4. Webhooks Onafriq pour freeze/unfreeze (cardStatus IA/LC/SC -> isFrozen=true)

---

## Etape 9 (optionnel) — Depot bancaire Bridge sandbox

**Endpoint:** `POST /payments/deposit/bridge`

Bridge Demo Bank provider_id 574, currency EUR sandbox.
Transaction type ADJUSTMENT, provider BRIDGE.
Succes webhook status ACSC -> credit wallet.

---

## Matrice des blocages par etape

| Etape | Blocage frequent | Code HTTP |
|-------|------------------|-----------|
| OTP request | Numero deja actif | 403 |
| OTP request | Rate limit | 429 |
| OTP verify | Code expire | 410 |
| OTP verify | 3 mauvaises tentatives | 403 |
| Deposit MoMo | KYC pending | 400 |
| Deposit MoMo | MSISDN MoMo invalide | 500 MTN |
| Withdraw MoMo | Solde insuffisant | 400 |
| Virtual card | KYC non verifie | 403 |

---

## Timeline async typique (depot MoMo)

```
T+0s    POST deposit/momo -> 202 PENDING
T+5s    Client recoit push USSD MTN
T+30s   Client approuve
T+35s   Webhook SUCCESSFUL -> wallet credite
T+60s   App poll -> isFinal: true, status: SUCCESS
```

Si pas de webhook a T+120s: polling actif obligatoire.

---

## Distinction KYC legal vs SmartSelfie

| | KYC legal | SmartSelfie |
|---|-----------|-------------|
| Champ | kycStatus | smartSelfieLastAuthSuccess |
| Obligatoire pour | Paiements | Step-up haute valeur |
| Job Smile | job_type 1 ou 11 | job_type 2 ou 4 |
| Webhook modifie | kycStatus | champs smartSelfie* |

SmartSelfie reasons valides: `large_withdrawal`, `pin_reset`, `high_risk_device`, `wallet_recovery`.
