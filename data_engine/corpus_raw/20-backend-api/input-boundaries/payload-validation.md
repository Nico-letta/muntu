# Frontières d'entrée — Validation des Payloads

> **Couche** : `20-backend-api/input-boundaries` · **Axe** : Entrée → typage strict  
> **Stack** : NestJS 11, class-validator, class-transformer  
> **Source** : `src/kyc/kyc.controller.ts`, `src/kyc/smile-id-id-rules.ts`, `src/auth/auth.controller.ts`

## Contexte (Contract-Driven)

Les bugs critiques naissent aux **frontières** : une donnée externe non typée pénètre l'application. AfriWallet valide **avant** tout appel provider (MTN, Smile ID, Onafriq).

Le LLM ne doit pas inventer des formats d'ID africains — il applique les regex ci-dessous.

## KYC — Validations globales

```json
{
  "country": { "regex": "^[A-Z]{2}$", "format": "ISO 3166-1 alpha-2" },
  "dob": { "regex": "^\\d{4}-\\d{2}-\\d{2}$", "format": "yyyy-mm-dd" },
  "idNumber": { "max_length": 32 }
}
```

## KYC — Nigeria (NIN) — contrat strict

```json
{
  "NG": {
    "NIN": { "regex": "^\\d{11}$" },
    "NIN_V2": { "regex": "^\\d{11}$" },
    "BVN": { "regex": "^\\d{11}$" },
    "BANK_ACCOUNT": { "regex": "^\\d{10}$", "required_fields": ["bankCode"] },
    "V_NIN": { "regex": "^[A-Za-z0-9]{16}$" }
  }
}
```

## KYC — SmartSelfie reason (enum strict)

```json
{
  "smartselfie_auth_reasons": [
    "large_withdrawal",
    "pin_reset",
    "high_risk_device",
    "wallet_recovery"
  ],
  "validation": "@IsIn decorator — toute autre valeur = BadRequestException"
}
```

## Paiements — Montants

```json
{
  "amountFcfa": {
    "type": "integer",
    "rule": "must be > 0",
    "storage": "BigInt in PostgreSQL — never float"
  }
}
```

## Auth — OTP / PIN

```json
{
  "otp": { "length": 6, "ttl_minutes": 5, "max_attempts": 3 },
  "pin": { "required_on_verify": true, "stored": "bcrypt hash only" },
  "phoneNumber": { "required": true, "format": "international MSISDN" }
}
```

## Règle impérative

Validation échouée → **BadRequestException** avant tout side-effect (pas de transaction PENDING, pas d'appel MTN).

## Voir aussi

- `40-compliance-rules/kyc-id-rules-by-country.md`
- `20-backend-api/input-boundaries/webhook-security.md`
