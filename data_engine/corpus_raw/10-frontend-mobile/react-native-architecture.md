# Frontend Mobile — Architecture React Native

> **Couche** : `10-frontend-mobile` · **Expert MoE** : UI mobile  
> **Source** : `15-mobile-ux-studies/case-ui-001/`

## Contexte

Apps wallet AfriWallet consomment l'API REST async (MoMo, KYC). L'UI doit gérer états PENDING, polling, et connectivité intermittente.

## Principes

- MSISDN comme identifiant — clavier numérique PIN/OTP.
- Jamais afficher OTP en prod (vient par SMS).
- Polling statut paiement avec backoff (2s → 10s → 30s).
- États KYC : PENDING / VERIFIED / REJECTED clairement affichés.

```json
{
  "api_base": "JWT Bearer after /auth/otp/verify",
  "async_screens": ["momo_deposit_pending", "kyc_upload_progress", "bridge_payment_url"],
  "reference_case_study": "../15-mobile-ux-studies/case-ui-001/"
}
```

## Voir aussi

- `00-core-principles/mobile-first.md`
- `35-business-flows/afriwallet-business-flows.md`
