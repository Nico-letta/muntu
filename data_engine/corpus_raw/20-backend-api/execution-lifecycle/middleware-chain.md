# Cycle de vie — Chaîne Middleware & Guards

> **Couche** : `20-backend-api/execution-lifecycle` · **Axe** : req/res typé  
> **Stack** : NestJS JWT, JwtAuthGuard  
> **Source** : `src/auth/jwt.strategy.ts`, `src/auth/jwt-auth.guard.ts`

## Contexte

AfriWallet injecte `{ userId, phoneNumber }` via JWT après OTP/PIN. Les routes sensibles exigent **JwtAuthGuard** + souvent **KYC VERIFIED** côté service.

## Contrat — JWT

```json
{
  "header": "Authorization: Bearer {token}",
  "payload": { "sub": "userId", "phoneNumber": "string" },
  "expiry_default": "15m",
  "secret_env": "JWT_SECRET"
}
```

## Contrat — Routes publiques vs protégées

```json
{
  "public_auth": [
    "POST /auth/otp/request",
    "POST /auth/otp/verify",
    "POST /auth/pin/verify",
    "POST /auth/pin/reset/request",
    "POST /auth/pin/reset/verify"
  ],
  "jwt_required": [
    "/wallets/*",
    "/payments/*",
    "/kyc/*",
    "/virtual-cards"
  ],
  "webhooks_public_signed": [
    "/webhooks/mtn/*",
    "/webhooks/smile-id",
    "/webhooks/onafriq/*",
    "/webhooks/bridge/*"
  ]
}
```

## Contrat — Guards métier (service layer)

```json
{
  "kyc_verified_required": [
    "POST /payments/deposit/momo",
    "POST /payments/withdraw/momo",
    "POST /payments/deposit/bridge",
    "POST /virtual-cards"
  ],
  "check": "user.kycStatus === VERIFIED else BadRequestException"
}
```

## Throttling

```json
{
  "otp_endpoints": "5 requests/minute/IP",
  "auth_module_global": "120 requests/minute"
}
```

## Voir aussi

- `20-backend-api/input-boundaries/payload-validation.md`
- `30-system-integrations/api-endpoints.md`
