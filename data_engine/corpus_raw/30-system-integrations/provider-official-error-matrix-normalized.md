# Matrice erreurs officielles — MTN MoMo + Airtel Open API (normalisee)

> **Couche:** `30-system-integrations` · **Sources:** `Momo documentation.txt` (Common Error Codes), `Airtel.txt` (Platforms API + Cash-In API)  
> **Format:** code | HTTP | description officielle | action officielle | statut final ? | enquiry requis ?  
> **Usage:** reference canonique pour debug — ne pas dupliquer dans `90-codebase-constraints`

---

## MTN MoMo — Common Error Codes (HTTP + business)

Source : `Momo documentation.txt` section **Common Error Codes** (documentation Swagger MTN MoMo Developer Portal).

| HTTP | Code reponse | Description (officielle) | Action (officielle) | Final ? | Enquiry |
|------|--------------|--------------------------|---------------------|---------|---------|
| 409 | RESOURCE_ALREADY_EXIST | Duplicated Reference ID. Every request must have a unique reference ID. | Check X-Reference ID is unique UUID V4 | oui | GET status si 202 deja recu |
| 401 | ACCESS DENIED DUE TO INVALID SUBSCRIPTION KEY | Authentication failed. Ocp-Apim-Subscription-Key incorrect. | Verify product subscription key (Collection vs Disbursement vs Remittance differ) | oui | non |
| 404 | RESOURCE NOT FOUND | Reference ID not found. Predominantly Get Status API. | Check if original POST returned 202 | oui | non (ID invalide) |
| 400 | REQUEST REJECTED/ BAD REQUEST | Request does not follow specification. | Fix headers, UUID v4, currency, note <=160 chars, no unsupported body on Token API | oui | non |
| 403 | FORBIDDEN IP | IP not authorized for Disbursement API. | Share public IP with MTN Account Manager | oui | non |
| 500 | NOT_ALLOWED | User does not have permission. Account restricted. | Contact MTN Account Manager | oui | non |
| 500 | NOT_ALLOWED_TARGET_ENVIRONMENT | X-Target-Environment incorrect. | Use correct OpCo: mtncongo (Congo), mtncameroon, sandbox, etc. | oui | non |
| 500 | INVALID_CALLBACK_URL_HOST | Callback URL host differs from API User config. | Host must match providerCallbackHost (hostname not IP) | oui | non |
| 500 | INVALID_CURRENCY | Currency not supported on account. | Use country-specific currency code | oui | non |
| 503 | SERVICE_UNAVAILABLE | Service temporarily unavailable. | Retry later / MTN Support | non | oui apres retry |

### MTN MoMo — Common Error Responses (business, hors HTTP)

Source : meme section **Common Error Responses with Action**.

| Type | Description (officielle) | Action (officielle) | Final ? | Enquiry |
|------|--------------------------|---------------------|---------|---------|
| INTERNAL_PROCESSING_ERROR | Generic error. Predominantly insufficient customer funds. Also service denied or Wallet Platform unreachable. | Customer verify funds and retry. Contact Account Manager if persists. | souvent oui | GET status si doute |
| PAYEE_NOT_FOUND | MSISDN paid to is invalid. | MSISDN must include country code and be registered for MoMo | oui | non |
| PAYER_NOT_FOUND | MSISDN payer invalid. | MSISDN must include country code and be registered for MoMo | oui | non |
| COULD_NOT_PERFORM_TRANSACTION | Transaction timeout. Delay to approve within 5 minutes. | Customer retry and approve within 5 min | oui | non |

### MTN OpCo reference (X-Target-Environment)

| Pays | Valeur officielle |
|------|-------------------|
| Congo | mtncongo |
| Cameroun | mtncameroon |
| Nigeria | mtnnigeria |
| Test | sandbox |

---

## Airtel — Common Error Codes (Platforms API)

Source : `Airtel.txt` section **Common Error Codes** (Platforms API).

| Code | Description (officielle) | Enquiry requis ? | Final ? |
|------|--------------------------|------------------|---------|
| ROUTER001 | Wallet is not configured. Application Wallet not configured. | non | oui (config) |
| ROUTER003 | Missing header/body params. Mandatory header or body missing. | non | oui |
| ROUTER005 | Country route not configured. Contact customer support. | non | oui |
| ROUTER006 | Invalid Country. Incorrect country code. | non | oui |
| ROUTER007 | User Not authorized for provided country. | non | oui |
| ROUTER112 | Invalid Currency. Incorrect currency code. | non | oui |
| ROUTER114 | Error while Validating Pin. | non | oui |
| ROUTER115 | Incorrect Pin. | non | oui |
| ROUTER116 | Incorrect Encrypted Pin. Review encryption mechanism. | non | oui |
| ROUTER117 | Request Timeout. For payments/refund: perform transaction enquiry. | **oui** | non |
| ROUTER119 | Invalid/Missing Currency. | non | oui |

---

## Airtel — Product Specific Error Codes (ESB)

Source : `Airtel.txt` section **Product Specific Error Codes**.

| Code | Description (officielle) | Enquiry requis ? | Final ? |
|------|--------------------------|------------------|---------|
| ESB000001 | Something went wrong. Request can be in ambiguous state. | **oui** | non |
| ESB000004 | Error initiating payment. Ambiguous state possible. | **oui** | non |
| ESB000008 | Field validation error. Ambiguous state possible. | **oui** | non |
| ESB000010 | Request was Success. | non | oui (succes ESB) |
| ESB000011 | Request was Failed. | non | oui |
| ESB000014 | Error fetching transaction status. Ambiguous — enquiry after delay. | **oui** | non |
| ESB000033 | Invalid MSISDN Length. | non | oui |
| ESB000034 | Invalid Country Name. | non | oui |
| ESB000035 | Invalid Currency Code. | non | oui |
| ESB000036 | Invalid MSISDN length or does not start with 0. | non | oui |
| ESB000039 | Vendor not configured for country. | non | oui |
| ESB000041 | Transaction with External Transaction ID already exists. | **oui** (avant retry) | depend enquiry |
| ESB000045 | No Transaction Found With Provided Transaction Id. | non | oui |
| 0000900 | Transaction might be in ambiguous state. Check response_code or perform enquiry. | **oui** | non |

---

## Airtel — Cash-In API Error Codes (selection critique)

Source : `Airtel.txt` section **Cash-In-APIs > Error Codes**.

| Code | Label officiel | Description (officielle) | Enquiry ? |
|------|----------------|--------------------------|-----------|
| DP01000001000 | Ambiguous | Transaction still processing, ambiguous state. Do transaction enquiry. | **oui** |
| DP01000001001 | Success | Transaction is successful. | non |
| DP01000001005 | Failed | Transaction failed. | oui |
| DP01000001006 | In Process | Transaction in pending state. Check after sometime. | **oui** |
| DP01000001007 | Insufficient Funds | Wallet does not have enough money. | oui |
| DP01000001014 | Transaction Timed Out | May be processed or failed. Do transaction enquiry. | **oui** |

---

## Airtel — Statuts transaction (enquiry)

Source : `Airtel.txt` **GET /standard/v1/payments/{id}** — Transaction Enquiry.

| Statut | Signification (officielle) | airtel_money_id genere ? | Action |
|--------|----------------------------|--------------------------|--------|
| TS | Transaction Success | oui | Finaliser succes |
| TF | Transaction Failed | non | Finaliser echec |
| TA | Transaction Ambiguous | non | Enquiry repetee |
| TIP | Transaction in Progress | non | Attendre >= 1 min puis enquiry |

Note officielle : *airtel_money_id is not generated in case of TIP and TF. Only generated for TS. Recommended to conduct transaction inquiry at least one minute after payment API called.*

---

## Airtel — Disbursement v3 succes (reference)

Source : `Airtel.txt` **POST /standard/v3/disbursements** — 200 response sample.

| Champ | Valeur exemple officielle | Interpretation |
|-------|---------------------------|----------------|
| data.transaction.status | TS | Transaction Successful |
| status.response_code | DP00900001001 | Product-specific success code |
| status.success | true | Pas d'erreur ESB |
| data.transaction.id | Partner transaction id | Idempotence key externe |

---

## Airtel — Refund succes (reference)

Source : `Airtel.txt` **imt/v1/refund** — 200 response sample.

| Champ | Valeur exemple officielle | Interpretation |
|-------|---------------------------|----------------|
| data.transaction.status | TR | Transaction Reversed |
| status.response_code | DP03520001001 | Refund success |
| status.success | true | Renversement confirme |

---

## Matrice cross-provider — quand faire une enquiry

| Signal | MTN | Airtel | Regle unifiee |
|--------|-----|--------|---------------|
| Requete acceptee, statut inconnu | HTTP 202 PENDING | HTTP 200 + TIP/TA/0000900 | Ne pas finaliser wallet sans statut final |
| Duplicate external ID | 409 RESOURCE_ALREADY_EXIST | ESB000041 | GET enquiry avant tout nouveau POST |
| Timeout | COULD_NOT_PERFORM_TRANSACTION (5 min) | ROUTER117 / HTTP 408/504 | Enquiry obligatoire |
| Callback manquant | GET /requesttopay/{id} | GET /payments/{id} ou /disbursements/{id} | Fallback poll documente officiellement MTN ; Airtel >= 1 min |
| Succes wallet credit | SUCCESSFUL / SUCCESS | TS + DP01000001001 ou DP00900001001 | Verifier les deux niveaux status |

---

## Endpoints officiels Congo (CG)

| Provider | Environnement | Base URL |
|----------|---------------|----------|
| Airtel | UAT | https://openapiuat.airtel.cg |
| Airtel | Production | https://openapi.airtel.cg |
| MTN | Sandbox | https://sandbox.momodeveloper.mtn.com |
| MTN | Production | https://momoapi.mtn.com (profil production) |

Headers Airtel CG : `X-Country: CG`, `X-Currency: XAF`, `Authorization: Bearer {token}`.
