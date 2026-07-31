# Knowledge Chunks RAG — Version enrichie

## Chunk: `kyc-ng-nin-format`

**Domaine:** `kyc` | **Pays:** `NG` | **Tags:** NIN, BVN, Smile ID, biometric

**Source:** `src/kyc/smile-id-id-rules.ts`

### Contenu canonique

Nigeria NIN (National Identification Number) KYC rules in AfriWallet/Smile ID: NIN, NIN_V2, and NIN_SLIP all require exactly 11 numeric digits (regex ^\d{11}$). V_NIN requires 16 alphanumeric characters. BVN (Bank Verification Number) also uses 11 digits. For BANK_ACCOUNT type, account number is 10 digits plus mandatory bankCode. Biometric KYC template (NIN_V2) requires selfie (image_type_id 0) and 8 liveness images (image_type_id 4). Country code NG, dob format yyyy-mm-dd.

### Implications integration AfriWallet

Ce chunk ancre l'expert MoE `kyc` pour le marche `NG`. Croiser avec `providerTxId`, `eventKey`, schema Prisma.

---

## Chunk: `kyc-gh-ghana-card`

**Domaine:** `kyc` | **Pays:** `GH` | **Tags:** Ghana Card, PASSPORT

**Source:** `src/kyc/smile-id-id-rules.ts`

### Contenu canonique

Ghana identity verification via Smile ID supports GHANA_CARD and GHANA_CARD_NO_PHOTO with format: 3 letters + 9 digits + 1 check digit (regex ^[A-Z]{3}-?\d{9}-?\d$, case insensitive). Example: GHA-123456789-0. Also supported: PASSPORT (7-9 alphanumeric), VOTER_ID (10 digits). Ghana is in West Africa, UEMOA adjacent but uses GHS currency locally.

### Implications integration AfriWallet

Ce chunk ancre l'expert MoE `kyc` pour le marche `GH`. Croiser avec `providerTxId`, `eventKey`, schema Prisma.

---

## Chunk: `kyc-ug-requirements`

**Domaine:** `kyc` | **Pays:** `UG` | **Tags:** secondaryIdNumber, dob

**Source:** `src/kyc/smile-id-id-rules.ts`

### Contenu canonique

Uganda (UG) KYC via Smile ID: only NATIONAL_ID_NO_PHOTO supported. ID format: 14 alphanumeric characters (regex ^[A-Z0-9]{14}$, case insensitive). Uniquely requires two additional mandatory fields: secondaryIdNumber and dob (date of birth yyyy-mm-dd). Missing either field causes validation rejection.

### Implications integration AfriWallet

Ce chunk ancre l'expert MoE `kyc` pour le marche `UG`. Croiser avec `providerTxId`, `eventKey`, schema Prisma.

---

## Chunk: `kyc-cg-document`

**Domaine:** `kyc` | **Pays:** `CG` | **Tags:** document verification, IDENTITY_CARD

**Source:** `docs/smile-id/templates/document-verification-cg.info.json`

### Contenu canonique

Congo Brazzaville (CG) document verification in AfriWallet uses Smile ID job_type 11. Only CG country accepted for document verification endpoint. Document types: DRIVERS_LICENSE, IDENTITY_CARD, PASSPORT, RESIDENT_ID, TAX_ID, TRAVEL_DOC. ZIP must contain info.json, selfie, id_front (type 1), id_back (type 5). Template: document-verification-cg.info.json. Updates kycStatus via webhook.

### Implications integration AfriWallet

Ce chunk ancre l'expert MoE `kyc` pour le marche `CG`. Croiser avec `providerTxId`, `eventKey`, schema Prisma.

---

## Chunk: `momo-deposit-flow`

**Domaine:** `payments` | **Pays:** `multi` | **Tags:** MTN MoMo, RequestToPay, cash-in, async

**Source:** `src/payments/payments.service.ts`

### Contenu canonique

MTN MoMo deposit (cash-in) in AfriWallet: Requires KYC VERIFIED. API POST /payments/deposit/momo with amountFcfa integer. Calls MTN RequestToPay (POST /collection/v1_0/requesttopay) with payer MSISDN. Returns referenceId UUID as providerTxId. Transaction type CASH_IN_MOMO, status PENDING. Async completion via webhook /webhooks/mtn/requesttopay/{referenceId} or polling. Success statuses: SUCCESSFUL, SUCCESS — credits wallet. Sandbox currency often EUR; production XAF. Headers: X-Reference-Id, X-Target-Environment, X-Callback-Url.

### Implications integration AfriWallet

Ce chunk ancre l'expert MoE `payments` pour le marche `multi`. Croiser avec `providerTxId`, `eventKey`, schema Prisma.

---

## Chunk: `momo-withdraw-compensation`

**Domaine:** `payments` | **Pays:** `multi` | **Tags:** Disbursement, cash-out, compensation

**Source:** `src/webhooks/webhooks.service.ts`

### Contenu canonique

MTN MoMo withdraw (cash-out) in AfriWallet: Requires KYC VERIFIED and sufficient balance. Calls MTN Disbursement (POST /disbursement/v1_0/transfer). Wallet balance decremented IMMEDIATELY on initiation (PENDING reservation). Transaction type CASH_OUT_MOMO. On FAILED/REJECTED: automatic compensation re-credits wallet with full amount. Critical consumer protection pattern for African Mobile Money where provider failures are common.

### Implications integration AfriWallet

Ce chunk ancre l'expert MoE `payments` pour le marche `multi`. Croiser avec `providerTxId`, `eventKey`, schema Prisma.

---

## Chunk: `onafriq-card-defaults`

**Domaine:** `cards` | **Pays:** `CM` | **Tags:** Onafriq, virtual card, XAF

**Source:** `src/providers/onafriq.service.ts`

### Contenu canonique

Onafriq virtual card defaults in AfriWallet (Cameroon-centric): country CM, phone country code 237, city Douala, address Wallet user, birthDate 01-JAN-1990, idType 4, idValue AfriWallet-{userId suffix}, cardCurrency XAF. OAuth2 client_credentials to /idp/connect/token. Registration via POST /rest/api/v1/accounts/personalized. HTTP: 10s timeout, 2 retries, 400ms backoff. cardToken = registrationAccountId. Card freeze on statuses IA/LC/SC/DEACTIVATED/EX/INACTIVE/LOSTORSTOLEN; active on AC.

### Implications integration AfriWallet

Ce chunk ancre l'expert MoE `cards` pour le marche `CM`. Croiser avec `providerTxId`, `eventKey`, schema Prisma.

---

## Chunk: `wallet-fcfa-bigint`

**Domaine:** `architecture` | **Pays:** `multi` | **Tags:** FCFA, XAF, BigInt, wallet

**Source:** `prisma/schema.prisma`

### Contenu canonique

AfriWallet wallet stores balance as balanceFcfa BigInt integer in PostgreSQL — no decimal/floating point for FCFA amounts. One wallet per user (userId unique constraint). Default currency XAF on transactions. Wallet created automatically on OTP verification with balance 0. API returns Number(balanceFcfa) for JSON. All balance changes use Prisma atomic transactions alongside Transaction journal entries.

### Implications integration AfriWallet

Ce chunk ancre l'expert MoE `architecture` pour le marche `multi`. Croiser avec `providerTxId`, `eventKey`, schema Prisma.

---

## Chunk: `otp-security-rules`

**Domaine:** `auth` | **Pays:** `multi` | **Tags:** OTP, Twilio, PIN, rate limiting

**Source:** `src/auth/auth.service.ts`

### Contenu canonique

AfriWallet OTP security: 6-digit code, 5-minute TTL, max 3 verification attempts, 60-second resend cooldown, max 5 OTP per hour per phone, max 10 per day. Last OTP invalidates previous ones. Production: SMS via Twilio only (code never in API response). Message: Votre code de vérification est: {code}. Expired OTP returns HTTP 410 Gone. Throttle: 5 req/min/IP on OTP endpoints. PIN stored as bcrypt hash salt 10.

### Implications integration AfriWallet

Ce chunk ancre l'expert MoE `auth` pour le marche `multi`. Croiser avec `providerTxId`, `eventKey`, schema Prisma.

---

## Chunk: `webhook-idempotence`

**Domaine:** `webhooks` | **Pays:** `multi` | **Tags:** idempotence, eventKey, providerTxId

**Source:** `src/webhooks/webhooks.service.ts`

### Contenu canonique

AfriWallet webhook idempotency via WebhookEvent.eventKey unique constraint. Formats: MTN mtn:r2p:{referenceId}, Smile ID {job_id}, Onafriq onafriq:{notificationType}:{requestId}:{transactionId|customerId}, Bridge bridge:payments:{type}:{paymentRequestId}:{status}. Duplicate P2002 silently returns 200. Transaction layer: providerTxId unique (MTN referenceId UUID). Prevents double crediting in async African fintech flows.

### Implications integration AfriWallet

Ce chunk ancre l'expert MoE `webhooks` pour le marche `multi`. Croiser avec `providerTxId`, `eventKey`, schema Prisma.

---

## Chunk: `smartselfie-vs-kyc`

**Domaine:** `kyc` | **Pays:** `multi` | **Tags:** SmartSelfie, KYC, step-up, compliance

**Source:** `src/kyc/kyc.service.ts`

### Contenu canonique

AfriWallet distinguishes legal KYC from SmartSelfie biometric step-up. Legal KYC (job_type 1 biometric, job_type 11 document) updates kycStatus PENDING/VERIFIED/REJECTED via Smile ID webhook — required before any payment. SmartSelfie (job_type 2 auth, job_type 4 register) updates separate User fields (smartSelfieLastAuthSuccess, smartSelfieEnrolledAt) WITHOUT changing kycStatus. Auth reasons: large_withdrawal, pin_reset, high_risk_device, wallet_recovery.

### Implications integration AfriWallet

Ce chunk ancre l'expert MoE `kyc` pour le marche `multi`. Croiser avec `providerTxId`, `eventKey`, schema Prisma.

---

## Chunk: `geographic-cemac-uemoa`

**Domaine:** `glossary` | **Pays:** `multi` | **Tags:** CEMAC, UEMOA, XAF, XOF, FCFA

**Source:** `fintech-corpus/knowledge/09-geographic-coverage.json`

### Contenu canonique

African monetary zones relevant to AfriWallet: CEMAC (XAF/FCFA Central Africa) — Cameroon CM, Congo CG, Gabon, Chad, Equatorial Guinea, CAR. Regulators: BEAC, COBAC. UEMOA (XOF/FCFA West Africa) — Côte d'Ivoire CI, Senegal, Burkina Faso, etc. Regulator: BCEAO. AfriWallet defaults: XAF currency, Onafriq CM/+237. KYC biometric covers CI (West) and CM-adjacent CG (document only). Same FCFA name, different ISO codes and regulatory frameworks.

### Implications integration AfriWallet

Ce chunk ancre l'expert MoE `glossary` pour le marche `multi`. Croiser avec `providerTxId`, `eventKey`, schema Prisma.

---

## Chunk: `bridge-sandbox-deposit`

**Domaine:** `payments` | **Pays:** `multi` | **Tags:** Bridge, Open Banking, sandbox

**Source:** `src/providers/bridge-payments.service.ts`

### Contenu canonique

Bridge API bank deposit in AfriWallet sandbox: POST /payments/deposit/bridge, requires KYC VERIFIED. Uses Demo Bank provider_id 574, currency EUR. Creates Transaction type ADJUSTMENT, provider BRIDGE, status PENDING. Success on Bridge status ACSC (credits wallet). Failure on RJCT/CANC. Webhook POST /webhooks/bridge/payments with bridgeapi-signature HMAC-SHA256. Polling fallback with intervals: CREA/ACTC 2s, PENDING 10s.

### Implications integration AfriWallet

Ce chunk ancre l'expert MoE `payments` pour le marche `multi`. Croiser avec `providerTxId`, `eventKey`, schema Prisma.

---

## Chunk: `planned-not-implemented`

**Domaine:** `architecture` | **Pays:** `multi` | **Tags:** roadmap, Airtel, planned

**Source:** `fintech-corpus/knowledge/10-future-roadmap.json`

### Contenu canonique

Platform features in Prisma schema but NOT implemented in source code: Airtel Money (CASH_IN_AIRTEL, provider AIRTEL) — no service. Card payments (CARD_PAYMENT) and refunds (CARD_REFUND) — enum only. Biometric KYC for Cameroon CM — not in smile-id-id-rules. Dynamic fees — feeFcfa always 0. Multi-wallets — one wallet per user. The model must not describe these as available features.

### Implications integration AfriWallet

Ce chunk ancre l'expert MoE `architecture` pour le marche `multi`. Croiser avec `providerTxId`, `eventKey`, schema Prisma.

---

## Chunk: `contextual-sovereignty-africa`

**Domaine:** `architecture` | **Pays:** `multi` | **Tags:** contextual sovereignty, fine-tuning, african fintech

**Source:** `fintech-corpus/metadata.json`

### Contenu canonique

Contextual sovereignty for African fintech LLMs: Western LLMs lack knowledge of Mobile Money async patterns (MTN RequestToPay/Disbursement), country-specific ID formats (NIN 11 digits, Ghana Card, ZA 13 digits), FCFA/XAF integer handling, Smile ID biometric KYC across 8 African countries, Onafriq virtual card issuing, cash-out compensation patterns, and CEMAC/UEMOA regulatory distinctions. Reference wallet platform codebases encode this domain knowledge for fine-tuning.

### Implications integration AfriWallet

Ce chunk ancre l'expert MoE `architecture` pour le marche `multi`. Croiser avec `providerTxId`, `eventKey`, schema Prisma.

---

