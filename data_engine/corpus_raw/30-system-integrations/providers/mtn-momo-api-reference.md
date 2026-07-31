# MTN MoMo API Reference (Catalogue Developer)

> **Couche** : `30-system-integrations` · **Type** : référence API MTN Developer (produits, provisioning, headers)  
> **Complément** : [Intégration wallet platform](./mtn-momo.md) (RequestToPay, compensation, webhooks AfriWallet)

## 1. Principes de conception
- API REST JSON sur HTTPS.
- Objets abstraits indépendants de l'implémentation wallet sous-jacente.
- Types de transaction standardisés (RequestToPay, Transfer, Payment, Preapproval).
- Codes ISO pour devises et pays.
- Identifiants flexibles: `MSISDN`, `EMAIL`, `PARTY_CODE`, `ACCOUNT_ID`.

## 2. Catalogue produits MoMo API
| Produit | Usage |
|---------|-------|
| Collection | Collecter paiements (RequestToPay, Payment) |
| Disbursement | Verser fonds (Transfer, Deposit) |
| Remittance | Transferts transfrontaliers vers wallet MoMo |
| Collection Widget | Checkout web via QR dynamique |
| Distribute | Cash-in/cash-out/airtime pour agents |
| Channel as a Service | Sous-menu USSD/App MoMo |
| KYC / Account Validation | Onboarding simplifié |
| Pre-approval | Débit auto via PIN MoMo |
| Notify | SMS personnalisé post-transaction |

## 3. Environnements & endpoints
- `sandbox_base_url`: `https://sandbox.momodeveloper.mtn.com`
- `production_base_url`: `https://momodeveloper.mtn.com`
- `oauth2_token`: `POST /oauth2/v1_0/token`
- `provision_api_user`: `POST /apiuser`
- `provision_api_key`: `POST /apiuser/{APIUser}/apikey`
- `get_api_user`: `GET /apiuser/{APIUser}`
- `request_to_pay`: `POST /collection/v1_0/requesttopay`
- `get_request_to_pay_status`: `GET /collection/v1_0/requesttopay/{referenceId}`
- `transfer`: `POST /disbursement/v1_0/transfer`
- `payment`: `POST /collection/v2_0/payment`
- `preapproval`: `POST /collection/v1_0/preapproval`
- `validate_account`: `GET /collection/v1_0/accountholder/{accountHolderIdType}/{accountHolderId}`
- `get_balance`: `GET /collection/v1_0/account/balance`

## 4. Cycle de vie développeur
1. Signup sur `momodeveloper.mtn.com` (lien activation expire en 24h).
2. Subscribe aux produits: Collection Widget, Collection, Remittances, Disbursements.
3. Récupérer Primary Key + Secondary Key par produit (profil développeur).
4. Provisionner API User + API Key via Sandbox Provisioning API.
5. Obtenir OAuth2 token, puis appeler les APIs métier.

## 5. Headers & authentication
- `Ocp-Apim-Subscription-Key: <subscription_key>` (Primary ou Secondary)
- `Content-Type: application/json`
- `Accept: application/json`
- `X-Target-Environment: sandbox` (test) ou env pays (prod)
- `Authorization: Bearer <access_token>`
- `X-Reference-Id: <uuid_v4>` (obligatoire sur POST)
- `X-Callback-Url: <https_url>` (optionnel, même domaine que `providerCallbackHost`)

### Provisioning API User
```http
POST /apiuser HTTP/1.1
Host: sandbox.momodeveloper.mtn.com
X-Reference-Id: c72025f5-5cd1-4630-99e4-8ba4722fad56
Ocp-Apim-Subscription-Key: <subscription_key>
Content-Type: application/json

{"providerCallbackHost": "clinic.com"}
```
Réponse: `201 Created`

### Provisioning API Key
```http
POST /apiuser/c72025f5-5cd1-4630-99e4-8ba4722fad56/apikey HTTP/1.1
Host: sandbox.momodeveloper.mtn.com
Ocp-Apim-Subscription-Key: <subscription_key>
```
Réponse: `201 Created` avec `{"apiKey": "..."}`

### OAuth2 token
- Grant: `client_credentials` (RFC 6749).
- Auth: Basic `base64(api_user:api_key)`.
- Token: Bearer (RFC 6750), réutilisable jusqu'à expiration.
- Sandbox: provisioning API gère user/key. Production: Partner Portal.

## 6. MTN country target environment mapping
| Pays | X-Target-Environment |
|------|---------------------|
| MTN Congo | `mtncongo` |
| MTN Uganda | `mtnuganda` |
| MTN Ghana | `mtnghana` |
| MTN Ivory Coast | `mtnivorycoast` |
| MTN Zambia | `mtnzambia` |
| MTN Cameroon | `mtncameroon` |
| MTN Benin | `mtnbenin` |
| MTN Swaziland | `mtnswaziland` |
| MTN GuineaConakry | `mtnguineaconakry` |
| MTN SouthAfrica | `mtnsouthafrica` |
| MTN Liberia | `mtnliberia` |
| MTN SouthSudan | `mtnsouthsudan` |
| MTN Nigeria | `mtnnigeria` |
| MTN Rwanda | `mtnrwanda` |
| Sandbox test | `sandbox` |

## 7. Sémantique async (POST)
- `POST /requesttopay` et `POST /transfer` -> `202 Accepted` après validation.
- Ressource créée en état `PENDING`.
- État final: `SUCCESSFUL` ou `FAILED`.
- Callback envoyé une seule fois (PUT ou POST selon config), pas de retry.
- Fallback: `GET /requesttopay/{referenceId}` si callback manquant.
- `X-Reference-Id` dupliqué -> `409 RESOURCE_ALREADY_EXIST`.

## 8. États lifecycle
- `PENDING`, `SUCCESSFUL`, `FAILED`, `REJECTED`, `EXPIRED`, `ONGOING`

## 9. Aggregator API - transferType requis
Sandbox values:
- `CUSTOM_PAYMENT`
- `CUSTOM_BANK_PAYMENT`
- `CUSTOM_BANK_PAYMENT_FEE`

Production: valeurs contractuelles fournies par l'onboarding team.

### RequestToPay (Aggregator)
```bash
curl --location 'https://sandbox.momodeveloper.mtn.com/collection/v1_0/requesttopay' \
--header 'Ocp-Apim-Subscription-Key: <key>' \
--header 'Content-Type: application/json' \
--header 'X-Target-Environment: sandbox' \
--header 'Authorization: Bearer <token>' \
--header 'X-Reference-Id: <uuid_v4>' \
--data '{
  "amount": "1000",
  "currency": "EUR",
  "externalId": "10001",
  "payer": {"partyIdType": "MSISDN", "partyId": "123456789012"},
  "payerMessage": "Order Payment",
  "payeeNote": "Order Payment",
  "transferType": "CUSTOM_PAYMENT"
}'
```

### Transfer (Aggregator)
```bash
curl --location 'https://sandbox.momodeveloper.mtn.com/disbursement/v1_0/transfer' \
--header 'Ocp-Apim-Subscription-Key: <key>' \
--header 'Content-Type: application/json' \
--header 'X-Target-Environment: sandbox' \
--header 'Authorization: Bearer <token>' \
--header 'X-Reference-Id: <uuid_v4>' \
--data '{
  "amount": "1000",
  "currency": "EUR",
  "externalId": "10001",
  "payee": {"partyIdType": "MSISDN", "partyId": "123456789012"},
  "payerMessage": "Order Payment",
  "payeeNote": "Order Payment",
  "transferType": "CUSTOM_PAYMENT"
}'
```

### Payment (Aggregator)
```bash
curl --location 'https://sandbox.momodeveloper.mtn.com/collection/v2_0/payment' \
--header 'Ocp-Apim-Subscription-Key: <key>' \
--header 'Content-Type: application/json' \
--header 'X-Target-Environment: sandbox' \
--header 'Authorization: Bearer <token>' \
--header 'X-Reference-Id: <uuid_v4>' \
--data '{
  "externalTransactionId": "10001",
  "money": {"amount": "1000", "currency": "EUR"},
  "customerReference": "MSISDN",
  "serviceProviderUserName": "TestSpUsername",
  "transferType": "CUSTOM_PAYMENT"
}'
```

## 10. Java / PHP client patterns

### Java (RequestToPay)
```java
URL url = new URL("https://sandbox.momodeveloper.mtn.com/collection/v1_0/requesttopay");
HttpURLConnection con = (HttpURLConnection) url.openConnection();
con.setRequestMethod("POST");
con.setRequestProperty("Content-Type", "application/json");
con.setRequestProperty("Ocp-Apim-Subscription-Key", subscriptionKey);
con.setRequestProperty("X-Target-Environment", "sandbox");
con.setRequestProperty("Authorization", "Bearer " + accessToken);
con.setRequestProperty("X-Reference-Id", referenceId);
con.setDoOutput(true);
try (OutputStream os = con.getOutputStream()) {
  os.write(payload.getBytes("UTF-8"));
}
```

### PHP (RequestToPay - GuzzleHttp)
```php
$client = new GuzzleHttp\Client();
$response = $client->post('https://sandbox.momodeveloper.mtn.com/collection/v1_0/requesttopay', [
  'headers' => [
    'Content-Type' => 'application/json',
    'Ocp-Apim-Subscription-Key' => $subscriptionKey,
    'X-Target-Environment' => 'sandbox',
    'Authorization' => 'Bearer ' . $accessToken,
    'X-Reference-Id' => $referenceId
  ],
  'body' => json_encode($payload)
]);
```

## 11. Callback rules
### Sandbox
- Enregistrer `providerCallbackHost` à la création API Key.
- Callback URL dans header `X-Callback-Url` sur chaque POST.
- HTTPS obligatoire.
- Autoriser PUT et POST sur le listener callback.

### Production
- Callback host enregistré via Accounts Portal.
- HTTPS obligatoire.
- Callback envoyé une seule fois - implémenter polling GET en fallback.

### CA intermédiaires approuvés (extrait)
- Amazon Root CA 1/4, Amazon RSA 2048 M01/M02/M03
- COMODO RSA Domain Validation Secure Server CA
- Certum Domain Validation CA SHA2

## 12. Sandbox test environment
- `X-Target-Environment`: `sandbox`
- Devise sandbox: `EUR`
- Comptes Partner GUI existants ne fonctionnent PAS en sandbox - utiliser Provisioning API.
- Tout MSISDN non listé -> succès par défaut.

### Valeurs de test RequestToPay (extrait)
| Scénario | MSISDN test |
|----------|-------------|
| PayerFailed | `46733123450` |
| PayerRejected | `46733123451` |
| PayerExpired | `46733123452` |
| PayerNotFound | `46733123455` |
| PayerNotAllowedTargetEnvironment | `46733123458` |
| PayerInvalidCallbackUrlHost | `46733123459` |
| PayerInvalidCurrency | `46733123460` |
| PayerInternalProcessingError | `46733123461` |
| PayerCouldNotPerformTransaction | `46733123463` |
| PayerTransfertypeUnknown | `46733123464` |

### Valeurs de test Transfer (extrait)
| Scénario | MSISDN test |
|----------|-------------|
| PayeeFailed | `46733123450` |
| PayeeNotEnoughFunds | `46733123455` |
| PayeeNotFound | `46733123457` |
| PayeeInternalProcessingError | `46733123462` |

### Valeurs de test Payment (montant)
| Scénario | Montant |
|----------|---------|
| PaymentAmountSuccess | `1000` |
| PaymentAmountFailed | `2000` |
| PaymentAmountPendingSuccess | `3000` |
| PaymentTransfertypeUnknown | `7000` |

## 13. Use cases séquentiels
1. **RequestToPay**: POST -> 202 -> PENDING -> client approuve USSD/App -> SUCCESSFUL/FAILED -> callback.
2. **Preapproval**: même flux, puis débits futurs sans re-autorisation.
3. **Transfer**: POST -> 202 -> fonds provider->payee -> callback final.
4. **Validate Account Holder**: GET -> 200 si actif (ne valide pas le montant).
5. **Get Balance**: GET solde compte par défaut lié à l'API User.
6. **Consent flows**: `POST /bc-authorize` -> `POST /oauth2/token/` -> API métier avec consent.

## 14. Règles de validation request body
- `X-Reference-Id` obligatoirement UUID v4 unique.
- Notes/messages max 160 caractères (utiliser Notify API au-delà).
- Pas de caractères spéciaux non supportés (ex: apostrophe `'`).
- Devise doit correspondre au pays cible.
- URL callback: hostname, pas IP.
- Collection, Disbursement, Remittance ont des subscription keys distinctes.

## 15. MTN Congo - note d'intégration
- Production Congo: `X-Target-Environment: mtncongo`
- Devise: XAF (Franc CFA CEA)
- Sandbox: toujours `sandbox` + EUR pour les tests documentés.
