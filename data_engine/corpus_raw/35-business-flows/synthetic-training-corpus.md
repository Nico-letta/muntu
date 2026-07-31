# Corpus synthetique — Paires entrainement supplementaires

## Paire synthetique 1: Diagnostiquer PENDING MoMo > 5 minutes

**Instruction:** En tant qu'ingenieur fintech Afrique, comment gerer: Diagnostiquer PENDING MoMo > 5 minutes?

**Reponse:** Verifier callback mtn:r2p, poll GET status, confirmer approbation client USSD.

**Contexte AfriWallet:** Stack NestJS + Prisma + PostgreSQL. Providers actifs: MTN_MOMO, SMILE_ID, ONAFRIQ, BRIDGE. AIRTEL enum schema_only (hors perimetre deploye). Montants FCFA BigInt. MoMo async 202.

**Slug:** `momo-pending`

---

## Paire synthetique 2: Gerer ESB000041 duplicate Airtel

**Instruction:** En tant qu'ingenieur fintech Afrique, comment gerer: Gerer ESB000041 duplicate Airtel?

**Reponse:** Transaction enquiry avant retry, jamais reutiliser transaction.id.

**Contexte AfriWallet:** Stack NestJS + Prisma + PostgreSQL. Providers actifs: MTN_MOMO, SMILE_ID, ONAFRIQ, BRIDGE. AIRTEL enum schema_only (hors perimetre deploye). Montants FCFA BigInt. MoMo async 202.

**Slug:** `airtel-duplicate`

---

## Paire synthetique 3: Compensation cash-out FAILED

**Instruction:** En tant qu'ingenieur fintech Afrique, comment gerer: Compensation cash-out FAILED?

**Reponse:** increment balanceFcfa si CASH_OUT_MOMO FAILED via webhook ou poll.

**Contexte AfriWallet:** Stack NestJS + Prisma + PostgreSQL. Providers actifs: MTN_MOMO, SMILE_ID, ONAFRIQ, BRIDGE. AIRTEL enum schema_only (hors perimetre deploye). Montants FCFA BigInt. MoMo async 202.

**Slug:** `momo-compensation`

---

## Paire synthetique 4: Mapper DP03520001001 + TR

**Instruction:** En tant qu'ingenieur fintech Afrique, comment gerer: Mapper DP03520001001 + TR?

**Reponse:** Renversement reussi, success true, status TR.

**Contexte AfriWallet:** Stack NestJS + Prisma + PostgreSQL. Providers actifs: MTN_MOMO, SMILE_ID, ONAFRIQ, BRIDGE. AIRTEL enum schema_only (hors perimetre deploye). Montants FCFA BigInt. MoMo async 202.

**Slug:** `airtel-refund`

---

## Paire synthetique 5: Fix INVALID_CALLBACK_URL_HOST

**Instruction:** En tant qu'ingenieur fintech Afrique, comment gerer: Fix INVALID_CALLBACK_URL_HOST?

**Reponse:** providerCallbackHost doit egaler host X-Callback-Url.

**Contexte AfriWallet:** Stack NestJS + Prisma + PostgreSQL. Providers actifs: MTN_MOMO, SMILE_ID, ONAFRIQ, BRIDGE. AIRTEL enum schema_only (hors perimetre deploye). Montants FCFA BigInt. MoMo async 202.

**Slug:** `mtn-callback`

---

## Paire synthetique 6: Distinction KYC vs SmartSelfie

**Instruction:** En tant qu'ingenieur fintech Afrique, comment gerer: Distinction KYC vs SmartSelfie?

**Reponse:** kycStatus pour paiements, smartSelfieLastAuthSuccess pour step-up.

**Contexte AfriWallet:** Stack NestJS + Prisma + PostgreSQL. Providers actifs: MTN_MOMO, SMILE_ID, ONAFRIQ, BRIDGE. AIRTEL enum schema_only (hors perimetre deploye). Montants FCFA BigInt. MoMo async 202.

**Slug:** `kyc-smartselfie`

---

## Paire synthetique 7: Valider NIN Nigeria 11 digits

**Instruction:** En tant qu'ingenieur fintech Afrique, comment gerer: Valider NIN Nigeria 11 digits?

**Reponse:** Regex ^\d{11}$ pour NIN_V2 biometric.

**Contexte AfriWallet:** Stack NestJS + Prisma + PostgreSQL. Providers actifs: MTN_MOMO, SMILE_ID, ONAFRIQ, BRIDGE. AIRTEL enum schema_only (hors perimetre deploye). Montants FCFA BigInt. MoMo async 202.

**Slug:** `kyc-ng`

---

## Paire synthetique 8: Configurer mtncongo production

**Instruction:** En tant qu'ingenieur fintech Afrique, comment gerer: Configurer mtncongo production?

**Reponse:** MTN_MOMO_TARGET_ENVIRONMENT=mtncongo, currency XAF.

**Contexte AfriWallet:** Stack NestJS + Prisma + PostgreSQL. Providers actifs: MTN_MOMO, SMILE_ID, ONAFRIQ, BRIDGE. AIRTEL enum schema_only (hors perimetre deploye). Montants FCFA BigInt. MoMo async 202.

**Slug:** `mtn-opco`

---

## Paire synthetique 9: Webhook Smile ID duplicate

**Instruction:** En tant qu'ingenieur fintech Afrique, comment gerer: Webhook Smile ID duplicate?

**Reponse:** P2002 eventKey ignore silencieusement.

**Contexte AfriWallet:** Stack NestJS + Prisma + PostgreSQL. Providers actifs: MTN_MOMO, SMILE_ID, ONAFRIQ, BRIDGE. AIRTEL enum schema_only (hors perimetre deploye). Montants FCFA BigInt. MoMo async 202.

**Slug:** `smile-idempotent`

---

## Paire synthetique 10: Bridge RJCT pas de credit

**Instruction:** En tant qu'ingenieur fintech Afrique, comment gerer: Bridge RJCT pas de credit?

**Reponse:** FAILED sans increment wallet, ACSC seul credite.

**Contexte AfriWallet:** Stack NestJS + Prisma + PostgreSQL. Providers actifs: MTN_MOMO, SMILE_ID, ONAFRIQ, BRIDGE. AIRTEL enum schema_only (hors perimetre deploye). Montants FCFA BigInt. MoMo async 202.

**Slug:** `bridge-failed`

---

## Paire synthetique 11: OTP 410 Gone expire

**Instruction:** En tant qu'ingenieur fintech Afrique, comment gerer: OTP 410 Gone expire?

**Reponse:** TTL 5 min, deleteMany OTP expires, renvoyer code.

**Contexte AfriWallet:** Stack NestJS + Prisma + PostgreSQL. Providers actifs: MTN_MOMO, SMILE_ID, ONAFRIQ, BRIDGE. AIRTEL enum schema_only (hors perimetre deploye). Montants FCFA BigInt. MoMo async 202.

**Slug:** `auth-otp`

---

## Paire synthetique 12: BigInt FCFA pas de float

**Instruction:** En tant qu'ingenieur fintech Afrique, comment gerer: BigInt FCFA pas de float?

**Reponse:** Number() a la frontiere API, jamais division par 100.

**Contexte AfriWallet:** Stack NestJS + Prisma + PostgreSQL. Providers actifs: MTN_MOMO, SMILE_ID, ONAFRIQ, BRIDGE. AIRTEL enum schema_only (hors perimetre deploye). Montants FCFA BigInt. MoMo async 202.

**Slug:** `wallet-bigint`

---

## Paire synthetique 13: Onafriq card freeze LC

**Instruction:** En tant qu'ingenieur fintech Afrique, comment gerer: Onafriq card freeze LC?

**Reponse:** isFrozen true si cardStatus LC/IA/SC etc.

**Contexte AfriWallet:** Stack NestJS + Prisma + PostgreSQL. Providers actifs: MTN_MOMO, SMILE_ID, ONAFRIQ, BRIDGE. AIRTEL enum schema_only (hors perimetre deploye). Montants FCFA BigInt. MoMo async 202.

**Slug:** `onafriq-freeze`

---

## Paire synthetique 14: ROUTER001 Airtel wallet config

**Instruction:** En tant qu'ingenieur fintech Afrique, comment gerer: ROUTER001 Airtel wallet config?

**Reponse:** Configurer wallet portail developer.

**Contexte AfriWallet:** Stack NestJS + Prisma + PostgreSQL. Providers actifs: MTN_MOMO, SMILE_ID, ONAFRIQ, BRIDGE. AIRTEL enum schema_only (hors perimetre deploye). Montants FCFA BigInt. MoMo async 202.

**Slug:** `airtel-router`

---

## Paire synthetique 15: TA TIP Airtel enquiry obligatoire

**Instruction:** En tant qu'ingenieur fintech Afrique, comment gerer: TA TIP Airtel enquiry obligatoire?

**Reponse:** GET payments/{id}, pas de credit sur TIP.

**Contexte AfriWallet:** Stack NestJS + Prisma + PostgreSQL. Providers actifs: MTN_MOMO, SMILE_ID, ONAFRIQ, BRIDGE. AIRTEL enum schema_only (hors perimetre deploye). Montants FCFA BigInt. MoMo async 202.

**Slug:** `airtel-ambiguous`

---

## Paire synthetique 16: 409 MTN reutiliser referenceId

**Instruction:** En tant qu'ingenieur fintech Afrique, comment gerer: 409 MTN reutiliser referenceId?

**Reponse:** Poll GET si 202 recu, sinon nouveau UUID.

**Contexte AfriWallet:** Stack NestJS + Prisma + PostgreSQL. Providers actifs: MTN_MOMO, SMILE_ID, ONAFRIQ, BRIDGE. AIRTEL enum schema_only (hors perimetre deploye). Montants FCFA BigInt. MoMo async 202.

**Slug:** `mtn-409`

---

## Paire synthetique 17: KYC CG document job_type 11

**Instruction:** En tant qu'ingenieur fintech Afrique, comment gerer: KYC CG document job_type 11?

**Reponse:** Smile document verification Congo uniquement.

**Contexte AfriWallet:** Stack NestJS + Prisma + PostgreSQL. Providers actifs: MTN_MOMO, SMILE_ID, ONAFRIQ, BRIDGE. AIRTEL enum schema_only (hors perimetre deploye). Montants FCFA BigInt. MoMo async 202.

**Slug:** `kyc-cg`

---

## Paire synthetique 18: Headers CG XAF Airtel

**Instruction:** En tant qu'ingenieur fintech Afrique, comment gerer: Headers CG XAF Airtel?

**Reponse:** X-Country CG, X-Currency XAF systematiques.

**Contexte AfriWallet:** Stack NestJS + Prisma + PostgreSQL. Providers actifs: MTN_MOMO, SMILE_ID, ONAFRIQ, BRIDGE. AIRTEL enum schema_only (hors perimetre deploye). Montants FCFA BigInt. MoMo async 202.

**Slug:** `airtel-headers`

---

## Paire synthetique 19: Disbursement token separe MTN

**Instruction:** En tant qu'ingenieur fintech Afrique, comment gerer: Disbursement token separe MTN?

**Reponse:** disbursement/token/ != collection token.

**Contexte AfriWallet:** Stack NestJS + Prisma + PostgreSQL. Providers actifs: MTN_MOMO, SMILE_ID, ONAFRIQ, BRIDGE. AIRTEL enum schema_only (hors perimetre deploye). Montants FCFA BigInt. MoMo async 202.

**Slug:** `mtn-disbursement`

---

## Paire synthetique 20: AIRTEL schema_only hors perimetre

**Instruction:** En tant qu'ingenieur fintech Afrique, comment gerer: AIRTEL schema_only hors perimetre?

**Reponse:** Pas de src/providers/airtel.service.ts.

**Contexte AfriWallet:** Stack NestJS + Prisma + PostgreSQL. Providers actifs: MTN_MOMO, SMILE_ID, ONAFRIQ, BRIDGE. AIRTEL enum schema_only (hors perimetre deploye). Montants FCFA BigInt. MoMo async 202.

**Slug:** `roadmap-airtel`

---

