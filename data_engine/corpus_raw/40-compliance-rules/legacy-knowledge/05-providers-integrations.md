# Legacy Knowledge — 05-providers-integrations

```json
{
  "title": "Intégrations Providers — AfriWallet Fintech Afrique",
  "version": "1.0.0",
  "providers": {
    "MTN_MOMO": {
      "name": "MTN Mobile Money",
      "type": "mobile_money",
      "source_files": [
        "src/providers/mtn.service.ts",
        "src/payments/payments.service.ts"
      ],
      "sandbox": {
        "base_url": "https://sandbox.momodeveloper.mtn.com",
        "currency_default": "EUR",
        "target_environment": "sandbox"
      },
      "production": {
        "currency_default": "XAF",
        "target_environments": [
          "mtnnigeria",
          "mtncameroon",
          "mtncongo"
        ],
        "note": "OpCo spécifique par pays MTN"
      },
      "auth": {
        "method": "OAuth2 client credentials via Basic auth",
        "token_collection": "POST /collection/token/",
        "token_disbursement": "POST /disbursement/token/",
        "headers": [
          "Authorization Bearer",
          "Ocp-Apim-Subscription-Key",
          "X-Target-Environment"
        ]
      },
      "apis": {
        "request_to_pay": {
          "method": "POST",
          "path": "/collection/v1_0/requesttopay",
          "headers": [
            "X-Reference-Id UUID",
            "X-Callback-Url optional"
          ],
          "body": {
            "amount": "string",
            "currency": "EUR|XAF",
            "externalId": "referenceId",
            "payer": {
              "partyIdType": "MSISDN",
              "partyId": "phoneNumber"
            },
            "payerMessage": "AfriWallet wallet top-up",
            "payeeNote": "AfriWallet wallet top-up"
          },
          "response": "HTTP 202 Accepted → PENDING"
        },
        "request_to_pay_status": {
          "method": "GET",
          "path": "/collection/v1_0/requesttopay/{referenceId}"
        },
        "transfer": {
          "method": "POST",
          "path": "/disbursement/v1_0/transfer",
          "body": {
            "payee": {
              "partyIdType": "MSISDN",
              "partyId": "phoneNumber"
            },
            "payerMessage": "AfriWallet wallet cash-out"
          }
        },
        "transfer_status": {
          "method": "GET",
          "path": "/disbursement/v1_0/transfer/{referenceId}"
        }
      },
      "webhook": {
        "path": "POST /webhooks/mtn/requesttopay/{referenceId}",
        "event_key": "mtn:r2p:{referenceId}",
        "payload_fields": [
          "status",
          "reason",
          "financialTransactionId"
        ],
        "success_values": [
          "SUCCESSFUL",
          "SUCCESS"
        ],
        "failed_values": [
          "FAILED",
          "REJECTED"
        ],
        "ip_allowlist": "MTN_MOMO_WEBHOOK_IP_ALLOWLIST optional"
      },
      "async_pattern": "Init → PENDING → callback webhook OU polling fallback"
    },
    "ONAFRIQ": {
      "name": "Onafriq Card Issuing",
      "type": "virtual_card",
      "source_files": [
        "src/providers/onafriq.service.ts",
        "src/virtual-cards/virtual-cards.service.ts"
      ],
      "sandbox": {
        "idp_url": "https://cards-sbx.onafriqservices.com",
        "api_url": "https://cards-sbx.onafriqservices.com"
      },
      "auth": {
        "method": "OAuth2 client_credentials",
        "path": "/idp/connect/token",
        "grant_type": "client_credentials"
      },
      "registration_defaults": {
        "country_code": "CM",
        "phone_country_code": "237",
        "state_region": "CM",
        "city": "Douala",
        "address_line1": "Wallet user",
        "birth_date": "01-JAN-1990",
        "id_type": 4,
        "id_value_prefix": "AfriWallet",
        "card_currency": "XAF",
        "first_name": "Wallet",
        "last_name_pattern": "U{8 chars userId}",
        "email_pattern": "{12 derniers userId}@platform.local"
      },
      "api": {
        "register_personalized": {
          "method": "POST",
          "path": "/rest/api/v1/accounts/personalized",
          "returns": [
            "registrationAccountId → cardToken",
            "registrationLast4Digits → lastFour",
            "registrationPassCode → passCode"
          ]
        }
      },
      "resilience": {
        "timeout_ms": 10000,
        "retry_count": 2,
        "retry_backoff_ms": 400,
        "retriable_statuses": [
          408,
          429,
          "5xx"
        ]
      },
      "webhook": {
        "path": "POST /webhooks/onafriq/cards",
        "auth": "x-webhook-signature AES256",
        "event_key": "onafriq:{notificationType}:{requestId}:{transactionId|customerId}",
        "card_status_freeze": [
          "IA",
          "LC",
          "SC",
          "DEACTIVATED",
          "EX",
          "INACTIVE",
          "LOSTORSTOLEN"
        ],
        "card_status_active": [
          "AC"
        ]
      }
    },
    "SMILE_ID": {
      "name": "Smile Identity",
      "type": "kyc_biometric",
      "source_files": [
        "src/providers/smile-id.service.ts",
        "src/kyc/kyc.controller.ts"
      ],
      "sandbox": {
        "base_url": "https://testapi.smileidentity.com"
      },
      "capabilities": {
        "biometric_kyc": {
          "job_type": 1,
          "countries": 8
        },
        "smartselfie_auth": {
          "job_type": 2
        },
        "smartselfie_register": {
          "job_type": 4
        },
        "document_verification": {
          "job_type": 11,
          "country": "CG"
        }
      },
      "rest_flow": {
        "step1": "upload-url endpoint → S3 presigned URL",
        "step2": "Build ZIP (info.json + images) → base64",
        "step3": "upload-zip endpoint"
      },
      "webhook": {
        "path": "POST /webhooks/smile-id",
        "auth": "HMAC signature ±5 min anti-replay",
        "event_key": "job_id or smile:{userId}:{timestamp}:{signature}",
        "success_field": "job_success: true → VERIFIED",
        "failure_field": "job_success: false → REJECTED"
      },
      "sandbox_result": "sandboxResult: 0|1|2 pour forcer succès/échec en test"
    },
    "BRIDGE": {
      "name": "Bridge API",
      "type": "bank_payment",
      "source_files": [
        "src/providers/bridge-payments.service.ts"
      ],
      "sandbox": {
        "base_url": "https://api.bridgeapi.io",
        "api_version": "2025-01-15",
        "demo_bank_provider_id": "574",
        "currency": "EUR"
      },
      "status_mapping": {
        "success": [
          "ACSC"
        ],
        "failed": [
          "RJCT",
          "CANC",
          "CANCELLED",
          "CANCELED"
        ],
        "pending": [
          "CREA",
          "ACTC",
          "PDNG"
        ]
      },
      "webhook": {
        "path": "POST /webhooks/bridge/payments",
        "auth": "bridgeapi-signature HMAC-SHA256",
        "event_key": "bridge:payments:{type}:{paymentRequestId}:{status}"
      }
    },
    "TWILIO": {
      "name": "Twilio SMS",
      "type": "sms_otp",
      "source_files": [
        "src/providers/sms.service.ts",
        "src/auth/auth.service.ts"
      ],
      "production_required": true,
      "message_template": "Votre code AfriWallet est: {code}",
      "otp_format": "6 chiffres"
    },
    "AIRTEL": {
      "name": "Airtel Money",
      "type": "mobile_money",
      "status": "PLANNED",
      "note": "Enum CASH_IN_AIRTEL et provider AIRTEL existent en schema Prisma mais aucune implémentation dans src/"
    }
  },
  "polling_intervals_ms": {
    "CREA": 2000,
    "ACTC": 2000,
    "PDNG": 10000,
    "PENDING": 10000,
    "UNKNOWN": 10000,
    "default": 30000
  }
}
```
