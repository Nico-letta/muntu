# MTN MoMo — Runbooks par code erreur

## `409 RESOURCE_ALREADY_EXIST` — X-Reference-Id duplique

**Remediation:** Nouveau UUID v4 ou poll GET si 202 recu

**Contexte async:** RequestToPay/Transfer retournent 202.

**Sandbox reproduction:** voir mtn-sandbox-test-matrix-full.md.

---

## `401 ACCESS DENIED DUE TO INVALID SUBSCRIPTION KEY` — Cle subscription invalide

**Remediation:** Primary/secondary key profil MTN

**Contexte async:** RequestToPay/Transfer retournent 202.

**Sandbox reproduction:** voir mtn-sandbox-test-matrix-full.md.

---

## `404 RESOURCE NOT FOUND` — Reference ID inconnu

**Remediation:** Verifier POST initial a retourne 202

**Contexte async:** RequestToPay/Transfer retournent 202.

**Sandbox reproduction:** voir mtn-sandbox-test-matrix-full.md.

---

## `400 REQUEST REJECTED/ BAD REQUEST` — Body/headers invalides

**Remediation:** UUID v4, currency, note <=160 chars

**Contexte async:** RequestToPay/Transfer retournent 202.

**Sandbox reproduction:** voir mtn-sandbox-test-matrix-full.md.

---

## `403 FORBIDDEN IP` — IP non whitelist Disbursement

**Remediation:** Partager IP publique Account Manager

**Contexte async:** RequestToPay/Transfer retournent 202.

**Sandbox reproduction:** voir mtn-sandbox-test-matrix-full.md.

---

## `500 NOT_ALLOWED` — Token sans permission

**Remediation:** Contact Account Manager MTN

**Contexte async:** RequestToPay/Transfer retournent 202.

**Sandbox reproduction:** voir mtn-sandbox-test-matrix-full.md.

---

## `500 NOT_ALLOWED_TARGET_ENVIRONMENT` — Mauvais OpCo

**Remediation:** mtncongo pour Congo, sandbox pour tests

**Contexte async:** RequestToPay/Transfer retournent 202.

**Sandbox reproduction:** voir mtn-sandbox-test-matrix-full.md.

---

## `500 INVALID_CALLBACK_URL_HOST` — Host callback mismatch

**Remediation:** Aligner providerCallbackHost

**Contexte async:** RequestToPay/Transfer retournent 202.

**Sandbox reproduction:** voir mtn-sandbox-test-matrix-full.md.

---

## `500 INVALID_CURRENCY` — Devise non supportee

**Remediation:** EUR sandbox, XAF prod Congo

**Contexte async:** RequestToPay/Transfer retournent 202.

**Sandbox reproduction:** voir mtn-sandbox-test-matrix-full.md.

---

## `503 SERVICE_UNAVAILABLE` — Plateforme indisponible

**Remediation:** Retry backoff + support MTN

**Contexte async:** RequestToPay/Transfer retournent 202.

**Sandbox reproduction:** voir mtn-sandbox-test-matrix-full.md.

---

## `INTERNAL_PROCESSING_ERROR` — Erreur generique business

**Remediation:** Fonds insuffisants ou wallet down

**Contexte async:** RequestToPay/Transfer retournent 202.

**Sandbox reproduction:** voir mtn-sandbox-test-matrix-full.md.

---

## `PAYEE_NOT_FOUND` — MSISDN payee invalide

**Remediation:** Format MSISDN + enregistrement MoMo

**Contexte async:** RequestToPay/Transfer retournent 202.

**Sandbox reproduction:** voir mtn-sandbox-test-matrix-full.md.

---

## `PAYER_NOT_FOUND` — MSISDN payer invalide

**Remediation:** Format MSISDN + enregistrement MoMo

**Contexte async:** RequestToPay/Transfer retournent 202.

**Sandbox reproduction:** voir mtn-sandbox-test-matrix-full.md.

---

## `COULD_NOT_PERFORM_TRANSACTION` — Timeout 5 min

**Remediation:** Re-initier avec nouvel ID

**Contexte async:** RequestToPay/Transfer retournent 202.

**Sandbox reproduction:** voir mtn-sandbox-test-matrix-full.md.

---

