# AfriWallet — Flux métier (Business Flows)

> **Couche** : `35-business-flows` · **Fichier fusionné** (ex-use-cases v3)  
> **Expert MoE** : cinématiques transactionnelles OTP → KYC → MoMo → cartes  
> **Distinction** : ≠ `15-mobile-ux-studies/` (exemples UI) — ce dossier = orchestration backend/métier  
> **Source** : `src/auth/`, `src/payments/`, `src/kyc/`, `src/virtual-cards/`

---

## 1. Onboarding OTP + PIN

MSISDN-first. OTP SMS 6 chiffres + PIN bcrypt + JWT 15m.

**Flux** : `/auth/otp/request` → `/auth/otp/verify` → User + Wallet(0) + JWT → `/auth/pin/verify` daily.

```json
{
  "otp": { "length": 6, "ttl_min": 5, "max_attempts": 3, "cooldown_s": 60, "max_hour": 5, "max_day": 10 },
  "pin": { "hash": "bcrypt", "salt": 10 },
  "prod_rule": "OTP never returned in API — Twilio SMS only"
}
```

### Golden Snippet — émission OTP sécurisée

En production, le code OTP part **uniquement par SMS** ; l'API renvoie `{ sent: true }` sans exposer le code. Rate limits anti-abus : cooldown 60s, 5/h, 10/j.

```typescript
// src/auth/auth.service.ts — issueOtp()
const code = (Math.floor(100000 + Math.random() * 900000)).toString();

// Cooldown 60s + quotas 5/h et 10/j (voir contrat JSON ci-dessus)
// ...

const isProd = process.env.NODE_ENV === 'production';

if (isProd && !this.sms.isConfigured()) {
  throw new InternalServerErrorException('SMS provider is required in production');
}

if (this.sms.isConfigured()) {
  await this.sms.sendSms({
    to: phoneNumber,
    body: `Votre code de verification est: ${code}`,
  });
}

// En prod : jamais le code dans la réponse HTTP
return isProd ? { phoneNumber, sent: true } : { phoneNumber, otp: code };
```

---

## 2. KYC Biométrique (REST)

Met à jour `kycStatus`. **Obligatoire** avant paiements et cartes.

**Flux** : `/kyc/start` → `/kyc/biometric/upload-url` → ZIP (selfie + liveness) → `/kyc/biometric/upload-zip` → webhook Smile.

```json
{
  "kycStatus_flow": { "PENDING": "open", "VERIFIED": "job_success true", "REJECTED": "job_success false" },
  "NG_example": { "country": "NG", "idType": "NIN_V2", "idNumber": "11 digits" },
  "CM_note": "no biometric registry — document CG or Onafriq defaults only"
}
```

---

## 3. SmartSelfie Step-Up

**Ne modifie pas** `kycStatus`. Raisons : `large_withdrawal`, `pin_reset`, `high_risk_device`, `wallet_recovery`.

**Flux** : `/kyc/smartselfie/auth/upload-url` → upload → `/kyc/smartselfie/confirm`.

---

## 4. MoMo Cash-In / Cash-Out

**Prérequis** : KYC VERIFIED. **Async** : HTTP 202 PENDING → webhook/polling.

**Cash-in** : `/payments/deposit/momo` → RequestToPay → SUCCESS crédite wallet.

**Cash-out** : décrément immédiat → Disbursement → FAILED = **compensation recrédit**.

```json
{
  "success_statuses": ["SUCCESSFUL", "SUCCESS", "ACSC"],
  "failed_statuses": ["FAILED", "REJECTED", "RJCT"],
  "polling_ms": { "CREA": 2000, "PENDING": 10000, "default": 30000 }
}
```

---

## 5. Émission Carte Virtuelle Onafriq

**Prérequis** : KYC VERIFIED + solde ≥ amountFcfa.

**Flux** : `POST /virtual-cards` → OAuth2 Onafriq → register → `CARD_ISSUANCE_FEE` SUCCESS → webhooks freeze/unfreeze.

```json
{
  "response": { "cardToken": "Onafriq accountId", "lastFour": "4 digits", "isFrozen": "via webhook cardStatus" }
}
```

## Voir aussi

- `../20-backend-api/execution-lifecycle/async-pipeline-jobs.md`
- `../40-compliance-rules/kyc-id-rules-by-country.md`
- `../90-codebase-constraints/project-roadmap.md`
