# Airtel Money Specifications (Congo-Brazzaville)

## 1. Environnements & onboarding
- `staging_base_url`: `https://openapiuat.airtel.cg`
- `production_base_url`: `https://openapi.airtel.cg`
- Créer un compte sur le portail développeur Airtel Africa.
- Générer les credentials staging depuis les paramètres d'application.
- Activer le compte production dans le dashboard avant le go-live.
- Ne jamais partager `client_id` / `client_secret` hors de l'équipe d'intégration.

## 2. Catalogue API (Congo CG / XAF)
| Module | Méthode | Endpoint | Usage |
|--------|---------|----------|-------|
| Auth | `POST` | `/auth/oauth2/token` | Obtenir le bearer token |
| KYC | `GET` | `/standard/v1/users/{msisdn}` | Vérifier l'abonné |
| Balance | `GET` | `/standard/v2/users/balance` | Solde wallet |
| Disbursement | `POST` | `/standard/v3/disbursements` | Créditer un wallet payee |
| Disbursement status | `GET` | `/standard/v3/disbursements/{id}` | Statut disbursement |
| Cash-In | `POST` | `/standard/v1/cashin/` | Créditer wallet depuis wallet payer |
| Payment enquiry | `GET` | `/standard/v1/payments/{id}` | Statut transaction par external id |
| ATM Withdrawal | `POST` | `/atmwithdrawal/v2/payments/` | Retrait GAB via paycode |
| Bank-to-Wallet | `POST` | `/bank-to-wallet/v1/payments/` | Virement banque -> wallet |
| Bank-to-Wallet status | `GET` | `/bank-to-wallet/v1/payments/{id}` | Statut B2W |
| Merchant register | `POST` | `/merchant-collection/v1/merchant` | Enregistrer micro-merchant |
| Merchant fetch | `GET` | `/merchant-collection/v1/fetch` | Récupérer merchant |
| Merchant collection | `POST` | `/merchant-collection/v1/payments` | Collecter fonds abonné |
| Merchant status | `GET` | `/merchant-collection/v1/payments/{id}` | Statut collection |
| Merchant refund | `POST` | `/merchant-collection/v1/payments/refund` | Rembourser collection |
| Remittance refund | `POST` | `/imt/v1/refund` | Remboursement intégral partenaire |

## 3. Headers obligatoires (Congo)
- `Content-Type: application/json`
- `Accept: application/json` ou `*/*`
- `Authorization: Bearer <access_token>`
- `X-Country: CG` (ou `x-country: CG` selon l'API)
- `X-Currency: XAF` (ou `x-currency: XAF`)
- `x-signature` + `x-key`: requis pour APIs avec message signing (disbursement v3, ATM withdrawal v2)

## 4. OAuth2 token flow
```http
POST /auth/oauth2/token HTTP/1.1
Host: openapiuat.airtel.cg
Content-Type: application/json
Accept: */*

{
  "client_id": "<consumer_key>",
  "client_secret": "<consumer_secret>",
  "grant_type": "client_credentials"
}
```
Réponse:
```json
{
  "access_token": "<token>",
  "expires_in": "180",
  "token_type": "bearer"
}
```
Règles:
- Token secret, réutiliser jusqu'à expiration.
- `expires_in` typiquement 180 secondes - rafraîchir proactivement.
- Même endpoint pour toutes les APIs du portail.

### Java (OAuth2)
```java
URL url = new URL("https://openapiuat.airtel.cg/auth/oauth2/token");
HttpURLConnection con = (HttpURLConnection) url.openConnection();
con.setRequestMethod("POST");
con.setRequestProperty("Content-Type", "application/json");
con.setRequestProperty("Accept", "*/*");
con.setDoOutput(true);
String body = "{\"client_id\":\"<id>\",\"client_secret\":\"<secret>\",\"grant_type\":\"client_credentials\"}";
try (OutputStream os = con.getOutputStream()) {
  os.write(body.getBytes("UTF-8"));
}
```

### PHP (OAuth2 - GuzzleHttp)
```php
$client = new GuzzleHttp\Client();
$response = $client->post('https://openapiuat.airtel.cg/auth/oauth2/token', [
  'headers' => [
    'Content-Type' => 'application/json',
    'Accept' => '*/*'
  ],
  'json' => [
    'client_id' => '<id>',
    'client_secret' => '<secret>',
    'grant_type' => 'client_credentials'
  ]
]);
$token = json_decode($response->getBody(), true)['access_token'];
```

## 5. Chiffrement & sécurité (v2.0)
- PIN: RSA 2048-bit, mode ECB, padding `OAEPWithSHA-256AndMGF1Padding`.
- Callback auth: HMAC-SHA256 + Base64 sur le body callback, clé privée dans les settings application.
- Message signing (disbursement v3, ATM withdrawal): payload chiffré via `x-signature` + `x-key` (AES key:iv pair).
- Clé publique RSA fournie dans la documentation Encryption du portail.

### Callback payload exemple
```json
{
  "transaction": {
    "id": "BBZMiscxy",
    "message": "Paid XAF 5,000 to TECH LIMITED, Trans ID MP210603.1234.L06941.",
    "status_code": "TS",
    "airtel_money_id": "MP210603.1234.L06941"
  }
}
```

## 6. Statuts transaction Airtel
| Code | Signification |
|------|---------------|
| `TS` | Transaction Success |
| `TF` | Transaction Failed |
| `TIP` | Transaction in Progress |
| `TA` | Transaction Ambiguous |
| `TR` | Transaction Reversed (remboursement) |

Règle critique: `airtel_money_id` n'est généré qu'en cas de `TS`. Après un payment API, attendre au moins 1 minute avant transaction enquiry.

## 7. Exemple Disbursement v3 (B2B)
```bash
curl -X POST https://openapiuat.airtel.cg/standard/v3/disbursements \
  -H 'Content-Type: application/json' \
  -H 'X-Country: CG' \
  -H 'X-Currency: XAF' \
  -H 'Authorization: Bearer <token>' \
  -H 'x-signature: <encrypted_payload>' \
  -H 'x-key: <encrypted_aes_key_iv>' \
  -d '{
    "payee": {"msisdn": "75****26", "wallet_type": "SALARY"},
    "reference": "AB***141",
    "pin": "<encrypted_pin>",
    "transaction": {"amount": 1000, "id": "AB***141", "type": "B2B"}
  }'
```
Réponse succès:
```json
{
  "data": {
    "transaction": {
      "reference_id": "APC**4",
      "airtel_money_id": "product-partner-**41",
      "id": "AB***141",
      "status": "TS",
      "message": "Transaction Successful"
    }
  },
  "status": {
    "response_code": "DP00900001001",
    "code": "200",
    "success": true,
    "message": "SUCCESS"
  }
}
```

### Java (Disbursement)
```java
URL url = new URL("https://openapiuat.airtel.cg/standard/v3/disbursements");
HttpURLConnection con = (HttpURLConnection) url.openConnection();
con.setRequestMethod("POST");
con.setRequestProperty("Content-Type", "application/json");
con.setRequestProperty("X-Country", "CG");
con.setRequestProperty("X-Currency", "XAF");
con.setRequestProperty("Authorization", "Bearer " + accessToken);
con.setRequestProperty("x-signature", encryptedPayload);
con.setRequestProperty("x-key", encryptedAesKeyIv);
con.setDoOutput(true);
```

### PHP (Disbursement - GuzzleHttp)
```php
$response = $client->post('https://openapiuat.airtel.cg/standard/v3/disbursements', [
  'headers' => [
    'Content-Type' => 'application/json',
    'X-Country' => 'CG',
    'X-Currency' => 'XAF',
    'Authorization' => 'Bearer ' . $accessToken,
    'x-signature' => $encryptedPayload,
    'x-key' => $encryptedAesKeyIv
  ],
  'json' => $payload
]);
```

## 8. Exemple Bank-to-Wallet
```bash
curl -X POST https://openapiuat.airtel.cg/bank-to-wallet/v1/payments/ \
  -H 'Content-Type: application/json' \
  -H 'x-country: CG' \
  -H 'x-currency: XAF' \
  -H 'Authorization: Bearer <token>' \
  -d '{
    "transaction": {
      "id": "AB********ya",
      "amount": "100",
      "payee": {"address_type": "MOBILE", "msisdn": "1********0"}
    },
    "note": "Bank initiated bank to wallet transfer",
    "additional_info": {}
  }'
```

## 9. Exemple Merchant Collection
```bash
curl -X POST https://openapiuat.airtel.cg/merchant-collection/v1/payments \
  -H 'x-country: CG' \
  -H 'x-currency: XAF' \
  -H 'Authorization: Bearer <token>' \
  -H 'Content-Type: application/json' \
  -d '{
    "payee": {"relationship_id": "ABCDE1"},
    "payer": {"msisdn": "24205xxxxxxx"},
    "transaction": {
      "id": "TXN-001",
      "amount": "5000",
      "reference": "Invoice-2026-001"
    }
  }'
```

## 10. Exemple Remittance Refund (statut TR)
```bash
curl -X POST https://openapiuat.airtel.cg/imt/v1/refund \
  -H 'Authorization: Bearer <token>' \
  -H 'x-country: CG' \
  -H 'x-currency: XAF' \
  -d '{"transaction": {"id": "1753167656"}, "pin": "<encrypted_pin>"}'
```
Réponse renversement:
```json
{
  "data": {
    "transaction": {
      "id": "1754303725",
      "airtel_money_id": "REMX-ASBDGHKL-1754303725",
      "reference_id": "APCCG173533944374656",
      "message": "Transaction Reversed",
      "status": "TR"
    }
  },
  "status": {
    "code": "200",
    "message": "Success",
    "response_code": "DP03520001001",
    "success": true
  }
}
```

## 11. KYC - User Enquiry
```bash
curl -X GET https://openapiuat.airtel.cg/standard/v1/users/{msisdn} \
  -H 'X-Country: CG' \
  -H 'X-Currency: XAF' \
  -H 'Authorization: Bearer <token>'
```
Champs clés: `first_name`, `last_name`, `is_barred`, `is_pin_set`, `registration.status`.

## 12. ATM Withdrawal v2
- `authentication_medium`: uniquement `PAYCODE`.
- `payer.transfer_type`: uniquement `WALLET`.
- Headers: `x-country-code: CG`, `x-currency-code: XAF`, `x-signature`, `x-key`.
- Endpoint: `POST /atmwithdrawal/v2/payments/`.

## 13. USSD & services bancaires Congo (opérationnel)
- `*128*4#`: menu Bank-to-Wallet / Wallet-to-Bank.
- `*128#`: menu principal Airtel Money.
- Actions: `1` wallet->banque, `2` banque->wallet, `3` solde bancaire, `4` mini relevé.
- Banques partenaires: UBA BANK, LCB Bank, ECOBANK, BSCA, BGFIBank, BCI, MUCODEC, BCH, CREDIT DU CONGO.
- Tarifs: banque->Airtel 0 F CFA, Airtel->banque 1%, consultation solde/relevé 0 F CFA.
- Retrait MUCODEC GAB: `*128#` -> 6 -> 2, montants multiples de 5000, code SMS valide 15 min.

## 14. Patterns d'intégration critiques
- Toujours injecter `X-Country: CG` + `X-Currency: XAF` sur les APIs Congo.
- External transaction id unique - doublon -> `ESB000041`.
- En cas d'ambiguïté (`TA`, `TIP`, `0000900`): transaction enquiry obligatoire.
- Callback envoyé une seule fois, pas de retry côté Airtel.
- Polling fallback recommandé via GET status si callback manquant.
- PIN toujours chiffré RSA avant envoi.
- Support: `121` (24/24), `Serviceclients@cg.airtel.com`.
