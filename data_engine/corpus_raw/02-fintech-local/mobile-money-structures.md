# Mobile Money Data Structures & Generic Integration Patterns

## 1. Core Domain Objects
- `account_holder`: consumer or merchant identity.
- `wallet`: balance-bearing account attached to a mobile-money provider.
- `transaction`: financial operation with amount, currency, reference, and lifecycle state.
- `party`: payer, payee, merchant, or agent.

## 2. MoMo API Extension Objects (from the provided documentation)
- `product_subscription`: entitlement to a MoMo product such as Remittance, Distribute, Channel as a Service, KYC/Account Validation, Pre-approval, or Notify.
- `api_user`: provisioning identity used to access the API.
- `api_key`: bearer credential issued for API access.
- `subscription_key`: primary or secondary credential used to authenticate the developer account.
- `callback`: asynchronous endpoint used to receive transaction state updates.
- `consent_record`: pre-approval or terms-and-conditions acceptance tied to a MoMo PIN flow.

## 3. Generic Transaction Shape
```json
{
  "amount": 5000,
  "currency": "XOF",
  "payer": {"partyIdType": "MSISDN", "partyId": "22500000000"},
  "payee": {"partyIdType": "MSISDN", "partyId": "22511111111"},
  "reference": "invoice-001",
  "callbackUrl": "https://example.test/callback"
}
```

## 4. MoMo-Oriented Access Envelope
```json
{
  "product": "remittance",
  "subscriptionKey": "primary-or-secondary",
  "apiUser": "partner-api-user",
  "apiKey": "secret-bearer-token",
  "callbackUrl": "https://example.test/callback",
  "party": {
    "partyIdType": "MSISDN",
    "partyId": "22500000000"
  }
}
```

## 5. Party Identifier Types
- `MSISDN`
- `EMAIL`
- `PARTY_CODE`
- `ACCOUNT_ID`

## 6. Lifecycle States
- `PENDING`
- `SUCCESSFUL`
- `FAILED`
- `REJECTED`
- `EXPIRED`
- `ONGOING`

## 7. Design Principles
- Use REST over HTTPS.
- Prefer ISO currency and country codes.
- Keep identifiers flexible because no single global mobile-money account ID exists.
- Allow provider-specific metadata without breaking the baseline schema.
- Separate access management from transaction processing via subscription keys and API user/API key provisioning.

## 8. Generic Use-Case Patterns
- `RequestToPay`: collect a payment from a payer.
- `Transfer`: move funds from provider to payee.
- `Payment`: merchant or bill payment flow.
- `Preapproval`: recurring authorization granted once and reused later.
- `Notify`: send customized SMS notifications tied to transaction activity.
