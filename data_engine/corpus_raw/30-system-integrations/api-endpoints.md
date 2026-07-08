# Interface — Référence API REST

> **Couche** : `30-system-integrations` · **Surface HTTP** exposée par la plateforme  
> **Source** : controllers NestJS, Postman collection

## Contexte

Cette couche documente **ce que la plateforme expose** — distincte des adapters (ce qu'elle consomme) et des use cases (comment orchestrer).

Auth par défaut : `Authorization: Bearer {JWT}` sauf endpoints publics et webhooks.

## Contrat — Auth

```json
{
  "public": [
    "POST /auth/otp/request",
    "POST /auth/otp/verify",
    "POST /auth/pin/verify",
    "POST /auth/pin/reset/request",
    "POST /auth/pin/reset/verify"
  ],
  "jwt_required": ["/wallets/*", "/payments/*", "/kyc/*", "/virtual-cards"]
}
```

## Contrat — Payments (JWT + KYC VERIFIED)

```json
{
  "POST /payments/deposit/momo": { "body": { "amountFcfa": "integer > 0" } },
  "POST /payments/withdraw/momo": { "body": { "amountFcfa": "integer > 0" } },
  "POST /payments/deposit/bridge": { "body": { "amountFcfa": "integer > 0" } },
  "GET /payments/deposit/momo/:referenceId/status": {},
  "GET /payments/withdraw/momo/:referenceId/status": {}
}
```

## Contrat — KYC (JWT)

```json
{
  "POST /kyc/start": {},
  "POST /kyc/biometric/upload-url": {},
  "POST /kyc/biometric/upload-zip": {},
  "POST /kyc/document-verification/upload-url": { "country": "CG only" },
  "POST /kyc/smartselfie/auth/upload-url": {},
  "POST /kyc/smartselfie/confirm": {},
  "POST /kyc/utils/job-status": { "jobType": "1|2|4|11" }
}
```

## Contrat — Wallets & Cartes

```json
{
  "GET /wallets": {},
  "GET /wallets/:walletId": {},
  "GET /wallets/:walletId/transactions": {},
  "POST /virtual-cards": { "body": { "walletId": "string", "amountFcfa": "integer" } }
}
```

## Montants exemple (tests)

```json
{
  "momo_deposit_fcfa": 5000,
  "momo_withdraw_fcfa": 1000,
  "virtual_card_fcfa": 3000
}
```

## Voir aussi

- [Webhooks](../20-backend-api/input-boundaries/webhook-security.md)
- [Use cases](../35-business-flows/)
