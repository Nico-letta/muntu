# Legacy Knowledge — 04-business-flows

```json
{
  "title": "Flux métier AfriWallet — Fintech Africaine",
  "version": "1.0.0",
  "flows": [
    {
      "id": "onboarding_complete",
      "name": "Onboarding utilisateur complet",
      "description": "Création compte, wallet FCFA, KYC, premier dépôt",
      "steps": [
        {
          "step": 1,
          "action": "Demander OTP",
          "endpoint": "POST /auth/otp/request",
          "body": { "phoneNumber": "+237670000000" },
          "rules": ["Numéro ne doit pas exister", "Cooldown 60s", "Max 5/h, 10/jour"],
          "result": "SMS OTP 6 chiffres (Twilio prod) ou otp en dev"
        },
        {
          "step": 2,
          "action": "Vérifier OTP et définir PIN",
          "endpoint": "POST /auth/otp/verify",
          "body": { "phoneNumber": "+237670000000", "otp": "123456", "pin": "1234" },
          "rules": ["OTP TTL 5 min", "Max 3 tentatives", "PIN hashé bcrypt"],
          "result": "User + Wallet (balance 0) + JWT accessToken"
        },
        {
          "step": 3,
          "action": "Démarrer KYC",
          "endpoint": "POST /kyc/start",
          "auth": "JWT Bearer",
          "result": "kycStatus PENDING, kycReference généré"
        },
        {
          "step": 4,
          "action": "Biometric KYC upload-url",
          "endpoint": "POST /kyc/biometric/upload-url",
          "body_example_ng": {
            "country": "NG",
            "idType": "NIN_V2",
            "idNumber": "00000000000",
            "firstName": "John",
            "lastName": "Doe",
            "dob": "1990-01-01"
          },
          "result": "upload_url S3 + jobId"
        },
        {
          "step": 5,
          "action": "Upload ZIP biométrique",
          "endpoint": "POST /kyc/biometric/upload-zip",
          "note": "ZIP avec info.json + selfie + 8 liveness",
          "result": "uploaded: true"
        },
        {
          "step": 6,
          "action": "Attendre résultat KYC",
          "options": [
            "Webhook POST /webhooks/smile-id (job_success true/false)",
            "Polling POST /kyc/utils/job-status jobType 1"
          ],
          "result": "kycStatus VERIFIED ou REJECTED"
        },
        {
          "step": 7,
          "action": "Premier dépôt MoMo",
          "endpoint": "POST /payments/deposit/momo",
          "body": { "amountFcfa": 5000 },
          "prerequisite": "kycStatus VERIFIED",
          "result": "referenceId PENDING → SUCCESS crédite wallet"
        }
      ]
    },
    {
      "id": "momo_deposit",
      "name": "Dépôt Mobile Money (cash-in)",
      "provider": "MTN_MOMO",
      "transaction_type": "CASH_IN_MOMO",
      "steps": [
        { "step": 1, "check": "KYC VERIFIED" },
        { "step": 2, "action": "MTN RequestToPay", "api": "POST /collection/v1_0/requesttopay", "headers": ["X-Reference-Id UUID", "X-Target-Environment", "X-Callback-Url optional"] },
        { "step": 3, "action": "Créer Transaction PENDING", "providerTxId": "referenceId" },
        { "step": 4, "action": "Client confirme sur téléphone MoMo" },
        { "step": 5, "action": "Callback ou polling", "success_statuses": ["SUCCESSFUL", "SUCCESS"], "effect": "Crédit wallet + Transaction SUCCESS" },
        { "step": 6, "action": "Si FAILED/REJECTED", "effect": "Transaction FAILED, pas de crédit" }
      ],
      "sandbox_note": "Devise souvent EUR en sandbox, XAF en prod"
    },
    {
      "id": "momo_withdraw",
      "name": "Retrait Mobile Money (cash-out)",
      "provider": "MTN_MOMO",
      "transaction_type": "CASH_OUT_MOMO",
      "steps": [
        { "step": 1, "check": "KYC VERIFIED + solde suffisant" },
        { "step": 2, "action": "MTN Disbursement transfer", "api": "POST /disbursement/v1_0/transfer" },
        { "step": 3, "action": "Décrément wallet IMMÉDIAT (réservation PENDING)" },
        { "step": 4, "action": "Callback ou polling" },
        { "step": 5, "success": "Transaction SUCCESS — fonds sur MoMo client" },
        { "step": 6, "failure": "Transaction FAILED + RECRÉDIT wallet (compensation)" }
      ],
      "critical_pattern": "Compensation obligatoire si échec après réservation"
    },
    {
      "id": "virtual_card_creation",
      "name": "Émission carte virtuelle Onafriq",
      "provider": "ONAFRIQ",
      "transaction_type": "CARD_ISSUANCE_FEE",
      "steps": [
        { "step": 1, "check": "KYC VERIFIED + solde >= amountFcfa" },
        { "step": 2, "action": "OAuth2 Onafriq token", "api": "POST /idp/connect/token grant client_credentials" },
        { "step": 3, "action": "Register personalized account", "api": "POST /rest/api/v1/accounts/personalized", "defaults": { "country": "CM", "city": "Douala", "currency": "XAF" } },
        { "step": 4, "action": "Décrément wallet + VirtualCard + Transaction SUCCESS" },
        { "step": 5, "result": "cardToken, lastFour, passCode en metadata" }
      ]
    },
    {
      "id": "smartselfie_auth",
      "name": "Authentification SmartSelfie (step-up)",
      "description": "Biométrie pour action sensible — ne change PAS kycStatus",
      "steps": [
        { "step": 1, "action": "Choisir reason", "values": ["large_withdrawal", "pin_reset", "high_risk_device", "wallet_recovery"] },
        { "step": 2, "action": "POST /kyc/smartselfie/auth/upload-url ou /auth direct" },
        { "step": 3, "action": "Upload selfie via ZIP" },
        { "step": 4, "action": "POST /kyc/smartselfie/confirm", "jobType": 2 },
        { "step": 5, "result": "smartSelfieLastAuthSuccess true/false sur User" }
      ]
    },
    {
      "id": "document_verification_cg",
      "name": "Vérification document Congo",
      "country": "CG",
      "job_type": 11,
      "steps": [
        { "step": 1, "action": "POST /kyc/document-verification/upload-url", "idType": "IDENTITY_CARD" },
        { "step": 2, "action": "ZIP: info.json + selfie + id_front + id_back" },
        { "step": 3, "action": "POST /kyc/document-verification/upload-zip" },
        { "step": 4, "action": "Webhook Smile → VERIFIED/REJECTED" }
      ],
      "restriction": "Seul CG accepté pour document verification dans AfriWallet"
    },
    {
      "id": "pin_reset",
      "name": "Réinitialisation PIN",
      "steps": [
        { "step": 1, "endpoint": "POST /auth/pin/reset/request", "requires": "Compte existant" },
        { "step": 2, "endpoint": "POST /auth/pin/reset/verify", "body": { "phoneNumber", "otp", "pin": "nouveau PIN" } },
        { "step": 3, "result": "Nouveau PIN hashé + JWT" }
      ]
    },
    {
      "id": "bridge_deposit",
      "name": "Dépôt bancaire Bridge (sandbox)",
      "provider": "BRIDGE",
      "transaction_type": "ADJUSTMENT",
      "steps": [
        { "step": 1, "check": "KYC VERIFIED" },
        { "step": 2, "action": "Bridge createPaymentRequest", "sandbox_bank": "Demo Bank provider_id 574" },
        { "step": 3, "action": "Transaction PENDING, retour paymentRequestUrl" },
        { "step": 4, "action": "Client paie via interface bancaire" },
        { "step": 5, "success": "Statut ACSC → crédit wallet" },
        { "step": 6, "failure": "Statut RJCT → FAILED" }
      ]
    },
    {
      "id": "onafriq_card_lifecycle",
      "name": "Cycle de vie carte Onafriq (webhooks)",
      "steps": [
        { "step": 1, "event": "Carte créée", "cardStatus": "AC", "isFrozen": false },
        { "step": 2, "event": "Gel carte", "cardStatus": ["IA", "LC", "SC", "DEACTIVATED", "EX", "INACTIVE", "LOSTORSTOLEN"], "isFrozen": true },
        { "step": 3, "event": "Réactivation", "cardStatus": "AC", "isFrozen": false }
      ]
    }
  ]
}

```
