# Legacy Knowledge — 02-glossary

```json
{
  "title": "Glossaire Fintech Africaine",
  "version": "1.0.0",
  "terms": [
    {
      "term": "FCFA",
      "aliases": [
        "XAF",
        "Franc CFA"
      ],
      "definition": "Devise du wallet AfriWallet en entiers BigInt. XAF = zone CEMAC.",
      "context": "Onafriq cardCurrency XAF"
    },
    {
      "term": "MoMo",
      "aliases": [
        "Mobile Money",
        "MTN MoMo"
      ],
      "definition": "Paiement mobile MTN. Collection (cash-in) et Disbursement (cash-out) via MSISDN.",
      "context": "Provider MTN_MOMO"
    },
    {
      "term": "RequestToPay",
      "definition": "API MTN collection — débit MoMo client → crédit wallet. Async, HTTP 202.",
      "context": "POST /collection/v1_0/requesttopay"
    },
    {
      "term": "Disbursement",
      "definition": "API MTN transfer — crédit MoMo client depuis wallet. Réservation solde immédiate.",
      "context": "POST /disbursement/v1_0/transfer"
    },
    {
      "term": "MSISDN",
      "definition": "Numéro téléphone international = partyId MTN.",
      "example": "+237670000000"
    },
    {
      "term": "OpCo",
      "definition": "Environnement MTN par pays: mtnnigeria, mtncameroon, mtncongo, sandbox.",
      "context": "X-Target-Environment header"
    },
    {
      "term": "KYC",
      "definition": "Vérification identité. Statuts PENDING/VERIFIED/REJECTED via Smile ID.",
      "context": "Obligatoire avant paiements"
    },
    {
      "term": "SmartSelfie",
      "definition": "Step-up biométrique décorrélé du KYC légal.",
      "reasons": [
        "large_withdrawal",
        "pin_reset",
        "high_risk_device",
        "wallet_recovery"
      ]
    },
    {
      "term": "NIN",
      "definition": "National Identification Number Nigeria — 11 chiffres.",
      "country": "NG"
    },
    {
      "term": "BVN",
      "definition": "Bank Verification Number Nigeria — 11 chiffres.",
      "country": "NG"
    },
    {
      "term": "Ghana Card",
      "definition": "ID Ghana: 3 lettres + 9 chiffres + 1 chiffre.",
      "country": "GH"
    },
    {
      "term": "Onafriq",
      "definition": "Émetteur cartes virtuelles XAF. Defaults Cameroun CM/+237/Douala.",
      "context": "CardProvider ONAFRIQ"
    },
    {
      "term": "cardToken",
      "definition": "ID compte carte Onafriq = registrationAccountId.",
      "context": "VirtualCard.cardToken"
    },
    {
      "term": "Idempotence",
      "definition": "Anti-doublon via providerTxId, eventKey, idempotencyKey.",
      "context": "Critique webhooks"
    },
    {
      "term": "Compensation cash-out",
      "definition": "Recrédit wallet si retrait MoMo FAILED/REJECTED.",
      "context": "Pattern fintech essentiel"
    },
    {
      "term": "CEMAC",
      "definition": "Afrique Centrale — XAF. CM, CG, GA, TD, GQ, CF.",
      "context": "AfriWallet defaults CM"
    },
    {
      "term": "UEMOA",
      "definition": "Afrique de l'Ouest — XOF. CI supporté KYC.",
      "context": "8 pays dont CI, SN"
    }
  ]
}
```
