# Regional Governance — Index Multi-Zone

> **Couche** : `40-compliance-rules` · **Ne pas fusionner les zones** — le modèle hallucine si NG, CM et CI sont mélangés.

## Matrice réglementaire (sectorisation v4)

| Fichier | Zone | Devise | Pays clés |
|---------|------|--------|-----------|
| [cemac-cobac.md](./cemac-cobac.md) | CEMAC / BEAC / COBAC | XAF | CM, CG |
| [uemoa-bceao.md](./uemoa-bceao.md) | UEMOA / BCEAO | XOF | CI |
| [cbn-nigeria.md](./cbn-nigeria.md) | Nigeria / CBN / NIMC | NGN | NG |

```json
{
  "rule": "Toujours résoudre ISO pays + devise AVANT d'appliquer regex KYC ou OpCo MTN",
  "kyc_detail": "kyc-id-rules-by-country.md",
  "async_flows": "../30-system-integrations/async-reconciliation-patterns.md"
}
```

## Product Governance Model (MTN Developer)
- The provided MoMo documentation organizes the platform around distinct products: Remittance, Distribute, Channel as a Service, KYC/Account Validation, Pre-approval, and Notify.
- Each product is presented as a separate capability surface, which makes it suitable for a modular training corpus.

## 2. Onboarding & Access Management
- Developers must sign up for an account before accessing the MoMo API ecosystem.
- Account activation is delivered by email and has a limited validity window.
- Developers subscribe to products through the developer portal.
- Each product subscription can expose a Primary Key and a Secondary Key.
- API User and API Key are provisioned as a separate step after subscription.

## 3. Identity, Consent & Customer Controls
- KYC information can be requested to simplify customer onboarding.
- Pre-approval is explicitly tied to the MoMo PIN and customer acceptance of terms and conditions.
- Consent and authorization should be treated as explicit business controls rather than implicit workflow steps.

## 4. Operational Lifecycle
- Sandbox provisioning is the documented path for initial API user and key creation.
- Transaction lifecycle checks include status retrieval, balance retrieval, and user-status validation.
- Callback-based state updates are part of the expected integration flow.

## 5. Structured Representation
```json
{
  "onboarding": ["signup", "product_subscription", "subscription_key_management"],
  "access_control": ["api_user", "api_key", "primary_key", "secondary_key"],
  "customer_controls": ["kyc_validation", "pin_preapproval", "terms_acceptance"],
  "integration_flow": ["sandbox_provisioning", "transaction_status_check", "balance_check", "callback_handling"]
}
```

## 6. Operator-specific USSD Integrations (Airtel example)
- **USSD entrypoints** are operator-specific and must be modeled as integration parameters (`ussd_code`, `menu_path`, `timeout_seconds`).
- **Bank partnerships & interconnect**: model partner lists and fee matrices per country and per bank to avoid hardcoding rules in training data.
- **Cash-out constraints**: include withdrawal constraints (e.g., multiples of 5 000, SMS code expiry) as structured fields rather than prose to save tokens.
- **Support & escalation metadata**: include `support_number`, `support_email`, and `call_tariff` for operational playbooks.