# Instruction-Response Training Pairs (AfriWallet)

> Source: afriwallet_codebase/fintech-corpus/training/instruction-response.jsonl

## Pair 1

**Instruction:** Quel est le format valide d'un NIN (National Identification Number) au Nigeria pour le KYC Smile ID ?

**Output:** Le NIN au Nigeria doit contenir exactement 11 chiffres numériques, validé par la regex ^\d{11}$. Les variantes acceptées par Smile ID dans AfriWallet incluent NIN, NIN_V2 et NIN_SLIP — toutes avec le même format 11 chiffres. Il existe aussi le V_NIN (Virtual NIN) au format 16 caractères alphanumériques. Pour un KYC biométrique NIN_V2, il faut fournir firstName, lastName, dob au format yyyy-mm-dd, un selfie (image_type_id 0) et 8 images de liveness (image_type_id 4).

*Domain:* `kyc` | *Country:* `NG` | *Difficulty:* `basic`

---

## Pair 2

**Instruction:** What is the valid format for a Ghana Card identity document?

**Output:** The Ghana Card format is: 3 uppercase letters, optionally followed by a hyphen, then 9 digits, optionally followed by a hyphen, then 1 digit. Regex: ^[A-Z]{3}-?\d{9}-?\d$ (case insensitive). Example: GHA-123456789-0. Both GHANA_CARD and GHANA_CARD_NO_PHOTO id types use this format. Ghana also supports PASSPORT (7-9 alphanumeric chars) and VOTER_ID (10 digits).

*Domain:* `kyc` | *Country:* `GH` | *Difficulty:* `basic`

---

## Pair 3

**Instruction:** Quels champs supplémentaires sont requis pour un BANK_ACCOUNT au Nigeria vs en Zambie ?

**Output:** Pour un BANK_ACCOUNT au Nigeria (NG) : le numéro de compte doit avoir 10 chiffres (regex ^\d{10}$) et le champ bankCode est obligatoire. Pour un BANK_ACCOUNT en Zambie (ZM) : le numéro doit avoir 13 chiffres (regex ^\d{13}$) et bankCode est également obligatoire. Dans les deux cas, sans bankCode, la validation AfriWallet rejette la requête avec une BadRequestException.

*Domain:* `kyc` | *Country:* `NG` | *Difficulty:* `intermediate`

---

## Pair 4

**Instruction:** Quels pays africains sont supportés pour le KYC biométrique Smile ID dans AfriWallet ?

**Output:** 8 pays sont supportés pour le KYC biométrique (biometric registry) : CI (Côte d'Ivoire), GH (Ghana), KE (Kenya), NG (Nigeria), ZA (Afrique du Sud), UG (Ouganda), ZM (Zambie), ZW (Zimbabwe). Le Cameroun (CM) n'est PAS dans les règles biometric — seulement en defaults Onafriq pour les cartes. Le Congo (CG) supporte uniquement la vérification document (job_type 11), pas le biometric registry.

*Domain:* `kyc` | *Country:* `global` | *Difficulty:* `basic`

---

## Pair 5

**Instruction:** Explain the difference between legal KYC and SmartSelfie in AfriWallet.

**Output:** Legal KYC (Biometric KYC job_type 1 or Document Verification job_type 11) updates the user's kycStatus field: PENDING → VERIFIED (webhook job_success=true) or REJECTED (job_success=false). KYC VERIFIED is required before any money movement. SmartSelfie (job_type 2 auth, job_type 4 register) is a biometric step-up DECOUPLED from legal KYC — it updates separate fields on User (smartSelfieLastAuthSuccess, smartSelfieEnrolledAt, etc.) without changing kycStatus. SmartSelfie reasons: large_withdrawal, pin_reset, high_risk_device, wallet_recovery.

*Domain:* `kyc` | *Country:* `global` | *Difficulty:* `intermediate`

---

## Pair 6

**Instruction:** Comment fonctionne un dépôt Mobile Money MTN (cash-in) dans AfriWallet ?

**Output:** Le dépôt MoMo utilise l'API MTN RequestToPay (collection). Flux : 1) Vérifier KYC VERIFIED. 2) POST /payments/deposit/momo avec amountFcfa entier positif. 3) MTN initie RequestToPay — retourne referenceId UUID (HTTP 202). 4) Transaction CASH_IN_MOMO créée en PENDING, providerTxId = referenceId. 5) Le client confirme sur son téléphone MoMo. 6) Callback webhook POST /webhooks/mtn/requesttopay/{referenceId} OU polling GET status. 7) Si SUCCESSFUL/SUCCESS : crédit wallet + transaction SUCCESS. En sandbox MTN, la devise est souvent EUR ; en production XAF.

*Domain:* `payments` | *Country:* `global` | *Difficulty:* `intermediate`

---

## Pair 7

**Instruction:** What happens when a MoMo cash-out (withdraw) fails in AfriWallet?

**Output:** When initiating a MoMo withdraw, AfriWallet immediately decrements the wallet balance as a PENDING reservation before calling MTN Disbursement transfer API. If the provider later returns FAILED or REJECTED (via webhook or polling), AfriWallet executes automatic compensation: the reserved amount is credited back to the wallet and the transaction status becomes FAILED. This compensation pattern is critical for consumer protection — client funds must never be lost due to provider failure.

*Domain:* `payments` | *Country:* `global` | *Difficulty:* `advanced`

---

## Pair 8

**Instruction:** Qu'est-ce qu'un OpCo MTN et comment le configurer ?

**Output:** OpCo (Operating Company) est l'environnement MTN MoMo spécifique à un pays/opérateur. Il se configure via la variable MTN_MOMO_TARGET_ENVIRONMENT et le header HTTP X-Target-Environment. Valeurs connues : sandbox (tests), mtnnigeria (Nigeria), mtncameroon (Cameroun), mtncongo (Congo). En sandbox, MTN_MOMO_CURRENCY est souvent EUR ; en production, XAF pour la zone CEMAC. Chaque opco a ses propres credentials API (subscription key, api user, api key).

*Domain:* `payments` | *Country:* `global` | *Difficulty:* `intermediate`

---

## Pair 9

**Instruction:** Quelles sont les règles de rate limiting OTP dans AfriWallet ?

**Output:** Anti-abus OTP : cooldown de 60 secondes entre deux demandes pour le même numéro ; maximum 5 OTP par heure par numéro ; maximum 10 OTP par jour par numéro ; maximum 3 tentatives de saisie par code OTP ; TTL du code : 5 minutes (OTP_TTL_MINUTES). Le dernier OTP émis invalide les précédents ('le dernier l'emporte'). En production, le code n'est jamais retourné en API — envoi SMS Twilio obligatoire avec message 'Votre code AfriWallet est: {code}'. Throttling HTTP : 5 requêtes/minute/IP sur les endpoints OTP.

*Domain:* `auth` | *Country:* `global` | *Difficulty:* `intermediate`

---

## Pair 10

**Instruction:** How does Onafriq virtual card issuance work in AfriWallet?

**Output:** Virtual card creation via POST /virtual-cards with walletId and amountFcfa. Prerequisites: KYC VERIFIED and sufficient wallet balance. Flow: 1) OAuth2 token from Onafriq IDP (client_credentials). 2) POST /rest/api/v1/accounts/personalized with defaults: country CM, phone +237, city Douala, currency XAF. 3) Wallet decremented, VirtualCard created (cardToken = registrationAccountId, lastFour = registrationLast4Digits), Transaction CARD_ISSUANCE_FEE SUCCESS. HTTP resilience: 10s timeout, 2 retries, 400ms backoff, retriable on 408/429/5xx.

*Domain:* `cards` | *Country:* `CM` | *Difficulty:* `intermediate`

---

## Pair 11

**Instruction:** Quels statuts de carte Onafriq déclenchent un gel (freeze) ?

**Output:** Le webhook Onafriq POST /webhooks/onafriq/cards met isFrozen=true si cardStatus est l'un de : IA, LC, SC, DEACTIVATED, EX, INACTIVE, LOSTORSTOLEN. La carte est dégelée (isFrozen=false) si cardStatus = AC (Active). La corrélation se fait via cardToken (= customerId/accountId Onafriq) ou lastFour en fallback. L'eventKey d'idempotence : onafriq:{notificationType}:{requestId}:{transactionId|customerId}.

*Domain:* `cards` | *Country:* `global` | *Difficulty:* `intermediate`

---

## Pair 12

**Instruction:** Explain webhook idempotency patterns across AfriWallet providers.

**Output:** AfriWallet uses WebhookEvent.eventKey (@unique) for idempotency. Formats: MTN MoMo → mtn:r2p:{referenceId}; Smile ID → {job_id} or smile:{userId}:{timestamp}:{signature}; Onafriq → onafriq:{notificationType}:{requestId}:{transactionId|customerId}; Bridge → bridge:payments:{type}:{paymentRequestId}:{status}. On duplicate (Prisma P2002), webhooks return 200 silently. Transaction layer also uses providerTxId (@unique) — MTN referenceId as UUID. This dual-layer idempotency prevents double crediting/debiting in async African fintech flows.

*Domain:* `webhooks` | *Country:* `global` | *Difficulty:* `advanced`

---

## Pair 13

**Instruction:** Quel format d'identité est requis pour le KYC en Ouganda (UG) ?

**Output:** En Ouganda, seul NATIONAL_ID_NO_PHOTO est supporté. Le numéro doit matcher ^[A-Z0-9]{14}$ (14 caractères alphanumériques, insensible à la casse). Deux champs supplémentaires sont OBLIGATOIRES : secondaryIdNumber (numéro d'identité secondaire) et dob (date de naissance au format yyyy-mm-dd). Sans ces champs, validateSmileIdKycInput lève une BadRequestException.

*Domain:* `kyc` | *Country:* `UG` | *Difficulty:* `intermediate`

---

## Pair 14

**Instruction:** What is the South African National ID format for Smile ID KYC?

**Output:** South Africa (ZA) National ID and NATIONAL_ID_NO_PHOTO require exactly 13 digits (regex ^\d{13}$). ZA also supports PHONE_NUMBER (10 digits) and REFUGEE_ID (3-6 letters followed by 9-12 digits, regex ^[A-Za-z]{3,6}\d{9,12}$).

*Domain:* `kyc` | *Country:* `ZA` | *Difficulty:* `basic`

---

## Pair 15

**Instruction:** Comment effectuer un KYC document au Congo (CG) dans AfriWallet ?

**Output:** La vérification document au Congo utilise Smile ID job_type 11. Seul le pays CG est accepté — les autres pays sont rejetés. Types de document : DRIVERS_LICENSE, IDENTITY_CARD, PASSPORT, RESIDENT_ID, TAX_ID, TRAVEL_DOC. Flux REST recommandé : 1) POST /kyc/document-verification/upload-url. 2) Préparer ZIP avec info.json (template document-verification-cg.info.json) + selfie + id_front (type 1) + id_back (type 5). 3) POST /kyc/document-verification/upload-zip. 4) Attendre webhook Smile ID → kycStatus VERIFIED ou REJECTED.

*Domain:* `kyc` | *Country:* `CG` | *Difficulty:* `intermediate`

---

## Pair 16

**Instruction:** Quelle est la différence entre FCFA, XAF et XOF dans le contexte africain ?

**Output:** FCFA (Franc CFA) est le nom commun de la monnaie dans deux zones distinctes : XAF (Franc CFA CEMAC — Afrique Centrale : Cameroun, Congo, Gabon, Tchad, Guinée Équatoriale, RCA) et XOF (Franc CFA UEMOA — Afrique de l'Ouest : Côte d'Ivoire, Sénégal, Burkina Faso, etc.). AfriWallet stocke les soldes wallet en FCFA entiers (BigInt) avec currency par défaut XAF. Onafriq émet des cartes en XAF avec defaults Cameroun. Attention : même nom FCFA, codes ISO et zones réglementaires différents (BEAC vs BCEAO).

*Domain:* `glossary` | *Country:* `global` | *Difficulty:* `basic`

---

## Pair 17

**Instruction:** What polling intervals does AfriWallet use for async payment status checks?

**Output:** AfriWallet polling fallback intervals based on provider status: CREA or ACTC → 2000ms (2 seconds); PDNG, PENDING, or UNKNOWN → 10000ms (10 seconds); all other statuses → 30000ms (30 seconds). Status normalization: SUCCESS from SUCCESS/SUCCESSFUL/ACSC; FAILED from FAILED/REJECTED/RJCT/CANC/CANCELLED/CANCELED; everything else remains PENDING. Endpoints: GET /payments/deposit/momo/:referenceId/status, GET /payments/withdraw/momo/:referenceId/status, GET /payments/deposit/bridge/:paymentRequestId/status.

*Domain:* `payments` | *Country:* `global` | *Difficulty:* `advanced`

---

## Pair 18

**Instruction:** Quelles fonctionnalités sont planifiées mais NON implémentées dans AfriWallet ?

**Output:** Fonctionnalités présentes en enum Prisma mais sans code dans src/ : 1) Airtel Money (CASH_IN_AIRTEL, provider AIRTEL) — pas de service ni webhook. 2) Paiements carte (CARD_PAYMENT) et remboursements (CARD_REFUND). 3) KYC biométrique Cameroun (CM absent de smile-id-id-rules). 4) Frais dynamiques (feeFcfa toujours 0 malgré le champ en base). 5) Multi-wallets (1 wallet/user via userId @unique). Le modèle ne doit pas présenter ces features comme disponibles.

*Domain:* `architecture` | *Country:* `global` | *Difficulty:* `intermediate`

---

## Pair 19

**Instruction:** Describe the complete AfriWallet user onboarding flow from phone number to first deposit.

**Output:** Complete onboarding: 1) POST /auth/otp/request with new phoneNumber → SMS OTP 6 digits. 2) POST /auth/otp/verify with otp + pin → User created, Wallet (balance 0 FCFA), JWT token. 3) POST /kyc/start → kycStatus PENDING. 4) POST /kyc/biometric/upload-url (e.g., NG/NIN_V2) → S3 upload URL + jobId. 5) Upload ZIP (info.json + selfie + 8 liveness images) via /kyc/biometric/upload-zip. 6) Smile ID webhook or polling → kycStatus VERIFIED. 7) POST /payments/deposit/momo {amountFcfa: 5000} → MTN RequestToPay PENDING. 8) Client confirms on phone → webhook/polling → wallet credited. Example test phone: +237670000000.

*Domain:* `architecture` | *Country:* `global` | *Difficulty:* `advanced`

---

## Pair 20

**Instruction:** Quels sont les codes d'erreur Smile ID importants à connaître ?

**Output:** Codes erreur Smile ID dans AfriWallet : 2215 = job_id déjà existant — solution : générer un nouveau jobId ou passer retry:true. 2209 = job type incompatible — l'utilisateur est déjà enrolled SmartSelfie, utiliser auth au lieu de register. 2304 = job introuvable — vérifier jobId ou attendre propagation. En sandbox, sandboxResult '0'/'1'/'2' permet de forcer succès/échec/alternatif pour les tests.

*Domain:* `kyc` | *Country:* `global` | *Difficulty:* `intermediate`

---

## Pair 21

**Instruction:** How is the AfriWallet wallet balance stored and why?

**Output:** Wallet balance is stored as balanceFcfa BigInt (integer) in PostgreSQL via Prisma. This avoids floating-point precision errors common with decimal types when handling FCFA amounts. The API returns Number(balanceFcfa) for JSON serialization. Default currency field on Transaction is XAF. One wallet per user (Wallet.userId is unique). Balance modifications happen atomically in Prisma transactions alongside Transaction record creation/updates.

*Domain:* `architecture` | *Country:* `global` | *Difficulty:* `intermediate`

---

## Pair 22

**Instruction:** Quelles sont les raisons valides pour une authentification SmartSelfie ?

**Output:** Les 4 raisons SmartSelfie Auth strictement validées par le controller KYC (@IsIn) : large_withdrawal (retrait important), pin_reset (réinitialisation PIN), high_risk_device (appareil à risque), wallet_recovery (récupération wallet). Chaque raison est incluse dans le jobId prefix ssauth_{userId}_{reason}_{timestamp}. SmartSelfie Register (job_type 4) utilise prefix ssreg_ pour l'enrollment initial.

*Domain:* `kyc` | *Country:* `global` | *Difficulty:* `basic`

---

## Pair 23

**Instruction:** Explain Bridge API bank deposit integration in AfriWallet sandbox.

**Output:** Bridge deposit via POST /payments/deposit/bridge requires KYC VERIFIED. Creates Bridge paymentRequest with sandbox Demo Bank (provider_id 574), currency EUR. Transaction type ADJUSTMENT, provider BRIDGE, status PENDING. Returns paymentRequestId and payment URL. Success when Bridge status ACSC → wallet credited. Failure on RJCT/CANC/CANCELLED. Webhook at POST /webhooks/bridge/payments with bridgeapi-signature HMAC-SHA256. Polling fallback available at GET /payments/deposit/bridge/:paymentRequestId/status.

*Domain:* `payments` | *Country:* `global` | *Difficulty:* `intermediate`

---

## Pair 24

**Instruction:** Quel est le parcours de réinitialisation du PIN dans AfriWallet ?

**Output:** Reset PIN en 2 étapes : 1) POST /auth/pin/reset/request avec phoneNumber — requiert un compte existant (sinon 404). Envoie OTP SMS avec mêmes règles anti-abus (60s cooldown, 5/h, 10/jour). 2) POST /auth/pin/reset/verify avec phoneNumber, otp et nouveau pin — vérifie OTP (TTL 5 min, max 3 tentatives), hash bcrypt le nouveau PIN, supprime OTP utilisés, retourne JWT. Alternative sécurisée : SmartSelfie auth avec reason pin_reset avant le reset.

*Domain:* `auth` | *Country:* `global` | *Difficulty:* `basic`

---

## Pair 25

**Instruction:** What security measures protect AfriWallet webhooks from replay attacks?

**Output:** Provider-specific webhook security: Smile ID — HMAC signature validation with ±5 minute timestamp anti-replay window. Onafriq — x-webhook-signature using AES256 with ONAFRIQ_WEBHOOK_SECRET. Bridge — bridgeapi-signature HMAC-SHA256 with BRIDGE_WEBHOOK_SECRET. MTN — optional IP allowlist (MTN_MOMO_WEBHOOK_IP_ALLOWLIST). All providers also use eventKey-based idempotency in WebhookEvent table to prevent duplicate processing regardless of replay.

*Domain:* `compliance` | *Country:* `global` | *Difficulty:* `advanced`

---

## Pair 26

**Instruction:** Quel format d'identité nationale utilise le Zimbabwe pour le KYC Smile ID ?

**Output:** Au Zimbabwe (ZW), seul NATIONAL_ID_NO_PHOTO est supporté. Format : 8 à 9 chiffres, suivis d'une lettre, suivis de 2 chiffres. Regex : ^[0-9]{8,9}[A-Za-z]\d{2}$. Exemple de structure : 12345678A90.

*Domain:* `kyc` | *Country:* `ZW` | *Difficulty:* `basic`

---

## Pair 27

**Instruction:** What is the BVN in Nigeria and how does it differ from NIN?

**Output:** BVN (Bank Verification Number) is Nigeria's unique bank customer identifier — 11 digits (regex ^\d{11}$). NIN (National Identification Number) is the national identity number, also 11 digits, with variants NIN, NIN_V2, NIN_SLIP. Key difference: BVN is banking-specific (requires bank relationship), NIN is civil/national identity. For BANK_ACCOUNT KYC in Nigeria, you need a 10-digit account number PLUS mandatory bankCode. Both BVN and NIN are verified against registries via Smile ID biometric KYC.

*Domain:* `kyc` | *Country:* `NG` | *Difficulty:* `intermediate`

---

## Pair 28

**Instruction:** Comment AfriWallet gère-t-il la rétention des données OTP et webhooks ?

**Output:** Maintenance automatique via cron toutes les 2 heures (MaintenanceService) : purge des OtpRequest expirés de plus de 7 jours (OTP_RETENTION_DAYS) ; purge des WebhookEvent traités de plus de 30 jours (WEBHOOK_RETENTION_DAYS). Les transactions restent immuables indéfiniment (journal comptable). Les payloads webhook sont stockés en JSON dans WebhookEvent.payload pour audit.

*Domain:* `compliance` | *Country:* `global` | *Difficulty:* `intermediate`

---

## Pair 29

**Instruction:** Pourquoi un LLM expert fintech africain doit-il maîtriser les patterns async Mobile Money ?

**Output:** Contrairement aux paiements carte bancaires synchrones (autorisation immédiate), Mobile Money africain (MTN MoMo) est fondamentalement asynchrone : RequestToPay retourne HTTP 202 PENDING, le client doit confirmer sur son téléphone, et le résultat arrive via callback webhook ou polling. Une plateforme wallet bien conçue implémente les deux mécanismes avec idempotence (providerTxId) et compensation cash-out. Un LLM occidental ignorant ce pattern recommanderait incorrectement des flows synchrones, causant des bugs de double-crédit ou de fonds bloqués — d'où l'importance de la souveraineté contextuelle africaine.

*Domain:* `architecture` | *Country:* `global` | *Difficulty:* `advanced`

---

## Pair 30

**Instruction:** What are the Côte d'Ivoire (CI) identity document formats for KYC?

**Output:** Côte d'Ivoire supports two id types: NATIONAL_ID_NO_PHOTO and RESIDENT_ID_NO_PHOTO. Both use the same regex: ^(?:\d{11}|[A-Za-z]\d{10})$ — either 11 digits OR 1 letter followed by 10 digits. CI is in the UEMOA zone (XOF currency) but AfriWallet wallet defaults to XAF. CI is supported for biometric KYC via Smile ID.

*Domain:* `kyc` | *Country:* `CI` | *Difficulty:* `basic`

---

