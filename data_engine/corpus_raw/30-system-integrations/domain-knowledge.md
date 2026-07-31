# Domain Knowledge — Vocabulaire, Zones & Structures MoMo

> **Couche** : `30-system-integrations` · **Fichier fusionné** (ex-glossary, geographic-zones, mobile-money-structures)  
> **Expert MoE** : vocabulaire transversal + géographie + objets MoMo génériques

---

## 1. Glossaire Fintech Africaine

| Terme | Définition | Piège LLM occidental |
|-------|------------|----------------------|
| **FCFA / XAF** | Franc CFA CEMAC, montants **BigInt entiers** | Centimes EUR/USD |
| **MoMo** | MTN Mobile Money via MSISDN | Paiement sync Stripe |
| **RequestToPay** | Collection MTN cash-in async HTTP 202 | SUCCESS immédiat |
| **Disbursement** | Transfer cash-out + réservation solde | Oublier compensation |
| **KYC légal** | `kycStatus` VERIFIED/REJECTED | Confondre SmartSelfie |
| **SmartSelfie** | Step-up biométrique décorrélé | Remplace KYC |
| **OpCo** | `mtncameroon`, `mtnnigeria`, etc. | `sandbox` en prod |
| **Idempotence** | `providerTxId`, `eventKey` | Double crédit webhook |

```json
{
  "PaymentProvider": {
    "coded_in_src": ["MTN_MOMO", "BRIDGE", "ONAFRIQ", "SMILE_ID"],
    "schema_only": ["AIRTEL"]
  },
  "TransactionType": {
    "CASH_IN_MOMO": "coded",
    "CASH_OUT_MOMO": "coded",
    "CARD_ISSUANCE_FEE": "coded",
    "ADJUSTMENT": "coded",
    "CASH_IN_AIRTEL": "schema_only",
    "CARD_PAYMENT": "schema_only",
    "CARD_REFUND": "schema_only"
  }
}
```

---

## 2. Zones Géographiques

| Zone | ISO | Régulateur | Pays corpus |
|------|-----|------------|-------------|
| CEMAC | XAF | BEAC, COBAC | CM, CG |
| UEMOA | XOF | BCEAO | CI, SN, BF… |

```json
{
  "biometric_kyc_countries": ["CI", "GH", "KE", "NG", "ZA", "UG", "ZM", "ZW"],
  "document_verification_only": { "CG": true },
  "not_in_biometric_registry": { "CM": "Onafriq defaults +237 Douala XAF" },
  "mtn_opcos_prod": ["mtnnigeria", "mtncameroon", "mtncongo"],
  "sandbox_currency": "EUR",
  "prod_currency": "XAF"
}
```

---

## 3. Structures Mobile Money Génériques

### Objets domaine

- `account_holder`, `wallet`, `transaction`, `party` (payer/payee)
- `api_user`, `api_key`, `subscription_key`, `callback`, `consent_record`

### Transaction shape générique

```json
{
  "amount": 5000,
  "currency": "XOF",
  "payer": {"partyIdType": "MSISDN", "partyId": "22500000000"},
  "reference": "invoice-001",
  "callbackUrl": "https://example.test/callback"
}
```

### Party ID types

`MSISDN` · `EMAIL` · `PARTY_CODE` · `ACCOUNT_ID`

### Lifecycle states

`PENDING` · `SUCCESSFUL` · `FAILED` · `REJECTED` · `EXPIRED` · `ONGOING`

### Patterns use-case

- `RequestToPay` — collect payment
- `Transfer` — disburse to payee
- `Preapproval` — recurring MoMo PIN authorization
- `Notify` — SMS post-transaction

## Voir aussi

- `../40-compliance-rules/kyc-id-rules-by-country.md` — regex ID par pays
- `provider-specs.md` — intégrations AfriWallet
- `../40-compliance-rules/` — régulation marché (COBAC, fraude)
