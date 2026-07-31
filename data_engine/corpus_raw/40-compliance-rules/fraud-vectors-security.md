# Fraud Vectors, Security Threat Modeling & Structural Risks

## Identified Threat Landscape & Vulnerabilities
* **Primary Threat Vectors**: Identity theft, Internal fraud (insider threats), Cyber-fraud, Agent-level fraud.
* **Technical Attack Typologies**: Social Engineering, Man-in-the-Middle (MitM) attacks, Malware deployment.
* **GSM Signaling Weakness**: USSD data transmissions over GSM signaling channels lack native end-to-end encryption (E2EE). Payloads pass through Mobile Network Operator (MNO) infrastructure in cleartext.

## Attack Vector Profile: SIM Swap Fraud
* **Mechanism**: Attackers hijack a subscriber's MSISDN by social engineering an MNO agent into issuing a replacement SIM card, thereby intercepting the USSD session validation path.
* **Mitigation Triggers**:
  * Implement a 24-72 hour cooling period/temporary hold on high-value transactions post SIM swap event flag.
  * Implement strict transaction velocity limits.
  * Mandatory out-of-band SMS notifications for all state-changing actions.

## Session UX Security Implementation Rules
* **PIN Authentication Placement**: Enforce PIN entry strictly at the final confirmation step, never at session initiation (prevents PIN harvest via abandoned sessions).
* **PIN Complexity Policy**: Hard rejection of sequential data (`1234`) or repetitive arrays (`0000`).
* **Menu Masking Rule**: Mask all sensitive data strings (e.g., account numbers, balances) except the last 4 characters within the 160-character menu display.
* **Inactivity Session Drop**: Force automatic state termination after 60 seconds of idle time (network-level timeout maximum is 180 seconds).
* **Two-Factor Authentication (2FA)**: For transactions exceeding defined risk velocity thresholds, process the USSD flow then trigger an out-of-band numeric SMS confirmation token prior to final settlement.
* **B2B / Merchant Security**: Merchant operations require strict verification mapping. Transition to static or dynamic QR Code generation to mitigate errors in recipient input (`Merchant ID` + `Merchant Name` matching array).
* **Cross-Channel Consistency**: Transactions validation sequences must bind across client agents (`MoMo App`, `Merchant App`, `Agent App`) and offline interfaces (`USSD Protocol`).

## MoMo Documentation Security Mapping
* **Access Control**: The provided documentation frames Subscription Key, API User, and API Key as the core access-control mechanism for the MoMo API surface.
* **Provisioning Control**: API user and API key creation is positioned as a formal provisioning step after onboarding and subscription.
* **Consent & Authorization**: Pre-approval is explicitly tied to the MoMo PIN and acceptance of terms and conditions, making user authorization a first-class control.
* **Validation Loop**: Transaction status, balance checks, and user-status validation are treated as asynchronous verification steps rather than blind execution.
* **Callback Discipline**: The documented lifecycle expects callback-based state updates, which should be treated as a security-sensitive integration boundary.

## Institutional Governance Friction
* **Supplier Perspective**: >70% of Mobile Money providers rate law enforcement agencies as ineffective.
* **Root Causes**: Lack of technical/forensic skills, insufficient resources, corruption.
* **Authentication Gap**: ~50% of active mobile money users in Sub-Saharan Africa do not have a password or PIN protecting their account assets (World Bank Global Findex 2025).

## Regulatory Charging & Clearing Models (Nigeria Case Study)
* **Pricing Resolution (February 2026)**: Resolution of the N300 billion bank-telco access fee dispute.
* **Regulated Session Cost**: End-user access fee fixed at N6.98 per 120-second USSD session (ALTON / Central Bank regulations).

## Financial Inclusion Fault-lines (Ecosystem & Usage Gaps)
```json
{
  "gender_gap_stagnation": {
    "senegal": {
      "male_account_penetration": "Nearly universal",
      "female_exclusion_rate": 0.25
    },
    "nigeria": {
      "gender_gap_2023": 0.46,
      "gender_gap_2024": 0.41
    }
  },
  "advanced_transaction_disparities": {
    "senegal_salary_receive_rate": { "male": 0.16, "female": 0.05 },
    "nigeria_client_payment_receive_rate": { "male": 0.41, "female": 0.25 },
    "kenya_merchant_payment_usage": { "male": 0.66, "female": 0.50 }
  }
}
