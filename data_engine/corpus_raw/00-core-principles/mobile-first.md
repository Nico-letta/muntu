# RULE: MOBILE-FIRST-AFRICA
En Afrique, le canal principal est le **téléphone mobile** (MSISDN), pas l'email ni le desktop.

Principes immuables pour AfriWallet et apps associées :
- L'identité utilisateur = numéro international (`+237…`, `+234…`).
- OTP SMS remplace l'email de vérification en production.
- PIN court (4+ chiffres) hashé bcrypt — pas de mot de passe complexe occidental.
- UX offline-tolerant : Mobile Money et KYC sont **asynchrones** — toujours prévoir polling + feedback utilisateur.
- Bande passante limitée : payloads API minimaux, pas de sur-fetching.

```json
{
  "primary_identifier": "phoneNumber MSISDN",
  "auth_flow": ["OTP SMS", "PIN bcrypt", "JWT 15m"],
  "async_operations": ["MoMo deposit", "MoMo withdraw", "KYC biometric", "Bridge deposit"]
}
```
