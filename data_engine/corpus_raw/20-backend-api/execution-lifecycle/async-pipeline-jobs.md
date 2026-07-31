# Cycle de vie — Pipelines Asynchrones (MoMo, KYC, Bridge)

> **Couche** : `20-backend-api/execution-lifecycle` · **Axe** : Entrée validée → état PENDING → finalisation  
> **Source** : `src/payments/payments.service.ts`, `src/providers/mtn.service.ts`

## Contexte

Mobile Money africain est **async by design**. HTTP 202 ≠ succès.

> **Référence canonique** : `30-system-integrations/async-reconciliation-patterns.md` (machine à états, golden snippets, edge cases).

## Flux cash-in MoMo (RequestToPay) — résumé

```json
{
  "steps": [
    "1. Validate KYC VERIFIED + amountFcfa > 0",
    "2. MTN POST /collection/v1_0/requesttopay → HTTP 202",
    "3. Create Transaction CASH_IN_MOMO PENDING, providerTxId = referenceId UUID",
    "4. Client confirms on phone",
    "5. Webhook OR polling → SUCCESS credits wallet"
  ],
  "never": "Credit wallet before SUCCESSFUL/SUCCESS status"
}
```

## Flux cash-out MoMo (Disbursement + compensation)

```json
{
  "steps": [
    "1. Validate balance >= amount",
    "2. Decrement wallet IMMEDIATELY (reservation)",
    "3. MTN POST /disbursement/v1_0/transfer",
    "4. SUCCESS → finalize | FAILED → re-credit full amount"
  ],
  "critical_pattern": "compensation on FAILED/REJECTED"
}
```

## Contrat — Polling fallback (si pas de callback)

```json
{
  "intervals_ms": {
    "CREA": 2000,
    "ACTC": 2000,
    "PDNG": 10000,
    "PENDING": 10000,
    "default": 30000
  },
  "endpoints": {
    "momo_deposit": "GET /payments/deposit/momo/:referenceId/status",
    "momo_withdraw": "GET /payments/withdraw/momo/:referenceId/status",
    "bridge": "GET /payments/deposit/bridge/:paymentRequestId/status"
  }
}
```

## Contrat — Statuts normalisés

```json
{
  "success": ["SUCCESSFUL", "SUCCESS", "ACSC"],
  "failed": ["FAILED", "REJECTED", "RJCT", "CANC", "CANCELLED"],
  "pending": ["CREA", "ACTC", "PDNG", "PENDING", "UNKNOWN"]
}
```

## KYC async (Smile ID)

```json
{
  "flow": "upload-url → ZIP → upload-zip → webhook job_success",
  "kyc_status": {
    "PENDING": "session open",
    "VERIFIED": "job_success true",
    "REJECTED": "job_success false"
  }
}
```

## Voir aussi

- `30-system-integrations/provider-specs.md`
- `35-business-flows/afriwallet-business-flows.md`
