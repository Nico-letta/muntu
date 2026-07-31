# Legacy Knowledge — 07-api-endpoints

```json
{
  "title": "Référence API AfriWallet — Endpoints complets",
  "version": "1.0.0",
  "base_url": "http://localhost:3000",
  "swagger": "/docs",
  "endpoints": {
    "public": [
      { "method": "GET", "path": "/", "description": "Health hello" },
      { "method": "GET", "path": "/users/health", "response": { "status": "ok" } },
      { "method": "POST", "path": "/users/register", "description": "Inscription directe legacy (bypass OTP)" },
      { "method": "POST", "path": "/users/lookup", "description": "Recherche utilisateur par téléphone" }
    ],
    "auth": [
      { "method": "POST", "path": "/auth/otp/request", "body": { "phoneNumber": "string" }, "throttle": "5/min/IP", "description": "OTP activation nouveau compte" },
      { "method": "POST", "path": "/auth/otp/verify", "body": { "phoneNumber": "string", "otp": "string", "pin": "string" }, "returns": "user + wallets + accessToken" },
      { "method": "POST", "path": "/auth/pin/verify", "body": { "phoneNumber": "string", "pin": "string" }, "returns": "user + accessToken" },
      { "method": "POST", "path": "/auth/pin/reset/request", "description": "OTP reset PIN compte existant" },
      { "method": "POST", "path": "/auth/pin/reset/verify", "body": { "phoneNumber", "otp", "pin" }, "description": "Nouveau PIN après OTP" }
    ],
    "kyc": [
      { "method": "POST", "path": "/kyc/start", "auth": "JWT", "description": "Ouvre session KYC PENDING" },
      { "method": "POST", "path": "/kyc/signature", "description": "Signature SDK Smile ID client" },
      { "method": "POST", "path": "/kyc/biometric", "auth": "JWT", "description": "Biometric KYC direct base64" },
      { "method": "POST", "path": "/kyc/biometric/upload-url", "auth": "JWT", "description": "Étape 1 REST — URL upload S3" },
      { "method": "POST", "path": "/kyc/biometric/upload-zip", "auth": "JWT", "description": "Étape 2 REST — upload ZIP base64" },
      { "method": "POST", "path": "/kyc/smartselfie/auth", "auth": "JWT", "description": "SmartSelfie auth direct" },
      { "method": "POST", "path": "/kyc/smartselfie/auth/upload-url", "auth": "JWT" },
      { "method": "POST", "path": "/kyc/smartselfie/register/upload-url", "auth": "JWT" },
      { "method": "POST", "path": "/kyc/smartselfie/upload-zip", "auth": "JWT" },
      { "method": "POST", "path": "/kyc/smartselfie/confirm", "auth": "JWT", "description": "Polling + persist SmartSelfie DB" },
      { "method": "POST", "path": "/kyc/document-verification", "auth": "JWT", "country": "CG only" },
      { "method": "POST", "path": "/kyc/document-verification/upload-url", "auth": "JWT" },
      { "method": "POST", "path": "/kyc/document-verification/upload-zip", "auth": "JWT" },
      { "method": "POST", "path": "/kyc/utils/job-status", "auth": "JWT", "body": { "jobId": "string", "jobType": "1|2|4|11" } },
      { "method": "POST", "path": "/kyc/utils/id-number-rate-limit-reset", "auth": "JWT", "description": "Reset rate limit Smile ID sandbox" }
    ],
    "wallets": [
      { "method": "GET", "path": "/wallets", "auth": "JWT", "description": "Liste wallets user" },
      { "method": "GET", "path": "/wallets/:walletId", "auth": "JWT", "description": "Détail + solde FCFA" },
      { "method": "GET", "path": "/wallets/:walletId/transactions", "auth": "JWT", "description": "Historique transactions desc" }
    ],
    "payments": [
      { "method": "POST", "path": "/payments/deposit/momo", "auth": "JWT", "body": { "amountFcfa": "integer > 0" }, "prerequisite": "KYC VERIFIED" },
      { "method": "POST", "path": "/payments/withdraw/momo", "auth": "JWT", "body": { "amountFcfa": "integer > 0" }, "prerequisite": "KYC VERIFIED + solde" },
      { "method": "POST", "path": "/payments/deposit/bridge", "auth": "JWT", "body": { "amountFcfa": "integer > 0" }, "prerequisite": "KYC VERIFIED" },
      { "method": "GET", "path": "/payments/deposit/momo/:referenceId/status", "auth": "JWT", "description": "Polling statut dépôt MoMo" },
      { "method": "GET", "path": "/payments/withdraw/momo/:referenceId/status", "auth": "JWT", "description": "Polling statut retrait MoMo" },
      { "method": "GET", "path": "/payments/deposit/bridge/:paymentRequestId/status", "auth": "JWT", "description": "Polling statut dépôt Bridge" }
    ],
    "virtual_cards": [
      { "method": "POST", "path": "/virtual-cards", "auth": "JWT", "body": { "walletId": "string", "amountFcfa": "integer" }, "prerequisite": "KYC VERIFIED + solde" }
    ],
    "webhooks": [
      { "method": "POST", "path": "/webhooks/mtn/requesttopay/:referenceId", "auth": "IP allowlist optional", "description": "Callback MTN MoMo" },
      { "method": "PUT", "path": "/webhooks/mtn/requesttopay/:referenceId", "description": "Alias POST MTN" },
      { "method": "POST", "path": "/webhooks/smile-id", "auth": "HMAC signature", "description": "Callback KYC Smile ID" },
      { "method": "POST", "path": "/webhooks/onafriq/cards", "auth": "x-webhook-signature AES256", "description": "Notifications carte Onafriq" },
      { "method": "POST", "path": "/webhooks/bridge/payments", "auth": "bridgeapi-signature HMAC-SHA256", "description": "Callback paiement Bridge" }
    ]
  },
  "auth_header": "Authorization: Bearer {JWT}",
  "jwt_payload": { "sub": "userId", "phoneNumber": "string" },
  "jwt_expiry_default": "15m",
  "example_amounts_fcfa": {
    "momo_deposit": 5000,
    "momo_withdraw": 1000,
    "bridge_deposit": 1000,
    "virtual_card": 3000
  },
  "example_phone": "+237670000000"
}

```
