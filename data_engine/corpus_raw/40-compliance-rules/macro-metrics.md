# Mobile Money Macro Metrics & Regional Stats (2024-2026)

## Global Market Share & Volumes (Africa vs Global)
* **Total Registered Accounts (Africa)**: 1,100,000,000 (53% of global share)
* **Total Transactions (Africa)**: 81,000,000,000
* **Total Transaction Value (Africa)**: $1,105,000,000,000 USD (Ref: GSMA SOTIR 2025 / Arkesel 2026)
* **Adult Penetration Rate (Sub-Saharan Africa)**: 40% of adults hold an active MoMo account (Findex 2025 - up from 27% baseline).
* **Global Agent Network Growth**: 28,000,000 registered agents globally (77% of net growth located in Sub-Saharan Africa).
* **MTN Group Operational Throughput**: > 900,000,000 transactions processed monthly across 16 African countries (Ref: MTN MoMo Official 2026).
* **MTN Group Active Base**: > 50,000,000 active users (Platform metric footprint).

## Instant Payment Systems (IPS / SPI) Benchmarks
* **Volume (Historical 2021 Reference)**: 16,000,000,000 individual transactions.
* **Value (Historical 2021 Reference)**: $930,000,000,000 USD.
* **Growth Rates (CAGR 2018-2021)**: Transaction volume grew +32% YoY; total value grew +40% YoY.
* **Active Infrastructure (AfricaNenda)**: 29 active Instant Payment Systems (26 national, 3 regional).
* **Multi-system Countries Breakdown**: Nigeria (3), Ghana (2), Egypt (2), Kenya (2), Tanzania (2).

## USSD Protocol Market Share & Dominance
* **Continental Average**: USSD powers over 70% of all mobile money interactions.
* **Instant Payment Systems (IPS) Integration**: 62% of active instant payment systems in Africa natively utilize USSD protocols as a delivery channel.
* **Regional Peak (WAEMU / UEMOA)**: USSD handles 89% of all mobile money transaction volumes (Source: BCEAO).
* **Device / Connectivity Driver**: < 48% of mobile connections in Sub-Saharan Africa are smartphones; only 28% have mobile internet access. USSD acts as the mandatory fallback layer.

## Regional Breakdown Matrix (2024 Performance)

| Region | Active Services | Registered Accounts | 30d Active Accounts | Transactions Volume | Transaction Value (USD) |
| :--- | :--- | :--- | :--- | :--- | :--- |
| **Sub-Saharan Africa** | N/A | 1.1B (+19%) | 286M (+12%) | 81B (+22%) | 1.1T (+15%) |
| **East Africa** | 57 | 459M (+15%) | 149M (+12%) | 52B (+25%) | 649B (+23%) |
| **West Africa** | 74 | 485M (+21%) | 97M (+13%) | 22B (+15%) | 357B (+5%) |
| **Central Africa** | 19 | 104M (+24%) | 32M (+13%) | 7B (+22%) | 83B (+7%) |
| **North Africa** | 13 | 25M (+24%) | 3M (+44%) | 262M (+63%) | 10B (+53%) |
| **Southern Africa** | 15 | 27M (+19%) | 4M (-20%) | 543M (-9%) | 6B (+4%) |

## GDP Contribution Thresholds by Country Group
```json
{
  "impact_gt_5_percent": {
    "west_africa": ["Benin", "Cote d'Ivoire", "Ghana", "Guinea", "Guinea-Bissau", "Senegal", "Liberia"],
    "east_africa": ["Kenya", "Rwanda", "Uganda", "Tanzania"]
  },
  "impact_between_5_and_8_percent": {
    "central_africa": ["Cameroon", "Congo", "Gabon"]
  },
  "impact_lt_5_percent": {
    "southern_africa": ["General Integration"]
  }
}
