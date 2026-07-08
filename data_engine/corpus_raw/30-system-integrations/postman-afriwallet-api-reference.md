# AfriWallet — Reference API Postman

> Source: `afriwallet_codebase/postman/AfriWallet.postman_collection.json`

## Dossiers collection

- **Health** — sante API
- **Users** — register, lookup phone
- **Auth** — OTP, PIN, reset PIN
- **KYC** — Smile ID, SmartSelfie
- **Wallets** — solde, transactions
- **Payments** — MoMo, Bridge, polling
- **Virtual Cards** — Onafriq
- **Webhooks** — MTN, Smile, Onafriq, Bridge

## Collection JSON complete

```json
{
  "info": {
    "_postman_id": "c5d9a8b7-2e3c-4f1d-4f1d-afriwallet-backend-local",
    "name": "AfriWallet Backend (Local)",
    "description": "Collection AfriWallet API : auth (OTP, PIN, reset PIN), users, KYC Smile, wallets, cartes, paiements MTN/Bridge, webhooks (MTN, Smile ID, Onafriq, Bridge). Voir /docs (Swagger) pour le détail des schémas.",
    "schema": "https://schema.getpostman.com/json/collection/v2.1.0/collection.json"
  },
  "item": [
    {
      "name": "Health",
      "item": [
        {
          "name": "API Root",
          "request": {
            "method": "GET",
            "header": [],
            "url": {
              "raw": "{{baseUrl}}/",
              "host": [
                "{{baseUrl}}"
              ],
              "path": [
                ""
              ]
            }
          }
        },
        {
          "name": "Users Health",
          "request": {
            "method": "GET",
            "header": [],
            "url": {
              "raw": "{{baseUrl}}/users/health",
              "host": [
                "{{baseUrl}}"
              ],
              "path": [
                "users",
                "health"
              ]
            }
          }
        }
      ]
    },
    {
      "name": "Users",
      "item": [
        {
          "name": "Register User",
          "request": {
            "method": "POST",
            "header": [
              {
                "key": "Content-Type",
                "name": "Content-Type",
                "value": "application/json",
                "type": "text"
              }
            ],
            "body": {
              "mode": "raw",
              "raw": "{\n  \"phoneNumber\": \"{{phoneNumber}}\",\n  \"pin\": \"1234\"\n}"
            },
            "url": {
              "raw": "{{baseUrl}}/users/register",
              "host": [
                "{{baseUrl}}"
              ],
              "path": [
                "users",
                "register"
              ]
            }
          }
        },
        {
          "name": "Lookup User by Phone",
          "request": {
            "method": "POST",
            "header": [
              {
                "key": "Content-Type",
                "name": "Content-Type",
                "value": "application/json",
                "type": "text"
              }
            ],
            "body": {
              "mode": "raw",
              "raw": "{\n  \"phoneNumber\": \"{{phoneNumber}}\"\n}"
            },
            "url": {
              "raw": "{{baseUrl}}/users/lookup",
              "host": [
                "{{baseUrl}}"
              ],
              "path": [
                "users",
                "lookup"
              ]
            }
          }
        }
      ]
    },
    {
      "name": "Auth (OTP & PIN)",
      "item": [
        {
          "name": "Request OTP",
          "request": {
            "method": "POST",
            "header": [
              {
                "key": "Content-Type",
                "name": "Content-Type",
                "value": "application/json",
                "type": "text"
              }
            ],
            "body": {
              "mode": "raw",
              "raw": "{\n  \"phoneNumber\": \"{{phoneNumber}}\"\n}"
            },
            "url": {
              "raw": "{{baseUrl}}/auth/otp/request",
              "host": [
                "{{baseUrl}}"
              ],
              "path": [
                "auth",
                "otp",
                "request"
              ]
            }
          }
        },
        {
          "name": "Verify OTP & Set PIN",
          "request": {
            "method": "POST",
            "header": [
              {
                "key": "Content-Type",
                "name": "Content-Type",
                "value": "application/json",
                "type": "text"
              }
            ],
            "body": {
              "mode": "raw",
              "raw": "{\n  \"phoneNumber\": \"{{phoneNumber}}\",\n  \"otp\": \"123456\",\n  \"pin\": \"1234\"\n}"
            },
            "url": {
              "raw": "{{baseUrl}}/auth/otp/verify",
              "host": [
                "{{baseUrl}}"
              ],
              "path": [
                "auth",
                "otp",
                "verify"
              ]
            }
          }
        },
        {
          "name": "Verify PIN",
          "request": {
            "method": "POST",
            "header": [
              {
                "key": "Content-Type",
                "name": "Content-Type",
                "value": "application/json",
                "type": "text"
              }
            ],
            "body": {
              "mode": "raw",
              "raw": "{\n  \"phoneNumber\": \"{{phoneNumber}}\",\n  \"pin\": \"1234\"\n}"
            },
            "url": {
              "raw": "{{baseUrl}}/auth/pin/verify",
              "host": [
                "{{baseUrl}}"
              ],
              "path": [
                "auth",
                "pin",
                "verify"
              ]
            }
          }
        },
        {
          "name": "PIN reset — Request OTP",
          "request": {
            "method": "POST",
            "header": [
              {
                "key": "Content-Type",
                "name": "Content-Type",
                "value": "application/json",
                "type": "text"
              }
            ],
            "body": {
              "mode": "raw",
              "raw": "{\n  \"phoneNumber\": \"{{phoneNumber}}\"\n}"
            },
            "description": "Compte déjà existant uniquement (sinon 404). Même OTP que l’activation (SMS / réponse dev). Ne pas confondre avec POST /auth/otp/request (nouveau numéro).",
            "url": {
              "raw": "{{baseUrl}}/auth/pin/reset/request",
              "host": [
                "{{baseUrl}}"
              ],
              "path": [
                "auth",
                "pin",
                "reset",
                "request"
              ]
            }
          }
        },
        {
          "name": "PIN reset — Verify OTP + new PIN",
          "request": {
            "method": "POST",
            "header": [
              {
                "key": "Content-Type",
                "name": "Content-Type",
                "value": "application/json",
                "type": "text"
              }
            ],
            "body": {
              "mode": "raw",
              "raw": "{\n  \"phoneNumber\": \"{{phoneNumber}}\",\n  \"otp\": \"123456\",\n  \"pin\": \"5678\"\n}"
            },
            "description": "Après pin/reset/request : le champ pin est le NOUVEAU code (pas l’ancien). Retourne JWT + wallets. Ne pas utiliser pour la première inscription (utiliser otp/verify).",
            "url": {
              "raw": "{{baseUrl}}/auth/pin/reset/verify",
              "host": [
                "{{baseUrl}}"
              ],
              "path": [
                "auth",
                "pin",
                "reset",
                "verify"
              ]
            }
          }
        },
        {
          "name": "Authenticated call example (Get wallet transactions)",
          "request": {
            "method": "GET",
            "header": [
              {
                "key": "Authorization",
                "name": "Authorization",
                "value": "Bearer {{accessToken}}",
                "type": "text"
              }
            ],
            "url": {
              "raw": "{{baseUrl}}/wallets/WALLET_ID_TO_REPLACE/transactions",
              "host": [
                "{{baseUrl}}"
              ],
              "path": [
                "wallets",
                "WALLET_ID_TO_REPLACE",
                "transactions"
              ]
            }
          }
        }
      ]
    },
    {
      "name": "KYC",
      "item": [
        {
          "name": "Start KYC",
          "request": {
            "method": "POST",
            "header": [
              {
                "key": "Content-Type",
                "name": "Content-Type",
                "value": "application/json",
                "type": "text"
              }
            ],
            "body": {
              "mode": "raw",
              "raw": "{\n  \"userId\": \"USER_ID_TO_REPLACE\"\n}"
            },
            "url": {
              "raw": "{{baseUrl}}/kyc/start",
              "host": [
                "{{baseUrl}}"
              ],
              "path": [
                "kyc",
                "start"
              ]
            }
          }
        },
        {
          "name": "Get Smile ID signature",
          "request": {
            "method": "POST",
            "header": [],
            "url": {
              "raw": "{{baseUrl}}/kyc/signature",
              "host": [
                "{{baseUrl}}"
              ],
              "path": [
                "kyc",
                "signature"
              ]
            }
          }
        },
        {
          "name": "Biometric KYC (SDK style)",
          "request": {
            "method": "POST",
            "header": [
              {
                "key": "Content-Type",
                "name": "Content-Type",
                "value": "application/json",
                "type": "text"
              },
              {
                "key": "Authorization",
                "name": "Authorization",
                "value": "Bearer {{accessToken}}",
                "type": "text"
              }
            ],
            "body": {
              "mode": "raw",
              "raw": "{\n  \"firstName\": \"John\",\n  \"lastName\": \"Doe\",\n  \"country\": \"NG\",\n  \"idType\": \"NIN_V2\",\n  \"idNumber\": \"00000000000\",\n  \"dob\": \"1990-01-01\",\n  \"imageDetails\": [\n    {\n      \"image_type_id\": 2,\n      \"image\": \"BASE64_IMAGE_TO_REPLACE\"\n    }\n  ],\n  \"returnJobStatus\": true,\n  \"returnHistory\": false,\n  \"returnImageLinks\": false\n}"
            },
            "url": {
              "raw": "{{baseUrl}}/kyc/biometric",
              "host": [
                "{{baseUrl}}"
              ],
              "path": [
                "kyc",
                "biometric"
              ]
            }
          }
        },
        {
          "name": "Biometric KYC - Request Upload URL (recommended)",
          "request": {
            "method": "POST",
            "header": [
              {
                "key": "Content-Type",
                "name": "Content-Type",
                "value": "application/json",
                "type": "text"
              },
              {
                "key": "Authorization",
                "name": "Authorization",
                "value": "Bearer {{accessToken}}",
                "type": "text"
              }
            ],
            "body": {
              "mode": "raw",
              "raw": "{\n  \"firstName\": \"John\",\n  \"lastName\": \"Doe\",\n  \"country\": \"NG\",\n  \"idType\": \"NIN_V2\",\n  \"idNumber\": \"00000000000\",\n  \"dob\": \"1990-01-01\",\n  \"fileName\": \"biometric_kyc_ng_nin_v2.zip\",\n  \"sandboxResult\": \"0\",\n  \"modelParameters\": {}\n}"
            },
            "url": {
              "raw": "{{baseUrl}}/kyc/biometric/upload-url",
              "host": [
                "{{baseUrl}}"
              ],
              "path": [
                "kyc",
                "biometric",
                "upload-url"
              ]
            }
          },
          "event": [
            {
              "listen": "test",
              "script": {
                "type": "text/javascript",
                "exec": [
                  "let data = {};",
                  "try {",
                  "  data = pm.response.json();",
                  "} catch (e) {",
                  "  pm.test('Response is valid JSON', function () {",
                  "    throw new Error('Invalid JSON response');",
                  "  });",
                  "}",
                  "",
                  "pm.test('Biometric upload URL is returned', function () {",
                  "  pm.expect(data).to.have.property('upload');",
                  "  pm.expect(data.upload).to.have.property('upload_url');",
                  "  pm.expect(data.upload.upload_url).to.be.a('string').and.not.empty;",
                  "});",
                  "",
                  "pm.test('Biometric jobId is returned', function () {",
                  "  pm.expect(data).to.have.property('jobId');",
                  "  pm.expect(data.jobId).to.be.a('string').and.not.empty;",
                  "});",
                  "",
                  "if (data.upload && data.upload.upload_url) {",
                  "  pm.environment.set('biometricUploadUrl', data.upload.upload_url);",
                  "}",
                  "if (data.jobId) {",
                  "  pm.environment.set('biometricJobId', data.jobId);",
                  "}"
                ]
              }
            }
          ]
        },
        {
          "name": "Biometric KYC - Upload ZIP to signed URL",
          "request": {
            "method": "POST",
            "header": [
              {
                "key": "Content-Type",
                "name": "Content-Type",
                "value": "application/json",
                "type": "text"
              },
              {
                "key": "Authorization",
                "name": "Authorization",
                "value": "Bearer {{accessToken}}",
                "type": "text"
              }
            ],
            "body": {
              "mode": "raw",
              "raw": "{\n  \"uploadUrl\": \"{{biometricUploadUrl}}\",\n  \"zipBase64\": \"{{zipBase64Biometric}}\"\n}"
            },
            "url": {
              "raw": "{{baseUrl}}/kyc/biometric/upload-zip",
              "host": [
                "{{baseUrl}}"
              ],
              "path": [
                "kyc",
                "biometric",
                "upload-zip"
              ]
            }
          },
          "event": [
            {
              "listen": "test",
              "script": {
                "type": "text/javascript",
                "exec": [
                  "let data = {};",
                  "try {",
                  "  data = pm.response.json();",
                  "} catch (e) {",
                  "  pm.test('Response is valid JSON', function () {",
                  "    throw new Error('Invalid JSON response');",
                  "  });",
                  "}",
                  "",
                  "pm.test('Biometric ZIP upload succeeded', function () {",
                  "  pm.expect(data).to.have.property('uploaded');",
                  "  pm.expect(data.uploaded).to.eql(true);",
                  "});",
                  "",
                  "// Runner only: chain automatically to job status polling request.",
                  "if (typeof postman !== 'undefined' && typeof postman.setNextRequest === 'function') {",
                  "  postman.setNextRequest('Smile Utility - Job Status');",
                  "}"
                ]
              }
            }
          ]
        },
        {
          "name": "SmartSelfie Auth (SDK style)",
          "request": {
            "method": "POST",
            "header": [
              {
                "key": "Content-Type",
                "name": "Content-Type",
                "value": "application/json",
                "type": "text"
              },
              {
                "key": "Authorization",
                "name": "Authorization",
                "value": "Bearer {{accessToken}}",
                "type": "text"
              }
            ],
            "body": {
              "mode": "raw",
              "raw": "{\n  \"jobId\": \"\",\n  \"reason\": \"large_withdrawal\",\n  \"imageDetails\": [\n    {\n      \"image_type_id\": 2,\n      \"image\": \"BASE64_IMAGE_TO_REPLACE\"\n    }\n  ],\n  \"returnJobStatus\": true,\n  \"returnHistory\": false,\n  \"returnImageLinks\": false\n}"
            },
            "url": {
              "raw": "{{baseUrl}}/kyc/smartselfie/auth",
              "host": [
                "{{baseUrl}}"
              ],
              "path": [
                "kyc",
                "smartselfie",
                "auth"
              ]
            }
          }
        },
        {
          "name": "SmartSelfie Auth - Request Upload URL (recommended)",
          "request": {
            "method": "POST",
            "header": [
              {
                "key": "Content-Type",
                "name": "Content-Type",
                "value": "application/json",
                "type": "text"
              },
              {
                "key": "Authorization",
                "name": "Authorization",
                "value": "Bearer {{accessToken}}",
                "type": "text"
              }
            ],
            "body": {
              "mode": "raw",
              "raw": "{\n  \"reason\": \"large_withdrawal\",\n  \"fileName\": \"selfie.zip\",\n  \"modelParameters\": {},\n  \"retry\": false\n}"
            },
            "url": {
              "raw": "{{baseUrl}}/kyc/smartselfie/auth/upload-url",
              "host": [
                "{{baseUrl}}"
              ],
              "path": [
                "kyc",
                "smartselfie",
                "auth",
                "upload-url"
              ]
            }
          }
        },
        {
          "name": "SmartSelfie Register - Request Upload URL",
          "request": {
            "method": "POST",
            "header": [
              {
                "key": "Content-Type",
                "name": "Content-Type",
                "value": "application/json",
                "type": "text"
              },
              {
                "key": "Authorization",
                "name": "Authorization",
                "value": "Bearer {{accessToken}}",
                "type": "text"
              }
            ],
            "body": {
              "mode": "raw",
              "raw": "{\n  \"reason\": \"wallet_recovery\",\n  \"fileName\": \"selfie.zip\",\n  \"modelParameters\": {},\n  \"retry\": false\n}"
            },
            "url": {
              "raw": "{{baseUrl}}/kyc/smartselfie/register/upload-url",
              "host": [
                "{{baseUrl}}"
              ],
              "path": [
                "kyc",
                "smartselfie",
                "register",
                "upload-url"
              ]
            }
          }
        },
        {
          "name": "SmartSelfie - Confirm (persist DB)",
          "request": {
            "method": "POST",
            "header": [
              {
                "key": "Content-Type",
                "name": "Content-Type",
                "value": "application/json",
                "type": "text"
              },
              {
                "key": "Authorization",
                "name": "Authorization",
                "value": "Bearer {{accessToken}}",
                "type": "text"
              }
            ],
            "body": {
              "mode": "raw",
              "raw": "{\n  \"jobId\": \"JOB_ID_TO_CONFIRM\",\n  \"history\": true,\n  \"imageLinks\": false\n}"
            },
            "url": {
              "raw": "{{baseUrl}}/kyc/smartselfie/confirm",
              "host": [
                "{{baseUrl}}"
              ],
              "path": [
                "kyc",
                "smartselfie",
                "confirm"
              ]
            }
          }
        },
        {
          "name": "SmartSelfie - Upload ZIP to signed URL",
          "request": {
            "method": "POST",
            "header": [
              {
                "key": "Content-Type",
                "name": "Content-Type",
                "value": "application/json",
                "type": "text"
              },
              {
                "key": "Authorization",
                "name": "Authorization",
                "value": "Bearer {{accessToken}}",
                "type": "text"
              }
            ],
            "body": {
              "mode": "raw",
              "raw": "{\n  \"uploadUrl\": \"UPLOAD_URL_FROM_PREVIOUS_STEP\",\n  \"zipBase64\": \"BASE64_ZIP_CONTENT\"\n}"
            },
            "url": {
              "raw": "{{baseUrl}}/kyc/smartselfie/upload-zip",
              "host": [
                "{{baseUrl}}"
              ],
              "path": [
                "kyc",
                "smartselfie",
                "upload-zip"
              ]
            }
          }
        },
        {
          "name": "Smile Utility - Job Status",
          "request": {
            "method": "POST",
            "header": [
              {
                "key": "Content-Type",
                "name": "Content-Type",
                "value": "application/json",
                "type": "text"
              },
              {
                "key": "Authorization",
                "name": "Authorization",
                "value": "Bearer {{accessToken}}",
                "type": "text"
              }
            ],
            "body": {
              "mode": "raw",
              "raw": "{\n  \"jobId\": \"{{biometricJobId}}\",\n  \"jobType\": \"1\",\n  \"history\": true,\n  \"imageLinks\": false\n}"
            },
            "url": {
              "raw": "{{baseUrl}}/kyc/utils/job-status",
              "host": [
                "{{baseUrl}}"
              ],
              "path": [
                "kyc",
                "utils",
                "job-status"
              ]
            }
          }
        },
        {
          "name": "Smile Utility - Reset ID Number Rate Limit",
          "request": {
            "method": "POST",
            "header": [
              {
                "key": "Content-Type",
                "name": "Content-Type",
                "value": "application/json",
                "type": "text"
              },
              {
                "key": "Authorization",
                "name": "Authorization",
                "value": "Bearer {{accessToken}}",
                "type": "text"
              }
            ],
            "body": {
              "mode": "raw",
              "raw": "{\n  \"country\": \"NG\",\n  \"idType\": \"NIN_V2\",\n  \"idNumber\": \"00000000000\"\n}"
            },
            "url": {
              "raw": "{{baseUrl}}/kyc/utils/id-number-rate-limit-reset",
              "host": [
                "{{baseUrl}}"
              ],
              "path": [
                "kyc",
                "utils",
                "id-number-rate-limit-reset"
              ]
            }
          }
        },
        {
          "name": "Document Verification CG (SDK style)",
          "request": {
            "method": "POST",
            "header": [
              {
                "key": "Content-Type",
                "name": "Content-Type",
                "value": "application/json",
                "type": "text"
              },
              {
                "key": "Authorization",
                "name": "Authorization",
                "value": "Bearer {{accessToken}}",
                "type": "text"
              }
            ],
            "body": {
              "mode": "raw",
              "raw": "{\n  \"country\": \"CG\",\n  \"idType\": \"IDENTITY_CARD\",\n  \"imageDetails\": [\n    {\n      \"image_type_id\": 0,\n      \"image\": \"BASE64_SELFIE_IMAGE\"\n    },\n    {\n      \"image_type_id\": 1,\n      \"image\": \"BASE64_ID_FRONT_IMAGE\"\n    },\n    {\n      \"image_type_id\": 5,\n      \"image\": \"BASE64_ID_BACK_IMAGE\"\n    }\n  ]\n}"
            },
            "url": {
              "raw": "{{baseUrl}}/kyc/document-verification",
              "host": [
                "{{baseUrl}}"
              ],
              "path": [
                "kyc",
                "document-verification"
              ]
            }
          }
        },
        {
          "name": "Document Verification CG - Request Upload URL",
          "request": {
            "method": "POST",
            "header": [
              {
                "key": "Content-Type",
                "name": "Content-Type",
                "value": "application/json",
                "type": "text"
              },
              {
                "key": "Authorization",
                "name": "Authorization",
                "value": "Bearer {{accessToken}}",
                "type": "text"
              }
            ],
            "body": {
              "mode": "raw",
              "raw": "{\n  \"country\": \"CG\",\n  \"idType\": \"IDENTITY_CARD\",\n  \"fileName\": \"attachments.zip\",\n  \"sandboxResult\": \"0\",\n  \"modelParameters\": {}\n}"
            },
            "url": {
              "raw": "{{baseUrl}}/kyc/document-verification/upload-url",
              "host": [
                "{{baseUrl}}"
              ],
              "path": [
                "kyc",
                "document-verification",
                "upload-url"
              ]
            }
          }
        },
        {
          "name": "Document Verification CG - Upload ZIP",
          "request": {
            "method": "POST",
            "header": [
              {
                "key": "Content-Type",
                "name": "Content-Type",
                "value": "application/json",
                "type": "text"
              },
              {
                "key": "Authorization",
                "name": "Authorization",
                "value": "Bearer {{accessToken}}",
                "type": "text"
              }
            ],
            "body": {
              "mode": "raw",
              "raw": "{\n  \"uploadUrl\": \"UPLOAD_URL_FROM_PREVIOUS_STEP\",\n  \"zipBase64\": \"BASE64_ZIP_CONTENT\"\n}"
            },
            "url": {
              "raw": "{{baseUrl}}/kyc/document-verification/upload-zip",
              "host": [
                "{{baseUrl}}"
              ],
              "path": [
                "kyc",
                "document-verification",
                "upload-zip"
              ]
            }
          }
        }
      ]
    },
    {
      "name": "MTN MoMo (Sandbox Provisioning)",
      "item": [
        {
          "name": "Create API User (Sandbox)",
          "request": {
            "method": "POST",
            "header": [
              {
                "key": "Content-Type",
                "name": "Content-Type",
                "value": "application/json",
                "type": "text"
              },
              {
                "key": "X-Reference-Id",
                "name": "X-Reference-Id",
                "value": "{{mtnApiUser}}",
                "type": "text"
              },
              {
                "key": "Ocp-Apim-Subscription-Key",
                "name": "Ocp-Apim-Subscription-Key",
                "value": "{{mtnCollectionsSubscriptionKey}}",
                "type": "text"
              }
            ],
            "body": {
              "mode": "raw",
              "raw": "{\n  \"providerCallbackHost\": \"{{mtnProviderCallbackHost}}\"\n}"
            },
            "url": {
              "raw": "{{mtnSandboxBaseUrl}}/v1_0/apiuser",
              "host": [
                "{{mtnSandboxBaseUrl}}"
              ],
              "path": [
                "v1_0",
                "apiuser"
              ]
            }
          },
          "event": [
            {
              "listen": "prerequest",
              "script": {
                "type": "text/javascript",
                "exec": [
                  "if (!pm.environment.get('mtnApiUser')) {",
                  "  // Génère un UUID v4 si vide",
                  "  pm.environment.set('mtnApiUser', pm.variables.replaceIn('{{$guid}}'));",
                  "}"
                ]
              }
            }
          ]
        },
        {
          "name": "Create API Key for API User (Sandbox)",
          "request": {
            "method": "POST",
            "header": [
              {
                "key": "Ocp-Apim-Subscription-Key",
                "name": "Ocp-Apim-Subscription-Key",
                "value": "{{mtnCollectionsSubscriptionKey}}",
                "type": "text"
              }
            ],
            "url": {
              "raw": "{{mtnSandboxBaseUrl}}/v1_0/apiuser/{{mtnApiUser}}/apikey",
              "host": [
                "{{mtnSandboxBaseUrl}}"
              ],
              "path": [
                "v1_0",
                "apiuser",
                "{{mtnApiUser}}",
                "apikey"
              ]
            }
          },
          "event": [
            {
              "listen": "test",
              "script": {
                "type": "text/javascript",
                "exec": [
                  "let data = {};",
                  "try {",
                  "  data = pm.response.json();",
                  "} catch (e) {",
                  "  pm.test('Response is valid JSON', function () {",
                  "    throw new Error('Invalid JSON response');",
                  "  });",
                  "}",
                  "pm.test('apiKey is returned', function () {",
                  "  pm.expect(data).to.have.property('apiKey');",
                  "  pm.expect(data.apiKey).to.be.a('string').and.not.empty;",
                  "});",
                  "if (data.apiKey) {",
                  "  pm.environment.set('mtnApiKey', data.apiKey);",
                  "}"
                ]
              }
            }
          ]
        },
        {
          "name": "Get API User Details (Sandbox)",
          "request": {
            "method": "GET",
            "header": [
              {
                "key": "Ocp-Apim-Subscription-Key",
                "name": "Ocp-Apim-Subscription-Key",
                "value": "{{mtnCollectionsSubscriptionKey}}",
                "type": "text"
              }
            ],
            "url": {
              "raw": "{{mtnSandboxBaseUrl}}/v1_0/apiuser/{{mtnApiUser}}",
              "host": [
                "{{mtnSandboxBaseUrl}}"
              ],
              "path": [
                "v1_0",
                "apiuser",
                "{{mtnApiUser}}"
              ]
            }
          }
        }
      ]
    },
    {
      "name": "Webhooks & Payments",
      "item": [
        {
          "name": "Initiate MoMo deposit",
          "request": {
            "method": "POST",
            "header": [
              {
                "key": "Content-Type",
                "name": "Content-Type",
                "value": "application/json",
                "type": "text"
              },
              {
                "key": "Authorization",
                "name": "Authorization",
                "value": "Bearer {{accessToken}}",
                "type": "text"
              }
            ],
            "body": {
              "mode": "raw",
              "raw": "{\n  \"amountFcfa\": 5000\n}"
            },
            "url": {
              "raw": "{{baseUrl}}/payments/deposit/momo",
              "host": [
                "{{baseUrl}}"
              ],
              "path": [
                "payments",
                "deposit",
                "momo"
              ]
            }
          },
          "event": [
            {
              "listen": "test",
              "script": {
                "type": "text/javascript",
                "exec": [
                  "let data = {};",
                  "try { data = pm.response.json(); } catch (e) {}",
                  "if (data && data.referenceId) {",
                  "  pm.environment.set('mtnReferenceId', data.referenceId);",
                  "}"
                ]
              }
            }
          ]
        },
        {
          "name": "Get MoMo deposit status (polling fallback)",
          "request": {
            "method": "GET",
            "header": [
              {
                "key": "Authorization",
                "name": "Authorization",
                "value": "Bearer {{accessToken}}",
                "type": "text"
              }
            ],
            "url": {
              "raw": "{{baseUrl}}/payments/deposit/momo/{{mtnReferenceId}}/status",
              "host": [
                "{{baseUrl}}"
              ],
              "path": [
                "payments",
                "deposit",
                "momo",
                "{{mtnReferenceId}}",
                "status"
              ]
            }
          }
        },
        {
          "name": "MTN callback receiver (RequestToPay) - POST (manual test)",
          "request": {
            "method": "POST",
            "header": [
              {
                "key": "Content-Type",
                "name": "Content-Type",
                "value": "application/json",
                "type": "text"
              },
              {
                "key": "x-reference-id",
                "name": "x-reference-id",
                "value": "{{mtnReferenceId}}",
                "type": "text"
              }
            ],
            "body": {
              "mode": "raw",
              "raw": "{\n  \"status\": \"SUCCESSFUL\",\n  \"reason\": \"\",\n  \"financialTransactionId\": \"sandbox_tx_123\"\n}"
            },
            "url": {
              "raw": "{{baseUrl}}/webhooks/mtn/requesttopay/{{mtnReferenceId}}",
              "host": [
                "{{baseUrl}}"
              ],
              "path": [
                "webhooks",
                "mtn",
                "requesttopay",
                "{{mtnReferenceId}}"
              ]
            }
          }
        },
        {
          "name": "MTN callback receiver (RequestToPay) - PUT (manual test)",
          "request": {
            "method": "PUT",
            "header": [
              {
                "key": "Content-Type",
                "name": "Content-Type",
                "value": "application/json",
                "type": "text"
              },
              {
                "key": "x-reference-id",
                "name": "x-reference-id",
                "value": "{{mtnReferenceId}}",
                "type": "text"
              }
            ],
            "body": {
              "mode": "raw",
              "raw": "{\n  \"status\": \"SUCCESSFUL\",\n  \"reason\": \"\",\n  \"financialTransactionId\": \"sandbox_tx_123\"\n}"
            },
            "url": {
              "raw": "{{baseUrl}}/webhooks/mtn/requesttopay/{{mtnReferenceId}}",
              "host": [
                "{{baseUrl}}"
              ],
              "path": [
                "webhooks",
                "mtn",
                "requesttopay",
                "{{mtnReferenceId}}"
              ]
            }
          }
        },
        {
          "name": "Initiate MoMo withdraw (Disbursement)",
          "request": {
            "method": "POST",
            "header": [
              {
                "key": "Content-Type",
                "name": "Content-Type",
                "value": "application/json",
                "type": "text"
              },
              {
                "key": "Authorization",
                "name": "Authorization",
                "value": "Bearer {{accessToken}}",
                "type": "text"
              }
            ],
            "body": {
              "mode": "raw",
              "raw": "{\n  \"amountFcfa\": 1000\n}"
            },
            "url": {
              "raw": "{{baseUrl}}/payments/withdraw/momo",
              "host": [
                "{{baseUrl}}"
              ],
              "path": [
                "payments",
                "withdraw",
                "momo"
              ]
            }
          },
          "event": [
            {
              "listen": "test",
              "script": {
                "type": "text/javascript",
                "exec": [
                  "let data = {};",
                  "try { data = pm.response.json(); } catch (e) {}",
                  "if (data && data.referenceId) {",
                  "  pm.environment.set('mtnWithdrawReferenceId', data.referenceId);",
                  "}"
                ]
              }
            }
          ]
        },
        {
          "name": "Get MoMo withdraw status (polling fallback)",
          "request": {
            "method": "GET",
            "header": [
              {
                "key": "Authorization",
                "name": "Authorization",
                "value": "Bearer {{accessToken}}",
                "type": "text"
              }
            ],
            "url": {
              "raw": "{{baseUrl}}/payments/withdraw/momo/{{mtnWithdrawReferenceId}}/status",
              "host": [
                "{{baseUrl}}"
              ],
              "path": [
                "payments",
                "withdraw",
                "momo",
                "{{mtnWithdrawReferenceId}}",
                "status"
              ]
            }
          }
        },
        {
          "name": "Initiate Bridge deposit (Sandbox)",
          "request": {
            "method": "POST",
            "header": [
              {
                "key": "Content-Type",
                "name": "Content-Type",
                "value": "application/json",
                "type": "text"
              },
              {
                "key": "Authorization",
                "name": "Authorization",
                "value": "Bearer {{accessToken}}",
                "type": "text"
              }
            ],
            "body": {
              "mode": "raw",
              "raw": "{\n  \"amountFcfa\": 1000\n}"
            },
            "url": {
              "raw": "{{baseUrl}}/payments/deposit/bridge",
              "host": [
                "{{baseUrl}}"
              ],
              "path": [
                "payments",
                "deposit",
                "bridge"
              ]
            }
          },
          "event": [
            {
              "listen": "test",
              "script": {
                "type": "text/javascript",
                "exec": [
                  "let data = {};",
                  "try { data = pm.response.json(); } catch (e) {}",
                  "if (data && data.paymentRequestId) {",
                  "  pm.environment.set('bridgePaymentRequestId', data.paymentRequestId);",
                  "}",
                  "if (data && data.url) {",
                  "  pm.environment.set('bridgePaymentUrl', data.url);",
                  "}"
                ]
              }
            }
          ]
        },
        {
          "name": "Get Bridge deposit status (polling)",
          "request": {
            "method": "GET",
            "header": [
              {
                "key": "Authorization",
                "name": "Authorization",
                "value": "Bearer {{accessToken}}",
                "type": "text"
              }
            ],
            "url": {
              "raw": "{{baseUrl}}/payments/deposit/bridge/{{bridgePaymentRequestId}}/status",
              "host": [
                "{{baseUrl}}"
              ],
              "path": [
                "payments",
                "deposit",
                "bridge",
                "{{bridgePaymentRequestId}}",
                "status"
              ]
            }
          }
        },
        {
          "name": "Bridge payments webhook receiver (manual test)",
          "request": {
            "method": "POST",
            "header": [
              {
                "key": "Content-Type",
                "name": "Content-Type",
                "value": "application/json",
                "type": "text"
              },
              {
                "key": "BridgeApi-Signature",
                "name": "BridgeApi-Signature",
                "value": "{{bridgeApiSignature}}",
                "type": "text"
              }
            ],
            "body": {
              "mode": "raw",
              "raw": "{\n  \"type\": \"payment.transaction.updated\",\n  \"content\": {\n    \"payment_request_id\": \"{{bridgePaymentRequestId}}\",\n    \"status\": \"ACSC\"\n  },\n  \"timestamp\": 1713630583000\n}"
            },
            "url": {
              "raw": "{{baseUrl}}/webhooks/bridge/payments",
              "host": [
                "{{baseUrl}}"
              ],
              "path": [
                "webhooks",
                "bridge",
                "payments"
              ]
            }
          }
        },
        {
          "name": "Smile ID webhook (manual test)",
          "request": {
            "method": "POST",
            "header": [
              {
                "key": "Content-Type",
                "name": "Content-Type",
                "value": "application/json",
                "type": "text"
              }
            ],
            "body": {
              "mode": "raw",
              "raw": "{\n  \"signature\": \"REPLACE_WITH_REAL_SMILE_WEBHOOK_SIGNATURE\",\n  \"timestamp\": \"2026-05-20T12:00:00.000Z\",\n  \"job_success\": true,\n  \"result\": {\n    \"PartnerParams\": {\n      \"user_id\": \"USER_CUID\",\n      \"job_id\": \"kyc_USER_JOB\"\n    }\n  }\n}"
            },
            "description": "Le backend vérifie signature + timestamp (±5 min) avec SMILE_ID_PARTNER_ID / SMILE_ID_SIGNATURE_API_KEY. Pour un test manuel fiable, colle un corps réel provenant d’un callback Smile (sandbox) ou génère la signature avec le SDK smile-identity-core comme Smile le fait sur les webhooks.",
            "url": {
              "raw": "{{baseUrl}}/webhooks/smile-id",
              "host": [
                "{{baseUrl}}"
              ],
              "path": [
                "webhooks",
                "smile-id"
              ]
            }
          }
        },
        {
          "name": "Simulate Onafriq cards webhook",
          "request": {
            "method": "POST",
            "header": [
              {
                "key": "Content-Type",
                "name": "Content-Type",
                "value": "application/json",
                "type": "text"
              },
              {
                "key": "x-webhook-signature",
                "name": "x-webhook-signature",
                "value": "{{onafriqGeneratedSignature}}",
                "type": "text"
              }
            ],
            "body": {
              "mode": "raw",
              "raw": "{\n  \"requestId\": 10001,\n  \"customerId\": \"{{onafriqCustomerId}}\",\n  \"notificationType\": \"statuschange\",\n  \"cardStatus\": \"IA\",\n  \"lastFourDigits\": \"{{createdLast4}}\"\n}"
            },
            "url": {
              "raw": "{{baseUrl}}/webhooks/onafriq/cards",
              "host": [
                "{{baseUrl}}"
              ],
              "path": [
                "webhooks",
                "onafriq",
                "cards"
              ]
            }
          },
          "event": [
            {
              "listen": "prerequest",
              "script": {
                "type": "text/javascript",
                "exec": [
                  "const secret = pm.environment.get('onafriqWebhookSecret');",
                  "const key = pm.environment.get('onafriqSecretKey');",
                  "if (!secret || !key) {",
                  "  throw new Error('Missing onafriqWebhookSecret or onafriqSecretKey');",
                  "}",
                  "const encrypted = CryptoJS.AES.encrypt(secret, key).toString();",
                  "pm.environment.set('onafriqGeneratedSignature', encrypted);"
                ]
              }
            }
          ]
        },
        {
          "name": "Simulate Onafriq cards webhook (unfreeze AC)",
          "request": {
            "method": "POST",
            "header": [
              {
                "key": "Content-Type",
                "name": "Content-Type",
                "value": "application/json",
                "type": "text"
              },
              {
                "key": "x-webhook-signature",
                "name": "x-webhook-signature",
                "value": "{{onafriqGeneratedSignature}}",
                "type": "text"
              }
            ],
            "body": {
              "mode": "raw",
              "raw": "{\n  \"requestId\": 10002,\n  \"customerId\": \"{{onafriqCustomerId}}\",\n  \"notificationType\": \"statuschange\",\n  \"cardStatus\": \"AC\",\n  \"lastFourDigits\": \"{{createdLast4}}\"\n}"
            },
            "url": {
              "raw": "{{baseUrl}}/webhooks/onafriq/cards",
              "host": [
                "{{baseUrl}}"
              ],
              "path": [
                "webhooks",
                "onafriq",
                "cards"
              ]
            }
          },
          "event": [
            {
              "listen": "prerequest",
              "script": {
                "type": "text/javascript",
                "exec": [
                  "const secret = pm.environment.get('onafriqWebhookSecret');",
                  "const key = pm.environment.get('onafriqSecretKey');",
                  "if (!secret || !key) {",
                  "  throw new Error('Missing onafriqWebhookSecret or onafriqSecretKey');",
                  "}",
                  "const encrypted = CryptoJS.AES.encrypt(secret, key).toString();",
                  "pm.environment.set('onafriqGeneratedSignature', encrypted);"
                ]
              }
            }
          ]
        }
      ]
    },
    {
      "name": "Cards & Wallets",
      "item": [
        {
          "name": "List wallets",
          "request": {
            "method": "GET",
            "header": [
              {
                "key": "Authorization",
                "name": "Authorization",
                "value": "Bearer {{accessToken}}",
                "type": "text"
              }
            ],
            "url": {
              "raw": "{{baseUrl}}/wallets",
              "host": [
                "{{baseUrl}}"
              ],
              "path": [
                "wallets"
              ]
            }
          }
        },
        {
          "name": "Get wallet by id",
          "request": {
            "method": "GET",
            "header": [
              {
                "key": "Authorization",
                "name": "Authorization",
                "value": "Bearer {{accessToken}}",
                "type": "text"
              }
            ],
            "url": {
              "raw": "{{baseUrl}}/wallets/WALLET_ID_TO_REPLACE",
              "host": [
                "{{baseUrl}}"
              ],
              "path": [
                "wallets",
                "WALLET_ID_TO_REPLACE"
              ]
            }
          }
        },
        {
          "name": "Create virtual card (Onafriq)",
          "request": {
            "method": "POST",
            "header": [
              {
                "key": "Content-Type",
                "name": "Content-Type",
                "value": "application/json",
                "type": "text"
              },
              {
                "key": "Authorization",
                "name": "Authorization",
                "value": "Bearer {{accessToken}}",
                "type": "text"
              }
            ],
            "body": {
              "mode": "raw",
              "raw": "{\n  \"walletId\": \"{{walletId}}\",\n  \"amountFcfa\": 3000\n}"
            },
            "url": {
              "raw": "{{baseUrl}}/virtual-cards",
              "host": [
                "{{baseUrl}}"
              ],
              "path": [
                "virtual-cards"
              ]
            }
          },
          "event": [
            {
              "listen": "test",
              "script": {
                "type": "text/javascript",
                "exec": [
                  "let data = {};",
                  "try { data = pm.response.json(); } catch (e) {}",
                  "if (data?.virtualCard?.lastFour) pm.environment.set('createdLast4', data.virtualCard.lastFour);",
                  "if (data?.transaction?.providerTxId) pm.environment.set('onafriqCustomerId', data.transaction.providerTxId);"
                ]
              }
            }
          ]
        },
        {
          "name": "Wallet transactions history",
          "request": {
            "method": "GET",
            "header": [
              {
                "key": "Authorization",
                "name": "Authorization",
                "value": "Bearer {{accessToken}}",
                "type": "text"
              }
            ],
            "url": {
              "raw": "{{baseUrl}}/wallets/WALLET_ID_TO_REPLACE/transactions",
              "host": [
                "{{baseUrl}}"
              ],
              "path": [
                "wallets",
                "WALLET_ID_TO_REPLACE",
                "transactions"
              ]
            }
          }
        }
      ]
    }
  ],
  "event": [],
  "variable": [
    {
      "key": "mtnSandboxBaseUrl",
      "value": "https://sandbox.momodeveloper.mtn.com",
      "type": "string"
    },
    {
      "key": "mtnCollectionsSubscriptionKey",
      "value": "",
      "type": "string"
    },
    {
      "key": "mtnProviderCallbackHost",
      "value": "example.ngrok-free.app",
      "type": "string"
    },
    {
      "key": "mtnApiUser",
      "value": "",
      "type": "string"
    },
    {
      "key": "mtnApiKey",
      "value": "",
      "type": "string"
    },
    {
      "key": "mtnReferenceId",
      "value": "",
      "type": "string"
    },
    {
      "key": "mtnWithdrawReferenceId",
      "value": "",
      "type": "string"
    },
    {
      "key": "bridgePaymentRequestId",
      "value": "",
      "type": "string"
    },
    {
      "key": "bridgePaymentUrl",
      "value": "",
      "type": "string"
    },
    {
      "key": "bridgeApiSignature",
      "value": "",
      "type": "string"
    },
    {
      "key": "walletId",
      "value": "",
      "type": "string"
    },
    {
      "key": "createdLast4",
      "value": "",
      "type": "string"
    },
    {
      "key": "onafriqCustomerId",
      "value": "",
      "type": "string"
    },
    {
      "key": "onafriqGeneratedSignature",
      "value": "",
      "type": "string"
    }
  ]
}
```
