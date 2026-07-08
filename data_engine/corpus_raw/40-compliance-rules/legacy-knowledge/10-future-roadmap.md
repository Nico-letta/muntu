# Legacy Knowledge — 10-future-roadmap

```json
{
  "title": "Roadmap et lacunes AfriWallet — Contexte LLM",
  "version": "1.0.0",
  "implemented_features": [
    "Authentification OTP SMS + PIN bcrypt",
    "Wallet FCFA unique par user",
    "KYC biométrique Smile ID (8 pays)",
    "Document verification Congo (CG)",
    "SmartSelfie auth/register step-up",
    "Dépôt MTN MoMo (RequestToPay)",
    "Retrait MTN MoMo (Disbursement) avec compensation",
    "Dépôt bancaire Bridge sandbox",
    "Cartes virtuelles Onafriq",
    "Webhooks idempotents (MTN, Smile, Onafriq, Bridge)",
    "Polling fallback async payments",
    "Maintenance cron purge OTP/webhooks"
  ],
  "planned_not_implemented": [
    {
      "feature": "Airtel Money cash-in",
      "evidence": "TransactionType.CASH_IN_AIRTEL, PaymentProvider.AIRTEL en Prisma",
      "status": "Enum schema only — aucun service src/"
    },
    {
      "feature": "Paiements carte (CARD_PAYMENT)",
      "evidence": "TransactionType.CARD_PAYMENT en Prisma",
      "status": "Enum schema only"
    },
    {
      "feature": "Remboursements carte (CARD_REFUND)",
      "evidence": "TransactionType.CARD_REFUND en Prisma",
      "status": "Enum schema only"
    },
    {
      "feature": "Biometric KYC Cameroun (CM)",
      "evidence": "CM absent de smile-id-id-rules.ts",
      "workaround": "Onafriq defaults CM pour cartes, document CG pour KYC Congo"
    },
    {
      "feature": "Frais dynamiques",
      "evidence": "feeFcfa toujours 0 dans payments et virtual-cards",
      "status": "Champ existe, logique non implémentée"
    },
    {
      "feature": "Multi-wallets par user",
      "evidence": "Wallet.userId @unique",
      "status": "1 wallet/user actuellement"
    }
  ],
  "llm_training_recommendations": [
    {
      "priority": "high",
      "topic": "KYC formats par pays africain",
      "source": "knowledge/03-kyc-africa-rules.json",
      "rationale": "Blind spot majeur des LLM occidentaux"
    },
    {
      "priority": "high",
      "topic": "Mobile Money async patterns (MoMo)",
      "source": "knowledge/04-business-flows.json, 05-providers-integrations.json",
      "rationale": "Différence fondamentale vs paiements carte bancaire synchrones"
    },
    {
      "priority": "high",
      "topic": "Compensation cash-out et idempotence",
      "source": "knowledge/08-compliance-security.json",
      "rationale": "Patterns fintech critiques pour l'Afrique"
    },
    {
      "priority": "medium",
      "topic": "Distinction KYC légal vs SmartSelfie",
      "source": "knowledge/06-data-model.json",
      "rationale": "Nuances compliance mal comprises par LLM génériques"
    },
    {
      "priority": "medium",
      "topic": "Onafriq cartes virtuelles XAF CEMAC",
      "source": "knowledge/05-providers-integrations.json",
      "rationale": "Infrastructure card issuing africaine"
    },
    {
      "priority": "low",
      "topic": "Features planifiées vs implémentées",
      "source": "Ce fichier",
      "rationale": "Éviter hallucinations sur Airtel, CARD_PAYMENT"
    }
  ],
  "external_enrichment_needed": [
    "Textes réglementaires BEAC, BCEAO, CBN",
    "Documentation MTN MoMo Developer par opco",
    "Documentation Smile ID complète par pays",
    "Documentation Onafriq programme-specific",
    "Cas d'usage Orange Money, Wave, M-Pesa",
    "Tarification Mobile Money par pays",
    "Plafonds KYC par niveau (L1/L2/L3)"
  ]
}
```
