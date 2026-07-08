# Exemples annotés normalisés — MTN MoMo + Airtel Open API

> **Couche:** `35-business-flows` · **Schema:** `corpus-annotation-schema.md`  
> **Sources:** `Momo documentation.txt`, `Airtel.txt` (documentation officielle uniquement)  
> **Complement:** scenarios narratifs dans `debug-scenarios-production.md` (non remplace)

---

## EX-MTN-001 — Cycle de vie async RequestToPay (POST 202 -> PENDING -> SUCCESSFUL/FAILED)

| Champ | Valeur |
|-------|--------|
| id | EX-MTN-001 |
| provider | MTN_MOMO |
| source_officielle | Momo documentation.txt |
| section_doc | Getting Started > POST / GET / PUT |
| pays | CG / mtncongo (prod) ; sandbox pour tests |
| devise | XAF (prod CG) ; EUR (sandbox) |
| flux | RequestToPay (Collection / cash-in) |
| async_mode | async_202 |
| difficulte | basic |
| afriwallet_status | deploye |
| tags | async, pending, callback, polling |

### Contexte metier
Integrateur initie un depot MoMo. L'API retourne 202 mais le wallet interne reste en attente. Question frequente : est-ce un bug ou le comportement normal ?

### Artefacts officiels

Documentation MTN (extrait) :

```
POST /requesttopay

The POST is an asynchronous method. The Wallet Platform will validate the request
to ensure that it is correct according to the API specification and then answer
with HTTP 202 Accepted. The created resource will get status PENDING. Once the
request has been processed the status will be updated to SUCCESSFUL or FAILED.
The requester may then be notified of the final status through callback.

POST /requesttopay request is sent with X-Reference-Id = 11377cbe-374c-43f6-a019-4fb70e57b617

GET /requesttopay/11377cbe-374c-43f6-a019-4fb70e57b617 will return the status of the request.
```

### Annotation semantique

| Element | Role |
|---------|------|
| HTTP 202 | Acceptation de la requete, **pas** succes financier |
| X-Reference-Id | Identifiant partenaire UUID v4, cle d'idempotence et de poll |
| status PENDING | Etat intermediaire obligatoire avant SUCCESSFUL ou FAILED |
| GET /requesttopay/{id} | Lecture du statut final si callback absent |
| Callback PUT | Notification finale optionnelle si X-Callback-Url fourni |

### Chaine de justification

1. **Fait :** HTTP 202 apres POST /requesttopay.
2. **Regle officielle :** 202 signifie requete validee et mise en file ; ressource creee en PENDING.
3. **Conclusion :** Absence de credit wallet immediate est **conforme** a la spec MTN.
4. **Action :** Attendre callback PUT ou poller GET jusqu'a statut SUCCESSFUL ou FAILED.

### Mapping AfriWallet (implementation)

- `Transaction.type = CASH_IN_MOMO`, `status = PENDING`, `providerTxId = referenceId`.
- Webhook attendu : `eventKey = mtn:r2p:{referenceId}`.
- Fallback : sync status via GET MTN (pattern documente officiellement).

### Anti-patterns

| Anti-pattern | Risque | Justification |
|--------------|--------|---------------|
| Crediter wallet sur HTTP 202 | Double spend / credit sans paiement | 202 != SUCCESSFUL |
| Ignorer GET fallback | PENDING indefini si callback perdu | Doc : callback envoye une seule fois |
| Reutiliser X-Reference-Id | 409 RESOURCE_ALREADY_EXIST | Doc POST : reference id must be unique |

### Liens corpus
- Scenario narratif : `debug-scenarios-production.md` Scenario 1
- Matrice erreurs : `30-system-integrations/provider-official-error-matrix-normalized.md`

---

## EX-MTN-002 — Callback unique sans retry + obligation poll fallback

| Champ | Valeur |
|-------|--------|
| id | EX-MTN-002 |
| provider | MTN_MOMO |
| source_officielle | Momo documentation.txt |
| section_doc | Callback (English) |
| pays | multi-OpCo |
| devise | selon OpCo |
| flux | RequestToPay / Transfer callback |
| async_mode | async_202 |
| difficulte | intermediate |
| afriwallet_status | deploye |
| tags | callback, reliability, polling |

### Contexte metier
Production : firewall, certificat TLS, ou downtime applicatif au moment du callback MTN. Transaction reste PENDING cote integrateur.

### Artefacts officiels

```
The PUT method is used by the Open API when sending callbacks.
The Wallet Platform will only send the callback once.
There is no retry on the callback if the Partner system does not respond.
If the callback is not received, then the Partner system can use GET to validate the status.

Please note that the Wallet Platform sends the callback only once.
There is no retry mechanism if the partner system does not respond.
To ensure reliability, we strongly recommend that partner systems implement a fallback
mechanism by polling the transaction status using the appropriate GET method.
```

Configuration sandbox :
```
Register your callback host by specifying the domain as providerCallbackHost when creating your API Keys.
Specify the callback URL in each of your /requesttopay or /transfer POST.
Only https is allowed on sandbox.
Allow PUT & POST on your callback listener host.
```

### Chaine de justification

1. **Fait :** Aucun webhook recu apres SUCCESSFUL cote MTN.
2. **Regle :** MTN n'effectue **aucun** retry callback.
3. **Conclusion :** L'integrateur **doit** poller GET ; ce n'est pas un bug MTN.
4. **Action :** GET status + verifier providerCallbackHost == host de X-Callback-Url.

### Mapping AfriWallet (implementation)

- `WebhookEvent` absent != transaction echouee.
- Route : `POST /webhooks/mtn/requesttopay/{referenceId}` (listener HTTPS public).
- Variable : `MTN_MOMO_CALLBACK_BASE_URL` doit correspondre au host enregistre.

### Anti-patterns

| Anti-pattern | Risque |
|--------------|--------|
| Attendre un 2e callback | PENDING permanent |
| IP au lieu de hostname pour providerCallbackHost | INVALID_CALLBACK_URL_HOST |
| HTTP au lieu de HTTPS | Rejet sandbox/prod |

### Liens corpus
- Scenario narratif : Scenario 6 (INVALID_CALLBACK_URL_HOST)

---

## EX-MTN-003 — 409 RESOURCE_ALREADY_EXIST (X-Reference-Id duplique)

| Champ | Valeur |
|-------|--------|
| id | EX-MTN-003 |
| provider | MTN_MOMO |
| source_officielle | Momo documentation.txt |
| section_doc | Common Error Codes |
| pays | multi-OpCo |
| devise | selon OpCo |
| flux | RequestToPay / Transfer POST |
| async_mode | async_202 |
| difficulte | intermediate |
| afriwallet_status | deploye |
| tags | idempotence, duplicate, 409 |

### Contexte metier
Retry reseau apres timeout client. Meme X-Reference-Id renvoye. MTN retourne 409.

### Artefacts officiels

| HTTP | Code | Description (officielle) | Action (officielle) |
|------|------|--------------------------|---------------------|
| 409 | RESOURCE_ALREADY_EXIST | Duplicated Reference ID. Every request must have a unique reference ID. | Check X-Reference ID is unique UUID V4 |

Regle POST :
```
If a POST is using a reference id that is already used, then a duplication error response will be sent to the client.
```

### Chaine de justification

1. **Fait :** HTTP 409 RESOURCE_ALREADY_EXIST.
2. **Regle :** Chaque POST exige un reference id unique.
3. **Conclusion :** Le retry avec le meme ID est **rejete** ; la transaction originale peut exister.
4. **Action :** GET /requesttopay/{referenceId} pour connaitre le statut reel ; ne pas generer un 2e POST avec le meme ID.

### Mapping AfriWallet (implementation)

- `providerTxId` = UUID v4 genere une seule fois par initiation.
- Si 409 et tx deja en base PENDING : poll, pas nouvelle initiation.

### Liens corpus
- Scenario narratif : Scenario 13
- Q&A : `debug-qa-deep-training.md` Q2

---

## EX-MTN-004 — NOT_ALLOWED_TARGET_ENVIRONMENT (OpCo Congo)

| Champ | Valeur |
|-------|--------|
| id | EX-MTN-004 |
| provider | MTN_MOMO |
| source_officielle | Momo documentation.txt |
| section_doc | Common Error Codes |
| pays | CG |
| devise | XAF |
| flux | Toute API MoMo |
| async_mode | async_202 |
| difficulte | basic |
| afriwallet_status | deploye |
| tags | opco, mtncongo, headers |

### Artefacts officiels

| HTTP | Code | Action (officielle) |
|------|------|---------------------|
| 500 | NOT_ALLOWED_TARGET_ENVIRONMENT | MTN Congo = mtncongo ; Test = sandbox |

### Chaine de justification

1. **Fait :** HTTP 500 NOT_ALLOWED_TARGET_ENVIRONMENT.
2. **Regle :** Header X-Target-Environment doit correspondre a l'OpCo du pays.
3. **Conclusion :** Brazzaville requiert mtncongo, pas mtncameroon ni sandbox.
4. **Action :** Corriger MTN_MOMO_TARGET_ENVIRONMENT et header ; aligner devise XAF.

---

## EX-MTN-005 — INTERNAL_PROCESSING_ERROR (fonds insuffisants masques)

| Champ | Valeur |
|-------|--------|
| id | EX-MTN-005 |
| provider | MTN_MOMO |
| source_officielle | Momo documentation.txt |
| section_doc | Common Error Responses with Action |
| pays | multi-OpCo |
| devise | selon OpCo |
| flux | RequestToPay / Transfer (statut final) |
| async_mode | async_202 |
| difficulte | advanced |
| afriwallet_status | deploye |
| tags | insufficient_funds, generic_error, ux |

### Artefacts officiels

| Type | Description (officielle) | Action (officielle) |
|------|--------------------------|---------------------|
| INTERNAL_PROCESSING_ERROR | Default generic error. Predominantly insufficient customer funds. Also service denied or Wallet Platform not reachable. | Customer verify funds and retry. Contact Account Manager if persists. |

Sandbox officiel :

| Use Case | MSISDN test |
|----------|-------------|
| RequestToPayPayerCouldNotPerformTransaction | 46733123463 |
| RequestToPayPayerNotFound | 46733123455 |
| RequestToPayPayerInternalProcessingError | 46733123461 |

### Chaine de justification

1. **Fait :** Statut FAILED avec reason INTERNAL_PROCESSING_ERROR.
2. **Regle :** Code generique ; cause frequente = fonds insuffisants cote client MoMo.
3. **Conclusion :** Message UX solde insuffisant plus pertinent que erreur interne.
4. **Action :** Client recharge MoMo ; utiliser MSISDN sandbox pour reproduire.

---

## EX-AIRTEL-001 — Disbursement v3 succes (TS + DP00900001001)

| Champ | Valeur |
|-------|--------|
| id | EX-AIRTEL-001 |
| provider | AIRTEL_OPEN_API |
| source_officielle | Airtel.txt |
| section_doc | POST /standard/v3/disbursements |
| pays | CG |
| devise | XAF |
| flux | Disbursement B2B |
| async_mode | sync_200 |
| difficulte | intermediate |
| afriwallet_status | spec_officielle_non_deployee |
| tags | disbursement, TS, headers, pin_rsa |

### Contexte metier
Specification officielle pour credit wallet payee. **AfriWallet : enum AIRTEL schema_only — pas de service TypeScript deploye.**

### Artefacts officiels

Headers requis : Content-Type, Accept, X-Country CG, X-Currency XAF, Authorization Bearer, x-signature/x-key optionnels.

Reponse 200 succes (extrait doc) :
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

UAT : `https://openapiuat.airtel.cg/standard/v3/disbursements`

### Chaine de justification

1. **Fait :** HTTP 200, status.success=true, transaction.status=TS.
2. **Regle :** TS + DP00900001001 = succes financier confirme (sync, pas 202).
3. **Conclusion :** Credit wallet autorise apres validation des deux niveaux status.
4. **Action :** Persister airtel_money_id ; ne pas re-POST meme transaction.id.

### Anti-patterns

| Anti-pattern | Risque |
|--------------|--------|
| Crediter sur HTTP 200 seul sans lire transaction.status | Faux positif si TF/TIP |
| Reutiliser transaction.id | ESB000041 |

---

## EX-AIRTEL-002 — ESB000041 Duplicate External Transaction ID

| Champ | Valeur |
|-------|--------|
| id | EX-AIRTEL-002 |
| provider | AIRTEL_OPEN_API |
| source_officielle | Airtel.txt |
| section_doc | Product Specific Error Codes |
| pays | CG |
| devise | XAF |
| flux | Disbursement / Payments POST |
| async_mode | enquiry_required |
| difficulte | advanced |
| afriwallet_status | spec_officielle_non_deployee |
| tags | duplicate, ESB000041, idempotence |

### Artefacts officiels

| Code | Description (officielle) |
|------|--------------------------|
| ESB000041 | Transaction with External Transaction ID already exists. Please try again with correct request. |

### Chaine de justification

1. **Fait :** Reponse ESB000041.
2. **Regle :** transaction.id partenaire deja present cote Airtel.
3. **Conclusion :** Retry POST aveugle interdit ; transaction originale peut etre TS ou TIP.
4. **Action :** GET enquiry avant toute decision.

Comparaison : MTN 409 RESOURCE_ALREADY_EXIST -> meme regle enquiry-first.

---

## EX-AIRTEL-003 — Transaction Enquiry Cash-In (TA / TIP / TS / TF)

| Champ | Valeur |
|-------|--------|
| id | EX-AIRTEL-003 |
| provider | AIRTEL_OPEN_API |
| source_officielle | Airtel.txt |
| section_doc | GET /standard/v1/payments/{id} |
| pays | CG |
| devise | XAF |
| flux | Cash-In status check |
| async_mode | enquiry_required |
| difficulte | advanced |
| afriwallet_status | spec_officielle_non_deployee |
| tags | TA, TIP, TS, TF, enquiry |

### Artefacts officiels

Note doc :
```
airtel_money_id is not generated in case of TIP and TF.
Only generated for TS.
Conduct transaction inquiry at least one minute after the payment API has been called.
```

Statuts : TF, TS, TA, TIP.

Codes : DP01000001000 Ambiguous, DP01000001006 In Process, DP01000001001 Success.

### Chaine de justification

1. **Fait :** status = TIP ou TA apres POST.
2. **Regle :** Etats non finaux ; pas d'airtel_money_id pour TIP/TF.
3. **Conclusion :** Interdiction de crediter wallet interne.
4. **Action :** Attendre >= 1 min, GET enquiry, repeter jusqu'a TS ou TF.

---

## EX-AIRTEL-004 — ROUTER001 Wallet not configured

| Champ | Valeur |
|-------|--------|
| id | EX-AIRTEL-004 |
| provider | AIRTEL_OPEN_API |
| source_officielle | Airtel.txt |
| section_doc | Common Error Codes |
| pays | CG |
| devise | XAF |
| flux | Toute API Airtel |
| async_mode | sync_200 |
| difficulte | basic |
| afriwallet_status | spec_officielle_non_deployee |
| tags | ROUTER001, configuration |

### Artefacts officiels

| Code | Description (officielle) |
|------|--------------------------|
| ROUTER001 | Wallet is not configured. Application Wallet not configured. |

### Chaine de justification

1. **Fait :** ROUTER001 des la premiere requete UAT.
2. **Regle :** Wallet produit requis dans portail Developer.
3. **Conclusion :** Probleme provisioning, pas bug applicatif.
4. **Action :** Dashboard Airtel -> Application Settings -> Wallet.

---

## EX-AIRTEL-005 — Refund TR + DP03520001001

| Champ | Valeur |
|-------|--------|
| id | EX-AIRTEL-005 |
| provider | AIRTEL_OPEN_API |
| source_officielle | Airtel.txt |
| section_doc | imt/v1/refund |
| pays | CG |
| devise | XAF |
| flux | Remittance refund |
| async_mode | sync_200 |
| difficulte | intermediate |
| afriwallet_status | spec_officielle_non_deployee |
| tags | refund, TR, DP03520001001 |

### Artefacts officiels

```json
{
  "data": {
    "transaction": {
      "status": "TR",
      "message": "Transaction Reversed"
    }
  },
  "status": {
    "response_code": "DP03520001001",
    "success": true
  }
}
```

### Chaine de justification

1. **Fait :** TR + DP03520001001 + success=true.
2. **Regle :** TR = Transaction Reversed ; code produit refund success.
3. **Conclusion :** Renversement confirme cote Airtel.
4. **Action :** Audit trail avec transaction.id original.

---

## EX-AIRTEL-006 — Callback authentication HMAC-SHA256

| Champ | Valeur |
|-------|--------|
| id | EX-AIRTEL-006 |
| provider | AIRTEL_OPEN_API |
| source_officielle | Airtel.txt |
| section_doc | Callback authentication |
| pays | CG |
| devise | XAF |
| flux | Webhook callback |
| async_mode | sync_200 |
| difficulte | advanced |
| afriwallet_status | spec_officielle_non_deployee |
| tags | callback, hmac, security |

### Artefacts officiels

```
Hash callback request with private key from application settings
using HmacSHA256, output Base64, match hash message sent.
```

Payload callback : status_code TS, airtel_money_id, transaction.id.

### Chaine de justification

1. **Fait :** Callback avec body + hash separe.
2. **Regle :** HMAC-SHA256 body JSON, cle portail, Base64.
3. **Conclusion :** Rejet si hash mismatch.
4. **Action :** Verifier signature avant mutation etat interne.

---

## EX-CROSS-001 — Async MTN vs Sync Airtel

| Champ | Valeur |
|-------|--------|
| id | EX-CROSS-001 |
| provider | CROSS_PROVIDER |
| source_officielle | Momo documentation.txt + Airtel.txt |
| section_doc | Callback MTN + payments enquiry |
| pays | CG |
| devise | XAF |
| flux | Comparaison integration |
| async_mode | cross |
| difficulte | advanced |
| afriwallet_status | cross_provider |
| tags | architecture, async, sync |

### Chaine de justification unifiee

1. MTN : POST **202** ; final via callback PUT (once) ou GET poll.
2. Airtel : POST **200** ; statut metier TS/TIP/TA/TF dans body.
3. Regle commune : ne jamais finaliser wallet sans statut metier explicite.
4. Duplicate : MTN 409 vs Airtel ESB000041 -> enquiry first.
5. Ambigu : MTN PENDING prolonge vs Airtel TA/TIP/0000900 -> poll/enquiry.

---

## EX-AIRTEL-007 — Cash-In POST /standard/v1/cashin/

| Champ | Valeur |
|-------|--------|
| id | EX-AIRTEL-007 |
| provider | AIRTEL_OPEN_API |
| source_officielle | Airtel.txt |
| section_doc | Cash-In-APIs > POST /standard/v1/cashin/ |
| pays | CG |
| devise | XAF |
| flux | Cash-In (credit payee depuis payer wallet) |
| async_mode | enquiry_required |
| difficulte | intermediate |
| afriwallet_status | spec_officielle_non_deployee |
| tags | cash-in, DP01000001007, insufficient_funds |

### Contexte metier
Cash-In Airtel credite le wallet payee depuis le wallet payer (agent/subscriber). Distinct du disbursement v3 (B2B avec PIN RSA). **Non deploye dans AfriWallet.**

### Artefacts officiels

Endpoint :
```
POST /standard/v1/cashin/
Base URL UAT: https://openapiuat.airtel.cg
Headers: Content-Type, Accept, X-Country: CG, X-Currency: XAF, Authorization Bearer
```

Description doc :
```
This API is used to credits the amount to payee wallet from payer wallet.
```

Enquiry associee :
```
GET /standard/v1/payments/{id}
Conduct transaction inquiry at least one minute after the payment API has been called.
```

Codes Cash-In critiques (extrait doc) :

| Code | Label | Description officielle |
|------|-------|------------------------|
| DP01000001000 | Ambiguous | Still processing — do transaction enquiry |
| DP01000001001 | Success | Transaction successful |
| DP01000001006 | In Process | Pending — check after sometime |
| DP01000001007 | Insufficient Funds | Payer wallet lacks funds |
| DP01000001014 | Transaction Timed Out | May be processed or failed — do enquiry |

### Chaine de justification

1. **Fait :** POST cashin retourne HTTP 200 avec statut TIP ou DP01000001006.
2. **Regle :** Cash-In peut rester In Process ; enquiry obligatoire >= 1 minute.
3. **Conclusion :** Ne pas crediter wallet interne tant que enquiry ne retourne TS + DP01000001001.
4. **Action :** GET /standard/v1/payments/{transaction.id} ; si DP01000001007, message UX solde insuffisant payer.

### Anti-patterns

| Anti-pattern | Risque |
|--------------|--------|
| Confondre cashin et disbursement v3 | Headers/body/PIN differents |
| Crediter sur DP01000001006 seul | In Process != Success |
| Enquiry immediate (< 1 min) | Race documentee par Airtel |

### Liens corpus
- Scenario narratif : Scenario 14 (fonds insuffisants, analogie UX)
- Matrice : provider-official-error-matrix-normalized.md

---

## EX-AIRTEL-008 — Merchant Collection (register + pull payment)

| Champ | Valeur |
|-------|--------|
| id | EX-AIRTEL-008 |
| provider | AIRTEL_OPEN_API |
| source_officielle | Airtel.txt |
| section_doc | MERCHANT COLLECTION |
| pays | CG |
| devise | XAF |
| flux | Register submerchant + pull funds from subscriber |
| async_mode | enquiry_required |
| difficulte | advanced |
| afriwallet_status | spec_officielle_non_deployee |
| tags | merchant-collection, till, micro-merchant |

### Contexte metier
Produit Merchant Collection : enregistrer des micro-marchands via portail dev, puis tirer des fonds depuis abonnes Airtel vers wallet micro-marchand.

Description doc :
```
Merchant collection requires the Merchant to register their micro-merchants on airtel
through dev portal. They can now use merchant collection product to pull funds from
airtel subscribers to their micro-merchant wallet.
```

### Artefacts officiels

**Etape 1 — Register submerchant**
```
POST /merchant-collection/v1/merchant
Headers: x-country CG, x-currency XAF, Authorization, Content-Type, Accept
```

Body (extrait) :
```json
{
  "merchants": [{
    "relationship_id": "ABCDE1",
    "name": "Fine Art Works",
    "account_details": { "msisdn": "123456789" }
  }]
}
```

Reponse : `airtel_relationship_id` assigne, `status: PENDING` initial.

**Etape 2 — Pull payment (transfer)**
```
POST /merchant-collection/v1/payments
```

Body (extrait doc) :
```json
{
  "payee": { "relationship_id": "Test123" },
  "payer": { "msisdn": "123****89" },
  "transaction": {
    "id": "unique-txn-id",
    "amount": "1000",
    "reference": "REF123"
  }
}
```

Champs obligatoires doc :
- `payee.relationship_id` : ID unique agregateur pour le marchand (6 chars recommande)
- `payer.msisdn` : MSISDN abonne debite
- `transaction.id` : ID unique transaction
- `transaction.reference` : max 25 chars pour rapports

**Etape 3 — Enquiry**
```
GET /merchant-collection/v1/payments/{id}
```

Codes merchant collection (extrait) :
```
DP02100001006 — Transaction In Progress: perform transaction enquiry
DP02100001007 — Invalid Input
```

### Chaine de justification

1. **Fait :** Merchant enregistre avec status PENDING.
2. **Regle :** Pull payment requiert relationship_id valide et subscriber avec fonds.
3. **Conclusion :** Flow en 3 temps (register -> pay -> enquiry) ; pas de credit marchand sans statut final.
4. **Action :** Stocker `airtel_relationship_id` ; idempotence sur `transaction.id`.

### Liens corpus
- Merchant transactions listing : `GET /merchant/v1/transactions` (rapports periode)
- Scenario narratif : matrice cross-provider debug-scenarios-production.md

---

## EX-AIRTEL-009 — Remittance IMT POST /imt/v1/credit

| Champ | Valeur |
|-------|--------|
| id | EX-AIRTEL-009 |
| provider | AIRTEL_OPEN_API |
| source_officielle | Airtel.txt |
| section_doc | Remittance APIs > imt/v1/credit |
| pays | CG |
| devise | XAF |
| flux | International remittance to Airtel subscriber |
| async_mode | enquiry_required |
| difficulte | advanced |
| afriwallet_status | spec_officielle_non_deployee |
| tags | remittance, imt, forex, thunes |

### Contexte metier
RemX : transferts internationaux vers abonnes Airtel depuis partenaires non-Airtel (Thunes, TerraPay).

Description doc :
```
RemX suite enables seamless electronic fund transfers across borders...
Currently supports transactions from non-Airtel partners to Airtel subscribers only.
```

### Artefacts officiels

Endpoint :
```
POST https://openapiuat.airtel.cg/imt/v1/credit
Headers: Authorization Bearer, x-country CG, x-currency XAF, Content-Type
```

Body requis (extrait doc) :
```json
{
  "payee": { "msisdn": "756255985" },
  "transaction": {
    "amount": 100,
    "id": "1747047503",
    "forex_rate": "0.408171"
  },
  "payer": {
    "country": "FR",
    "first_name": "Jean",
    "last_name": "Dupont"
  },
  "pin": "{encrypted}",
  "txn_type": "IMT"
}
```

Champs obligatoires doc :
- `transaction.id` : **Must be unique for each transaction** (partenaire remittance)
- `transaction.forex_rate` : Taux de change
- `payee.msisdn` : MSISDN beneficiaire Airtel
- `payer.country`, `payer.first_name`, `payer.last_name` : KYC expediteur
- `pin` : PIN chiffre RSA

Refund associe :
```
POST /imt/v1/refund
Reponse succes: status TR, response_code DP03520001001
```

### Chaine de justification

1. **Fait :** Credit IMT initie avec transaction.id partenaire unique.
2. **Regle :** Remittance = produit separe ; erreurs ambigues -> enquiry (cf. ROUTER117, 0000900).
3. **Conclusion :** Meme discipline idempotence que disbursement (ESB000041 si duplicate id).
4. **Action :** Enquiry avant retry ; refund via imt/v1/refund si annulation requise.

### Liens corpus
- EX-AIRTEL-005 (refund TR + DP03520001001)
- Scenario narratif : Scenario 5

---

## EX-MTN-006 — Remittance API (produit separe, cles subscription distinctes)

| Champ | Valeur |
|-------|--------|
| id | EX-MTN-006 |
| provider | MTN_MOMO |
| source_officielle | Momo documentation.txt |
| section_doc | Remittance + Common Error Codes |
| pays | multi-OpCo |
| devise | selon corridor |
| flux | Cross-border remittance to MoMo wallet |
| async_mode | async_202 |
| difficulte | advanced |
| afriwallet_status | non_deploye_codebase |
| tags | remittance, subscription_key, diaspora |

### Contexte metier
MTN MoMo Remittance permet aux providers licencies d'envoyer des fonds cross-border vers wallet MoMo. **Non present dans le codebase AfriWallet actuel** (seuls Collection + Disbursement deployes).

### Artefacts officiels

Description produit :
```
The MoMo Remittance API enables secure, cross-border money transfers via the MTN Mobile
Money platform. It allows licensed remittance providers to send funds directly to a
recipient's MoMo wallet in supported countries.
```

Regle cles API (Common Error Codes) :
```
Collection, Disbursement and Remittance have different subscription keys.
Verify related product subscription key is used.
Sandbox: https://momodeveloper.mtn.com/profile
Production: https://momoapi.mtn.com/profile
```

### Chaine de justification

1. **Fait :** 401 ACCESS DENIED avec cle Collection sur endpoint Remittance.
2. **Regle :** Chaque produit MTN a sa propre Ocp-Apim-Subscription-Key.
3. **Conclusion :** Erreur auth != credentials invalides globaux — mauvais produit souscrit.
4. **Action :** Souscrire produit Remittance ; provisionner API User dedie ; meme pattern async 202 + callback/poll.

### Comparaison AfriWallet deploye vs roadmap

| Produit MTN | Status AfriWallet |
|-------------|-------------|
| Collection RequestToPay | deploye (mtn.service.ts) |
| Disbursement Transfer | deploye (mtn.service.ts) |
| Remittance | non deploye |

### Liens corpus
- Golden snippet TS : `30-system-integrations/providers/mtn-momo.service.ts`
- Codebase AfriWallet : pas de remittance endpoint

---

## EX-AFW-001 — Golden Snippets TypeScript (code signature AfriWallet)

| Champ | Valeur |
|-------|--------|
| id | EX-AFW-001 |
| provider | CROSS_PROVIDER |
| source_officielle | afriwallet_codebase/src/ |
| section_doc | Golden Snippets exportes par expand_corpus_sources.py |
| pays | multi |
| devise | XAF / EUR sandbox |
| flux | Idempotence webhook + BigInt + compensation |
| async_mode | cross |
| difficulte | advanced |
| afriwallet_status | deploye |
| tags | typescript, golden-snippet, afriwallet |

### Fichiers .ts dans corpus_raw (compiles par generate_corpus.py)

| Fichier | Regle metier critique |
|---------|----------------------|
| `20-backend-api/golden-snippets/webhook-idempotence.ts` | eventKey `mtn:r2p:{referenceId}`, P2002 ignore, compensation FAILED cash-out |
| `20-backend-api/golden-snippets/momo-payments-financial-core.ts` | BigInt FCFA, decrement PENDING withdraw, recredit poll/webhook FAILED |
| `30-system-integrations/providers/mtn-momo.service.ts` | UUID v4 referenceId, 202 accepte, tokens Collection vs Disbursement |
| `25-database-storage/prisma-critical-models.ts` | balanceFcfa BigInt, providerTxId @unique, WebhookEvent.eventKey @unique |

### Chaine de justification

1. **Fait :** Le corpus markdown explique le pourquoi (CEMAC, codes erreur).
2. **Fait :** Les .ts montrent le comment exact dans AfriWallet.
3. **Regle :** Ne pas dupliquer le bundle complet (`afriwallet-complete-src-bundle.md`) — snippets signature uniquement.
4. **Action :** Relancer `python data_engine/expand_corpus_sources.py --config data_engine/configs/afriwallet.json` apres changement codebase AfriWallet.

### Liens corpus
- Schema : `corpus-annotation-schema.md`
- Scenarios : `debug-scenarios-production.md` Scenario 3 (compensation)

---

## Index

| ID | Titre | Provider |
|----|-------|----------|
| EX-MTN-001 | RequestToPay async 202 | MTN |
| EX-MTN-002 | Callback sans retry | MTN |
| EX-MTN-003 | 409 duplicate | MTN |
| EX-MTN-004 | OpCo mtncongo | MTN |
| EX-MTN-005 | INTERNAL_PROCESSING_ERROR | MTN |
| EX-MTN-006 | Remittance API produit separe | MTN |
| EX-AIRTEL-001 | Disbursement v3 TS | Airtel |
| EX-AIRTEL-002 | ESB000041 | Airtel |
| EX-AIRTEL-003 | Enquiry TA/TIP/TS/TF | Airtel |
| EX-AIRTEL-004 | ROUTER001 | Airtel |
| EX-AIRTEL-005 | Refund TR | Airtel |
| EX-AIRTEL-006 | Callback HMAC | Airtel |
| EX-AIRTEL-007 | Cash-In POST | Airtel |
| EX-AIRTEL-008 | Merchant Collection | Airtel |
| EX-AIRTEL-009 | Remittance IMT credit | Airtel |
| EX-CROSS-001 | MTN async vs Airtel sync | Cross |
| EX-AFW-001 | Golden Snippets TS | AfriWallet |
