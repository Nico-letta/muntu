# Configuration et Intégrations des Providers — AfriWallet

> **Couche** : `30-system-integrations` · **Expert MoE** : spécifications API / plomberie technique  
> **Source** : `src/providers/*.ts`, `.env.example`

## Contexte

Ce fichier indexe les **contrats d'intégration** avec les providers externes. Détails complets MTN Developer → `providers/mtn-momo-api-reference.md`.

---

## 1. MTN Mobile Money (MTN_MOMO)

* **Type** : Mobile Money Infrastructure  
* **Fichiers source** : `src/providers/mtn.service.ts`, `src/payments/payments.service.ts`

### Environnement production

```json
{
  "production": {
    "currency_default": "XAF",
    "target_environments": ["mtnnigeria", "mtncameroon", "mtncongo"],
    "note": "OpCo spécifique par pays MTN"
  },
  "sandbox": {
    "base_url": "https://sandbox.momodeveloper.mtn.com",
    "currency_default": "EUR",
    "target_environment": "sandbox"
  }
}
```

### Headers requis

```json
{
  "auth": "OAuth2 client credentials via Basic auth",
  "headers": [
    "Authorization: Bearer {token}",
    "Ocp-Apim-Subscription-Key",
    "X-Target-Environment",
    "X-Reference-Id: UUID on POST",
    "X-Callback-Url: optional HTTPS"
  ]
}
```

### APIs wallet

```json
{
  "request_to_pay": "POST /collection/v1_0/requesttopay → HTTP 202",
  "transfer": "POST /disbursement/v1_0/transfer",
  "async_pattern": "Init PENDING → webhook or polling"
}
```

### Webhook callback MTN

```json
{
  "path": "POST /webhooks/mtn/requesttopay/{referenceId}",
  "event_key": "mtn:r2p:{referenceId}",
  "success_values": ["SUCCESSFUL", "SUCCESS"],
  "failed_values": ["FAILED", "REJECTED"]
}
```

→ Référence catalogue MTN Developer : [providers/mtn-momo-api-reference.md](./providers/mtn-momo-api-reference.md)

---

## 2. Smile Identity (SMILE_ID)

* **Type** : KYC biométrique Afrique  
* **Fichiers source** : `src/providers/smile-id.service.ts`, `src/kyc/`

```json
{
  "sandbox_base_url": "https://testapi.smileidentity.com",
  "job_types": {
    "1": "Biometric KYC — updates kycStatus",
    "2": "SmartSelfie Auth — step-up only",
    "4": "SmartSelfie Register",
    "11": "Document Verification CG only"
  },
  "rest_flow": ["upload-url", "ZIP base64", "upload-zip", "webhook"]
}
```

### Webhook Smile ID

```json
{
  "path": "POST /webhooks/smile-id",
  "auth": "HMAC signature ±5 min anti-replay",
  "event_key": "{job_id} or smile:{userId}:{timestamp}:{signature}",
  "verified": "job_success true",
  "rejected": "job_success false"
}
```

---

## 3. Onafriq (ONAFRIQ)

* **Type** : Cartes virtuelles XAF  
* **Fichiers source** : `src/providers/onafriq.service.ts`

```json
{
  "auth": "OAuth2 client_credentials /idp/connect/token",
  "defaults": { "country": "CM", "phone": "237", "city": "Douala", "currency": "XAF" },
  "register": "POST /rest/api/v1/accounts/personalized"
}
```

### Webhook Onafriq (statuts carte)

```json
{
  "freeze": ["IA", "LC", "SC", "DEACTIVATED", "EX", "INACTIVE", "LOSTORSTOLEN"],
  "active": ["AC"],
  "http_resilience": { "timeout_ms": 10000, "retry_count": 2, "backoff_ms": 400 }
}
```

---

## 4. Bridge API (BRIDGE)

* **Type** : Open Banking sandbox  
* **Fichiers source** : `src/providers/bridge-payments.service.ts`

```json
{
  "base_url": "https://api.bridgeapi.io",
  "sandbox_bank_id": "574",
  "currency": "EUR",
  "success_status": "ACSC"
}
```

### Webhook Bridge

```json
{
  "path": "POST /webhooks/bridge/payments",
  "auth": "bridgeapi-signature HMAC-SHA256",
  "event_key": "bridge:payments:{type}:{paymentRequestId}:{status}",
  "success": ["ACSC"],
  "failed": ["RJCT", "CANC", "CANCELLED", "CANCELED"]
}
```

---

## 5. Airtel Money (AIRTEL) — NON IMPLÉMENTÉ

```json
{
  "status": "schema_only",
  "enum_exists": ["CASH_IN_AIRTEL", "PaymentProvider.AIRTEL"],
  "service_in_src": false,
  "warning": "Do NOT generate Airtel integration code — see project-roadmap.md"
}
```

→ Spec marché (NON IMPLÉMENTÉ) : [airtel-money-specs-draft.md](../../90-codebase-constraints/airtel-money-specs-draft.md)

---

## 6. Twilio (SMS OTP)

```json
{
  "production_required": true,
  "message_template": "Votre code de verification est: {code}",
  "otp_never_in_api_response_prod": true
}
```
