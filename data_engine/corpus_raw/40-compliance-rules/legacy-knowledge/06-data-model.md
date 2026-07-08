# Legacy Knowledge — 06-data-model

```json
{
  "title": "Modèle de données AfriWallet — Prisma Schema",
  "version": "1.0.0",
  "source_file": "prisma/schema.prisma",
  "database": "PostgreSQL",
  "models": {
    "User": {
      "description": "Utilisateur identifié par numéro de téléphone unique",
      "fields": {
        "id": {
          "type": "String",
          "default": "cuid()"
        },
        "phoneNumber": {
          "type": "String",
          "unique": true,
          "description": "Identifiant principal — format international"
        },
        "pinHash": {
          "type": "String",
          "description": "PIN bcrypt, jamais en clair"
        },
        "kycStatus": {
          "type": "KycStatus",
          "default": "PENDING"
        },
        "kycReference": {
          "type": "String?",
          "description": "Référence session KYC Smile ID"
        },
        "kycFailureReason": {
          "type": "String?"
        },
        "smartSelfieEnrolledAt": {
          "type": "DateTime?",
          "description": "Date enrollment SmartSelfie"
        },
        "smartSelfieEnrollJobId": {
          "type": "String?"
        },
        "smartSelfieEnrollReason": {
          "type": "String?"
        },
        "smartSelfieLastAuthAt": {
          "type": "DateTime?"
        },
        "smartSelfieLastAuthJobId": {
          "type": "String?"
        },
        "smartSelfieLastAuthReason": {
          "type": "String?"
        },
        "smartSelfieLastAuthSuccess": {
          "type": "Boolean?"
        }
      },
      "relations": [
        "wallets Wallet[]"
      ]
    },
    "Wallet": {
      "description": "Compte wallet FCFA — 1 par utilisateur",
      "fields": {
        "id": {
          "type": "String",
          "default": "cuid()"
        },
        "userId": {
          "type": "String",
          "unique": true
        },
        "balanceFcfa": {
          "type": "BigInt",
          "default": 0,
          "description": "Solde entier FCFA — pas de décimales"
        }
      },
      "relations": [
        "user User",
        "virtualCards VirtualCard[]",
        "transactions Transaction[]"
      ]
    },
    "VirtualCard": {
      "description": "Carte virtuelle émise par Onafriq",
      "fields": {
        "walletId": {
          "type": "String"
        },
        "provider": {
          "type": "CardProvider",
          "value": "ONAFRIQ"
        },
        "lastFour": {
          "type": "String",
          "length": 4,
          "description": "Affichage uniquement"
        },
        "cardToken": {
          "type": "String",
          "description": "registrationAccountId Onafriq"
        },
        "isFrozen": {
          "type": "Boolean",
          "default": false
        }
      }
    },
    "Transaction": {
      "description": "Journal comptable immuable",
      "fields": {
        "amountFcfa": {
          "type": "BigInt",
          "description": "Montant entier FCFA"
        },
        "feeFcfa": {
          "type": "BigInt",
          "default": 0,
          "note": "Toujours 0 dans implémentation actuelle"
        },
        "currency": {
          "type": "String",
          "default": "XAF"
        },
        "description": {
          "type": "String?"
        },
        "type": {
          "type": "TransactionType"
        },
        "status": {
          "type": "TransactionStatus",
          "default": "PENDING"
        },
        "failureReason": {
          "type": "String?"
        },
        "provider": {
          "type": "PaymentProvider?"
        },
        "providerTxId": {
          "type": "String?",
          "unique": true
        },
        "idempotencyKey": {
          "type": "String?",
          "unique": true
        },
        "metadata": {
          "type": "Json?",
          "description": "Payload webhook, passCode carte, etc."
        }
      },
      "indexes": [
        "walletId + createdAt"
      ]
    },
    "OtpRequest": {
      "description": "Historique OTP SMS",
      "fields": {
        "phoneNumber": {
          "type": "String"
        },
        "code": {
          "type": "String",
          "format": "6 digits"
        },
        "expiresAt": {
          "type": "DateTime",
          "ttl_minutes": 5
        },
        "attempts": {
          "type": "Int",
          "default": 0,
          "max": 3
        }
      }
    },
    "WebhookEvent": {
      "description": "Audit et idempotence webhooks",
      "fields": {
        "provider": {
          "type": "PaymentProvider"
        },
        "eventKey": {
          "type": "String",
          "unique": true
        },
        "userId": {
          "type": "String?"
        },
        "kycReference": {
          "type": "String?"
        },
        "payload": {
          "type": "Json"
        },
        "processedAt": {
          "type": "DateTime?"
        },
        "error": {
          "type": "String?"
        }
      }
    }
  },
  "enums": {
    "KycStatus": {
      "values": [
        "PENDING",
        "VERIFIED",
        "REJECTED"
      ],
      "flow": "PENDING → VERIFIED|REJECTED via webhook Smile ID"
    },
    "TransactionType": {
      "values": {
        "CASH_IN_MOMO": {
          "implemented": true,
          "description": "Dépôt MTN MoMo"
        },
        "CASH_OUT_MOMO": {
          "implemented": true,
          "description": "Retrait MTN MoMo"
        },
        "CASH_IN_AIRTEL": {
          "implemented": false,
          "description": "Futur Airtel Money"
        },
        "CARD_ISSUANCE_FEE": {
          "implemented": true,
          "description": "Frais émission carte Onafriq"
        },
        "CARD_PAYMENT": {
          "implemented": false,
          "description": "Paiement par carte — futur"
        },
        "CARD_REFUND": {
          "implemented": false,
          "description": "Remboursement carte — futur"
        },
        "ADJUSTMENT": {
          "implemented": true,
          "description": "Dépôt Bridge bancaire"
        }
      }
    },
    "TransactionStatus": {
      "values": [
        "PENDING",
        "SUCCESS",
        "FAILED"
      ],
      "note": "Journal immuable — seul status et metadata modifiables"
    },
    "PaymentProvider": {
      "values": [
        "MTN_MOMO",
        "AIRTEL",
        "BRIDGE",
        "ONAFRIQ",
        "SMILE_ID"
      ]
    },
    "CardProvider": {
      "values": [
        "ONAFRIQ"
      ]
    }
  },
  "business_rules": [
    "1 wallet par user — pas de multi-wallet",
    "balanceFcfa BigInt — évite erreurs floating point sur FCFA",
    "providerTxId unique — clé idempotence MTN referenceId",
    "SmartSelfie champs séparés de kycStatus",
    "Transactions triées createdAt desc pour historique"
  ]
}
```
