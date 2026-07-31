# Multi-Turn Training Scenarios (AfriWallet)

## Scenario 1

**SYSTEM:**

Tu es un expert fintech africain. Tu maîtrises les plateformes wallet, MTN MoMo, Smile ID KYC, Onafriq cartes virtuelles, wallets FCFA.

**USER:**

Je développe une app wallet au Cameroun. Comment onboarder un utilisateur avec numéro +237 ?

**ASSISTANT:**

Pour onboarder un utilisateur camerounais sur une plateforme wallet type AfriWallet :

1. **Activation** : POST /auth/otp/request avec phoneNumber (+237670000000 format international). OTP SMS 6 chiffres, TTL 5 min.
2. **PIN** : POST /auth/otp/verify avec otp + pin (4 chiffres minimum). Crée User + Wallet FCFA (solde 0) + JWT.
3. **KYC** : Le Cameroun (CM) n'est pas dans les règles biometric Smile ID. Options : document verification Congo (CG) si applicable, ou attendre support CM. Defaults Onafriq utilisent CM/+237/Douala pour les cartes.
4. **Connexion quotidienne** : POST /auth/pin/verify.

Rate limits OTP : 60s cooldown, 5/h, 10/jour. En prod, OTP par Twilio uniquement.

**USER:**

Et pour le KYC au Nigeria avec NIN ?

**ASSISTANT:**

Pour le Nigeria, le KYC biométrique NIN_V2 est fully supporté :

1. POST /kyc/start → kycStatus PENDING
2. POST /kyc/biometric/upload-url avec country: NG, idType: NIN_V2, idNumber: 11 chiffres, firstName, lastName, dob: yyyy-mm-dd
3. Préparer ZIP : info.json (template biometric-kyc-ng-nin_v2) + selfie.jpg + liveness_1 à liveness_8.jpg
4. POST /kyc/biometric/upload-zip avec ZIP en base64
5. Webhook /webhooks/smile-id ou polling POST /kyc/utils/job-status jobType: 1
6. kycStatus → VERIFIED → accès paiements MoMo

NIN format : exactement 11 chiffres. MTN opco : mtnnigeria.

*Metadata:* `{"domain": "onboarding", "countries": ["CM", "NG"], "language": "fr", "scenario": "developer_onboarding"}`

---

## Scenario 2

**SYSTEM:**

You are an African fintech expert specializing in Mobile Money integration patterns.

**USER:**

My MoMo deposit stays PENDING forever. What's wrong?

**ASSISTANT:**

MTN MoMo deposits are **asynchronous by design**. PENDING is the expected initial state. Common causes of stuck PENDING:

1. **Client didn't confirm** on their phone — RequestToPay requires user approval on MoMo app/USSD.
2. **No callback URL** — set MTN_MOMO_CALLBACK_BASE_URL to your public HTTPS URL. Without it, rely on polling: GET /payments/deposit/momo/{referenceId}/status
3. **Wrong target environment** — sandbox vs mtnnigeria/mtncameroon/mtncongo mismatch.
4. **Currency mismatch** — sandbox often uses EUR, not XAF.
5. **KYC not VERIFIED** — deposit rejected at API level before MTN call.

Poll every 2-10 seconds. SUCCESS when status is SUCCESSFUL or SUCCESS.

**USER:**

What if the withdraw fails after my balance was deducted?

**ASSISTANT:**

A well-designed wallet platform implements **automatic compensation** for failed cash-outs:

1. On withdraw initiation, balance is immediately decremented (PENDING reservation).
2. MTN Disbursement transfer is sent.
3. If webhook/polling returns FAILED or REJECTED → wallet is **re-credited** with the full amount.
4. Transaction status → FAILED.

The user should never lose funds on provider failure. If compensation didn't happen, check: webhook delivery, referenceId correlation via providerTxId, or duplicate webhook ignored by idempotency.

*Metadata:* `{"domain": "payments", "language": "en", "scenario": "momo_troubleshooting"}`

---

## Scenario 3

**SYSTEM:**

Tu es un expert compliance fintech Afrique.

**USER:**

Un client veut retirer 500 000 FCFA. Quelles vérifications avant ?

**ASSISTANT:**

Vérifications obligatoires pour un retrait MoMo de 500 000 FCFA :

1. **KYC VERIFIED** — sans ça, POST /payments/withdraw/momo retourne BadRequestException.
2. **Solde suffisant** — wallet.balanceFcfa >= 500000 (entiers BigInt).
3. **SmartSelfie recommandé** — pour large_withdrawal, déclencher POST /kyc/smartselfie/auth avec reason: large_withdrawal avant le retrait. SmartSelfie est décorrélé du KYC légal mais c'est le step-up biométrique prévu.
4. **MTN Disbursement** — vérifier opco et credentials prod (mtncameroon, currency XAF).
5. **Réservation immédiate** — le solde sera décrémenté dès l'init, compensation si échec MTN.

500 000 FCFA nécessite validation limites MTN opco et réglementaires locales.

**USER:**

Différence entre SmartSelfie et KYC ici ?

**ASSISTANT:**

**KYC légal** (biometric/document) :
- Met à jour kycStatus : PENDING → VERIFIED/REJECTED
- Obligatoire pour TOUT mouvement d'argent
- Job types 1 (biometric) ou 11 (document CG)

**SmartSelfie** (step-up) :
- Met à jour smartSelfieLastAuthSuccess, smartSelfieLastAuthAt
- NE change PAS kycStatus
- Raisons : large_withdrawal, pin_reset, high_risk_device, wallet_recovery
- Job types 2 (auth) ou 4 (register/enrollment)

Un user peut être KYC VERIFIED sans jamais avoir fait SmartSelfie. SmartSelfie ajoute une couche biométrique pour actions sensibles.

*Metadata:* `{"domain": "compliance", "country": "CM", "language": "fr", "scenario": "large_withdrawal_compliance"}`

---

## Scenario 4

**SYSTEM:**

You are an expert in African virtual card infrastructure.

**USER:**

How do I issue a virtual card for a verified user in Cameroon?

**ASSISTANT:**

Virtual card issuance on a typical African wallet platform:

**Endpoint**: POST /virtual-cards
**Body**: { "walletId": "...", "amountFcfa": 3000 }
**Auth**: JWT Bearer

**Prerequisites**:
- kycStatus = VERIFIED
- wallet.balanceFcfa >= amountFcfa

**Flow**:
1. Onafriq OAuth2 token (client_credentials)
2. Register personalized account with defaults: CM, +237, Douala, XAF
3. Wallet decremented, VirtualCard created, CARD_ISSUANCE_FEE transaction SUCCESS

**Returns**: cardToken, lastFour, updated wallet balance. passCode stored in transaction metadata.

**USER:**

The card got frozen. How does that work?

**ASSISTANT:**

Onafriq sends webhooks to POST /webhooks/onafriq/cards when card status changes.

**Freeze triggers** (isFrozen = true): cardStatus in IA, LC, SC, DEACTIVATED, EX, INACTIVE, LOSTORSTOLEN

**Unfreeze** (isFrozen = false): cardStatus = AC (Active)

Correlation: cardToken matches customerId/accountId from webhook. Fallback: lastFour digits.

Webhook signature: x-webhook-signature (AES256). Idempotency via eventKey in WebhookEvent table.

*Metadata:* `{"domain": "cards", "country": "CM", "language": "en", "scenario": "virtual_card_lifecycle"}`

---

