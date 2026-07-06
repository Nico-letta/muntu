# Telecom Operator Specifications & Financial Volumes (2024-2026)

## Protocol Layer Specifications
* **Core Transport Protocols**: USSD (Unstructured Supplementary Service Data), STK (SIM Toolkit technology).
* **Network Execution Property**: Session-oriented, real-time GSM signaling channel connection. Internet connectivity/data balance not required (Zero Data Cost delivery).
* **Interface Limits**: Maximum payload length per menu string is 160 characters. Session hardware timeout hard limit: 180 seconds. Target transaction flow completion limit: < 5 steps, < 30 seconds execution window.

## 1. Safaricom / Vodacom Group (M-PESA)
* **Shortcode Interface**: Dial `*334#` (Kenya Core).
* **Footprint**: 7 African markets (Kenya, Tanzania, Mozambique, DRC, Ghana, Egypt, Ethiopia).
* **Total Scale**: 66,200,000 active users.
* **Annual Throughput**: 28,000,000,000 individual transactions processing KES 40 trillion (~$309B to $314B USD annual value).
* **Agent Infrastructure**: 381,000 registered physical cash-in/cash-out nodes in Kenya.

## 2. MTN Group (MTN MoMo)
* **Shortcode Interface (Ghana Example)**: Dial `*170#`.
* **Footprint**: 14 out of 16 African markets.
* **Fintech Organization Matrix**: Managed by MTN Fintech / FinCos (Unified workforce of > 900 specialized fintech professionals).
* **Legal status / Compliance**: Operates via MTN (PTY) LTD, an authorized Financial Service Provider (FSP License: 44774).
* **Ecosystem Segmentation**:
  * **Consumer**: Airtime/bundles, bill payments (municipal, schools, DStv), savings, short-term loans, online shopping via MoMoPay.
  * **Business**: Bulk disbursements (payroll, suppliers), QR Code collection, remote invoice collection.
  * **Agents**: Cash-In / Cash-Out routing, cash-to-digital facilitation, multi-tier commission architecture.

## 3. MoMo API Product Catalog (from the provided documentation)
* **Remittance**: secure cross-border money transfers directly to a recipient's MoMo wallet.
* **Distribute**: enable businesses to distribute MTN and MoMo services, including cash-in, cash-out, and airtime sales.
* **Channel as a Service**: expose a sub-menu inside MoMo USSD and app channels for partner services.
* **KYC / Account Validation**: provide KYC information to simplify customer onboarding.
* **Pre-approval**: use the MoMo PIN to contract with customers and accept terms and conditions.
* **Notify**: send customized SMS notifications within payment or collection flows.

## 4. MoMo API Access Lifecycle
1. `Create Sandbox User` (initial verification stub)
2. `Generate API Key` (bearer credential generation)
3. `Request To Pay` (inbound collection push)
4. `Get Transaction Status` and `Get Account Balance` (asynchronous validation loop)
5. `Check User Status` (KYC compliance and wallet validation check)

## 5. Authentication & Key Management
* **Credentials**: Subscription Key plus API User and API Key.
* **Key Model**: each product can expose a Primary Key and a Secondary Key.
* **Provisioning**: API user and API key are provisioned through the Sandbox Provisioning API.
* **Subscription State**: subscriptions are stored under the developer profile and remain available until changed.

## 6. Integration Stack Blueprint
```json
{
  "api_integration_type": "REST_API_over_HTTPS",
  "mtn_momo_api_modules": {
    "collection": { "use_case": "Remote automatic collection of bills, fees, taxes" },
    "disbursement": { "use_case": "Automated multi-wallet deposit for payroll or suppliers" },
    "collection_widget": { "use_case": "Web-based checkout via dynamic QR code scanning" },
    "remittances": { "use_case": "Diaspora-to-local automated cross-border fund distribution" }
  },
  "supported_use_cases": {
    "P2P_transfer": { "typical_flow": "*shortcode# -> select_recipient -> input_amount -> pin_auth" },
    "merchant_payment": { "global_volume_2024_usd": 105000000000 },
    "bill_payment": { "global_volume_2024_usd": 93000000000 },
    "bulk_disbursement": { "global_volume_2024_usd": 97000000000 },
    "micro_loans": { "execution": "instant_credit_scoring_and_wallet_deposit" },
    "savings_deposits": { "execution": "microfinance_group_wallets" }
  }
}
```

## 7. Equity Bank
* **Shortcode Interface**: Dial `*247#` (Cross-network routing: Safaricom, Airtel, Telkom, Equitel).
* **Operational Velocity**: Migrated 4,000,000+ customers to mobile USSD banking in under 20 days via EazzyPay platform infrastructure. Onboarded 60,000+ active merchants.

## 8. Airtel Africa (Airtel Money)
* **Footprint**: 14 African markets.
* **Active Users**: 38,000,000 clients (+20.7%).
* **Revenue**: $837,000,000 USD in 2024.

## 9. Cross-Border & Interoperability Architecture
* **Cross-Border Clearing Rails**: PAPSS (Pan-African Payment and Settlement System) connecting over 160 commercial banks for local-currency instant settlement.
* **Regional Integrations**: 2026 Pesalink-PAPSS partnership enabling real-time local currency routing across 80+ banks, fintechs, and SACCO networks in East Africa.
* **Ghana Interoperability (MMI)**: Interoperable transactions grew +87% (from GHS 3.1B to GHS 5.8B). Total Ghana ecosystem scale reached 74,100,000 registered accounts for 34,000,000 population (multi-SIM density).