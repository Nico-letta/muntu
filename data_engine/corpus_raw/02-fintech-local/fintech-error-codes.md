# Fintech Error Codes and Routing Matrix

## 1. MTN Common Error Codes
| HTTP | Response Code | Description | Action |
|------|---------------|-------------|--------|
| `409` | `RESOURCE_ALREADY_EXIST` | Duplicated Reference ID. Every request must use a unique UUID V4. | Generate new `X-Reference-Id` |
| `401` | `ACCESS DENIED DUE TO INVALID SUBSCRIPTION KEY` | Invalid `Ocp-Apim-Subscription-Key`. Collection, Disbursement, Remittance have different keys. | Verify profile key; try secondary key; contact MTN support |
| `404` | `RESOURCE NOT FOUND` | Reference ID not found in Get Status. Original request may have failed. | Verify original POST returned `202 Accepted` |
| `400` | `REQUEST REJECTED/ BAD REQUEST` | Headers/body violate spec. | Validate UUID v4, currency, no unsupported chars, note <=160 chars, correct URL |
| `403` | `FORBIDDEN IP` | IP not authorized for Disbursement API. | Whitelist public IP with MTN Account Manager |
| `500` | `NOT_ALLOWED` | Token/user lacks permission. | Contact MTN Account Manager |
| `500` | `NOT_ALLOWED_TARGET_ENVIRONMENT` | Wrong `X-Target-Environment` for country. | Use correct env (see matrix §2) |
| `500` | `INVALID_CALLBACK_URL_HOST` | Callback host mismatch vs API user config. | Use hostname not IP; match portal config |
| `500` | `INVALID_CURRENCY` | Currency unsupported for target account. | Use country-specific currency code |
| `503` | `SERVICE_UNAVAILABLE` | Platform temporarily unavailable. | Retry later or escalate to MTN |

## 2. MTN Target Environment Matrix
| Pays | X-Target-Environment |
|------|---------------------|
| MTN Uganda | `mtnuganda` |
| MTN Ghana | `mtnghana` |
| MTN Ivory Coast | `mtnivorycoast` |
| MTN Zambia | `mtnzambia` |
| MTN Cameroon | `mtncameroon` |
| MTN Benin | `mtnbenin` |
| MTN Congo | `mtncongo` |
| MTN Swaziland | `mtnswaziland` |
| MTN GuineaConakry | `mtnguineaconakry` |
| MTN SouthAfrica | `mtnsouthafrica` |
| MTN Liberia | `mtnliberia` |
| MTN SouthSudan | `mtnsouthsudan` |
| MTN Nigeria | `mtnnigeria` |
| MTN Rwanda | `mtnrwanda` |
| Sandbox | `sandbox` |

## 3. MTN Common Error Responses (business layer)
| Type | Description | Action |
|------|-------------|--------|
| `INTERNAL_PROCESSING_ERROR` | Generic failure; often insufficient funds or wallet unreachable. | Customer retries with sufficient funds; escalate if persists |
| `PAYEE_NOT_FOUND` | Payee MSISDN invalid or not registered. | MSISDN must include country code |
| `PAYER_NOT_FOUND` | Payer MSISDN invalid or not registered. | MSISDN must include country code |
| `COULD_NOT_PERFORM_TRANSACTION` | Timeout; approval delay beyond 5 minutes. | Retry and approve within 5 min window |

## 4. MTN Sandbox test value routing (extrait)
| Use Case | Test Value | Expected Error |
|----------|------------|----------------|
| RequestToPayPayerNotFound | `46733123455` | Payer not found |
| RequestToPayPayerNotAllowedTargetEnvironment | `46733123458` | Wrong target env |
| RequestToPayPayerInvalidCallbackUrlHost | `46733123459` | Callback host invalid |
| RequestToPayPayerInvalidCurrency | `46733123460` | Invalid currency |
| RequestToPayPayerInternalProcessingError | `46733123461` | Internal processing |
| RequestToPayPayerCouldNotPerformTransaction | `46733123463` | Timeout |
| TransferPayeeNotEnoughFunds | `46733123455` | Insufficient funds |
| TransferPayeeNotFound | `46733123457` | Payee not found |
| PaymentAmountFailed | `2000` | Payment failed |
| PaymentAmountSuccess | `1000` | Payment success |

## 5. Airtel Common Error Codes (ROUTER)
| Code | Description | Handling |
|------|-------------|----------|
| `ROUTER001` | Wallet is not configured - Application Wallet not configured. | Configure wallet in dev portal before API calls |
| `ROUTER003` | Missing header/body params - mandatory field absent. | Validate all required headers and body fields |
| `ROUTER005` | Country route not configured. | Contact Airtel customer support |
| `ROUTER006` | Invalid Country - incorrect country code. | Use `CG` for Congo-Brazzaville |
| `ROUTER007` | User Not authorized for provided country. | Verify account country permissions |
| `ROUTER112` | Invalid Currency - incorrect currency code. | Use `XAF` for Congo-Brazzaville |
| `ROUTER114` | Error while Validating Pin. | Check PIN encryption (RSA 2048 OAEP) |
| `ROUTER115` | Incorrect Pin. | Re-prompt user for correct PIN |
| `ROUTER116` | Incorrect Encrypted Pin - encryption mechanism error. | Review RSA encryption implementation |
| `ROUTER117` | Request Timeout - ambiguous for payments/refund. | Perform transaction enquiry |
| `ROUTER119` | Invalid/Missing Currency in request parameters. | Inject `X-Currency: XAF` |

## 6. Airtel Product Specific Error Codes (ESB)
| Code | Description | Handling |
|------|-------------|----------|
| `ESB000001` | Something went wrong - ambiguous state. | Transaction enquiry |
| `ESB000004` | Error initiating payment - ambiguous state. | Transaction enquiry |
| `ESB000008` | Field validation error - ambiguous state. | Fix input + transaction enquiry |
| `ESB000010` | Request was Success. | Proceed |
| `ESB000011` | Request was Failed. | Fail workflow, log payload |
| `ESB000014` | Error fetching transaction status - ambiguous. | Retry enquiry after delay |
| `ESB000033` | Invalid MSISDN Length. | Fix MSISDN format |
| `ESB000034` | Invalid Country Name. | Use `CG` |
| `ESB000035` | Invalid Currency Code. | Use `XAF` |
| `ESB000036` | Invalid MSISDN length or doesn't start with 0. | Fix MSISDN local format |
| `ESB000039` | Vendor not configured for country. | Contact Airtel support |
| `ESB000041` | External Transaction ID already exists. | Generate new unique transaction id |
| `ESB000045` | No Transaction Found With Provided Transaction Id. | Verify id, re-enquire |
| `0000900` | Transaction might be in ambiguous state. | Check `response_code` or perform enquiry |

## 7. Airtel HTTP Error Codes
| HTTP | Description | Handling |
|------|-------------|----------|
| `400` | Bad Request - invalid request. | Fix input |
| `401` | Unauthorized - API key or bearer token incorrect. | Refresh OAuth2 token |
| `403` | Forbidden. | Check permissions |
| `404` | Not Found - path not found. | Verify endpoint URL |
| `405` | Method Not Allowed. | Use correct HTTP verb |
| `408` | Read Timeout - ambiguous for payments/refund. | Transaction enquiry |
| `429` | Too Many Requests. | Apply backoff |
| `500` | Internal Server Error. | Retry later |
| `502` | Bad Gateway - ambiguous for payments/refund. | Transaction enquiry |
| `503` | Service Unavailable. | Retry later |
| `504` | Gateway Timeout - ambiguous for payments/refund. | Transaction enquiry |

## 8. Airtel Cash-In Error Codes (DP01*)
| Code | Reason | Description |
|------|--------|-------------|
| `DP01000001000` | Ambiguous | Still processing - perform enquiry |
| `DP01000001001` | Success | Transaction successful |
| `DP01000001002` | Incorrect Pin | Wrong PIN entered |
| `DP01000001003` | Limit exceeded | Wallet transaction limit exceeded |
| `DP01000001004` | Invalid Amount | Below minimum amount |
| `DP01000001005` | Failed | Transaction failed |
| `DP01000001006` | In Process | Pending - check later |
| `DP01000001007` | Insufficient Funds | Wallet balance too low |
| `DP01000001008` | User Not Allowed | Payer not permitted |
| `DP01000001009` | Initiatee Invalid | Invalid initiatee |
| `DP01000001010` | Not Permitted | User not allowed as payer |
| `DP01000001011` | Do Not Honour | Transaction already completed |
| `DP01000001012` | Invalid Mobile Number | MSISDN incorrect or unregistered |
| `DP01000001013` | Failed/Refused | Transaction failed or refused |
| `DP01000001014` | Transaction Timed Out | Ambiguous - perform enquiry |

## 9. Airtel Bank-to-Wallet Error Codes (DP02*)
| Code | Reason | Description |
|------|--------|-------------|
| `DP02100001000` | Ambiguous | Processing or ambiguous - perform enquiry |
| `DP02100001001` | Success | Transaction successful |
| `DP02100001002` | Duplicate Transaction ID | Use unique transaction id |
| `DP02100001003` | Transaction Time Out | Perform enquiry |
| `DP02100001004` | Transaction Not Found | Verify transaction id |
| `DP02100001005` | Failed | Transaction failed or refused |
| `DP02100001006` | Transaction In Progress | Perform enquiry |
| `DP02100001007` | Invalid Input | One input field is invalid |

## 10. Airtel Remittance Refund - response_code mapping
| response_code | transaction.status | Signification |
|---------------|-------------------|---------------|
| `DP03520001001` | `TR` | Transaction Reversed - remboursement réussi |

## 11. Airtel Transaction Status Codes
| Code | Signification | airtel_money_id généré ? |
|------|---------------|---------------------------|
| `TS` | Transaction Success | Oui |
| `TF` | Transaction Failed | Non |
| `TIP` | Transaction in Progress | Non |
| `TA` | Transaction Ambiguous | Non |
| `TR` | Transaction Reversed | Oui (refund) |

## 12. Country / Currency Reference Matrix (Airtel Africa)
| Country | Currency | Country Code | Currency Code |
|---------|----------|--------------|---------------|
| UGANDA | Ugandan shilling | `UG` | `UGX` |
| NIGERIA | Nigerian naira | `NG` | `NGN` |
| TANZANIA | Tanzanian shilling | `TZ` | `TZS` |
| KENYA | Kenyan shilling | `KE` | `KES` |
| RWANDA | Rwandan franc | `RW` | `RWF` |
| ZAMBIA | Zambian kwacha | `ZM` | `ZMW` |
| GABON | CFA franc BEAC | `GA` | `CFA` |
| NIGER | CFA franc BCEAO | `NE` | `XOF` |
| **CONGO-BRAZZAVILLE** | **CFA franc BCEA** | **`CG`** | **`XAF`** |
| DR CONGO | Congolese franc | `CD` | `CDF` |
| DR CONGO | United States dollar | `CD` | `USD` |
| CHAD | CFA franc BEAC | `TD` | `XAF` |
| SEYCHELLES | Seychelles rupee | `SC` | `SCR` |
| MADAGASCAR | Malagasy ariary | `MG` | `MGA` |
| MALAWI | Malawian kwacha | `MW` | `MWK` |

## 13. Cross-provider error harmonization
### Wallet operations
| Symptom | MTN | Airtel |
|---------|-----|--------|
| Duplicate reference | `409 RESOURCE_ALREADY_EXIST` | `ESB000041` |
| Invalid subscription/key | `401 ACCESS DENIED...` | `401 Unauthorized` |
| Wrong country env | `500 NOT_ALLOWED_TARGET_ENVIRONMENT` | `ROUTER006` / `ROUTER007` |
| Wrong currency | `500 INVALID_CURRENCY` | `ROUTER112` / `ROUTER119` |
| Insufficient funds | `INTERNAL_PROCESSING_ERROR` | `DP01000001007` |
| Invalid MSISDN | `PAYEE_NOT_FOUND` / `PAYER_NOT_FOUND` | `DP01000001012` / `ESB000033` |
| Timeout / ambiguous | `COULD_NOT_PERFORM_TRANSACTION` | `ROUTER117` / `0000900` / `DP*10000` |
| Callback host mismatch | `500 INVALID_CALLBACK_URL_HOST` | N/A (config portal) |

### Bank-to-Wallet
| Symptom | Airtel code | Action |
|---------|-------------|--------|
| Duplicate txn id | `DP02100001002` | New unique id |
| Ambiguous state | `DP02100001000` / `DP02100001006` | Transaction enquiry |
| Timeout | `DP02100001003` | Transaction enquiry |

## 14. Error handling patterns (intégration)
- Valider body/headers avant appel API.
- `400` / `422` -> corriger input ou rejeter côté client.
- `401` / `403` -> rotation token ou alerte équipe intégration.
- `409` / `ESB000041` -> générer nouveau reference/transaction id.
- `429` -> backoff exponentiel.
- `500` / `502` / `504` -> retry si idempotent, sinon alerte ops.
- `202` + `PENDING` / `TIP` -> poll status ou attendre callback.
- Toujours logger: `request_id`, `X-Reference-Id`, `transaction.id`, `response_code`, `provider_message`, `route_country`.

## 15. Token-efficient troubleshooting guide
1. Vérifier `X-Reference-Id` (MTN) ou `transaction.id` (Airtel) - unicité.
2. Vérifier headers géo: `X-Country: CG` + `X-Currency: XAF` (Airtel Congo) ou `X-Target-Environment: mtncongo` (MTN Congo prod).
3. Si `duplicate_request` -> retourner résultat stocké, ne pas re-débiter.
4. Si `timeout` + appel idempotent -> une seule retry puis enquiry.
5. Si `business_rule` failure -> message utilisateur friendly (PIN incorrect, fonds insuffisants).
6. Si `ambiguous` (`TA`, `TIP`, `0000900`, `DP*10000`) -> transaction enquiry obligatoire avant toute action corrective.
7. Si callback manquant -> GET status; ne jamais supposer succès sur seul `202 Accepted`.
8. `DP03520001001` + `TR` = renversement confirmé côté Airtel remittance.
