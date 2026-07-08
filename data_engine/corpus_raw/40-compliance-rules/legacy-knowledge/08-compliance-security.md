# Legacy Knowledge — 08-compliance-security

```json
{
  "title": "Compliance et Sécurité — AfriWallet Fintech",
  "version": "1.0.0",
  "compliance_rules": [
    {
      "id": "kyc_before_money_movement",
      "rule": "KYC VERIFIED obligatoire avant tout mouvement d'argent",
      "applies_to": [
        "POST /payments/deposit/momo",
        "POST /payments/withdraw/momo",
        "POST /payments/deposit/bridge",
        "POST /virtual-cards"
      ],
      "enforcement": "BadRequestException ou ForbiddenException si kycStatus !== VERIFIED",
      "regulatory_context": "AML/CFT — obligation identification client avant services financiers"
    },
    {
      "id": "kyc_legal_vs_smartselfie",
      "rule": "SmartSelfie est décorrélé du KYC légal",
      "detail": "smartSelfieLastAuthSuccess ne remplace pas kycStatus VERIFIED pour les paiements",
      "use_case": "Step-up biométrique pour actions sensibles uniquement"
    },
    {
      "id": "immutable_transaction_journal",
      "rule": "Transactions = journal comptable immuable",
      "detail": "Seuls status, failureReason et metadata sont modifiables après création",
      "purpose": "Audit trail, réconciliation, conformité"
    },
    {
      "id": "cash_out_compensation",
      "rule": "Compensation automatique si cash-out MoMo échoue",
      "detail": "Montant réservé recrédité au wallet si status FAILED/REJECTED",
      "critical": true,
      "regulatory_context": "Protection consommateur — fonds client jamais perdus"
    },
    {
      "id": "otp_rate_limiting",
      "rule": "Anti-abus SMS OTP",
      "limits": {
        "cooldown_seconds": 60,
        "max_per_hour": 5,
        "max_per_day": 10,
        "max_attempts_per_code": 3,
        "ttl_minutes": 5
      },
      "purpose": "Prévention spam SMS et attaques brute-force"
    },
    {
      "id": "pin_security",
      "rule": "PIN jamais stocké en clair",
      "implementation": "bcrypt hash salt 10",
      "context": "Standard industrie fintech mobile"
    },
    {
      "id": "otp_production_sms",
      "rule": "En production, OTP envoyé par SMS uniquement — jamais retourné en API",
      "provider": "Twilio",
      "message": "Votre code de vérification est: {code}"
    }
  ],
  "webhook_security": [
    {
      "provider": "SMILE_ID",
      "method": "HMAC signature",
      "anti_replay": "±5 minutes timestamp window",
      "idempotence": "eventKey = job_id ou fallback signature+timestamp+userId"
    },
    {
      "provider": "ONAFRIQ",
      "method": "x-webhook-signature AES256",
      "secrets": [
        "ONAFRIQ_SECRET_KEY",
        "ONAFRIQ_WEBHOOK_SECRET"
      ]
    },
    {
      "provider": "BRIDGE",
      "method": "bridgeapi-signature HMAC-SHA256",
      "secret": "BRIDGE_WEBHOOK_SECRET"
    },
    {
      "provider": "MTN_MOMO",
      "method": "IP allowlist optionnelle",
      "env": "MTN_MOMO_WEBHOOK_IP_ALLOWLIST",
      "correlation": "referenceId dans URL path"
    }
  ],
  "idempotence_patterns": [
    {
      "layer": "Transaction",
      "key": "providerTxId",
      "example": "UUID MTN X-Reference-Id",
      "constraint": "@unique"
    },
    {
      "layer": "Transaction",
      "key": "idempotencyKey",
      "constraint": "@unique optional"
    },
    {
      "layer": "WebhookEvent",
      "key": "eventKey",
      "formats": {
        "MTN": "mtn:r2p:{referenceId}",
        "Smile": "{job_id}",
        "Onafriq": "onafriq:{notificationType}:{requestId}:{transactionId|customerId}",
        "Bridge": "bridge:payments:{type}:{paymentRequestId}:{status}"
      },
      "behavior": "Duplicate P2002 → ignore silently, return 200"
    }
  ],
  "data_retention": {
    "otp_expired": {
      "retention_days": 7,
      "cron": "every 2 hours"
    },
    "webhooks_processed": {
      "retention_days": 30,
      "cron": "every 2 hours"
    }
  },
  "throttling": {
    "auth_otp": "5 requests/minute/IP",
    "auth_module_global": "120 requests/minute"
  },
  "african_regulatory_hints": {
    "note": "AfriWallet implémente des contrôles techniques — interprétation juridique locale requise",
    "regions": {
      "CEMAC": {
        "currency": "XAF",
        "regulator_hint": "BEAC, COBAC — supervision bancaire zone CEMAC",
        "platform_context": "Defaults Onafriq CM, phone +237"
      },
      "UEMOA": {
        "currency": "XOF",
        "regulator_hint": "BCEAO — supervision zone UEMOA",
        "platform_context": "KYC CI supporté Smile ID"
      },
      "Nigeria": {
        "regulator_hint": "CBN, NIMC",
        "platform_context": "NIN/BVN KYC, MTN mtnnigeria opco"
      },
      "Kenya": {
        "regulator_hint": "CBK (Central Bank of Kenya)",
        "platform_context": "KRA PIN, National ID KYC"
      },
      "South_Africa": {
        "regulator_hint": "FSCA, SARB",
        "platform_context": "13-digit National ID KYC"
      }
    }
  }
}
```
