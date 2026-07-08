# Airtel Money — Runbooks par code erreur

> UAT: openapiuat.airtel.cg | Prod: openapi.airtel.cg

## `ROUTER001` — Wallet not configured

**Description:** Configurer wallet produit dans portail Airtel Developer.

**Action immediate:** Dashboard -> Application Settings -> Wallet

**Investigation:**
1. Capturer request/response HTTP complet (masquer secrets).
2. Verifier headers X-Country CG et X-Currency XAF.
3. Si ambigu: transaction enquiry avant tout retry.
4. Logger transaction.id et reference_id Airtel.

**Prevention:** idempotence transaction.id, OAuth2 token refresh, PIN RSA.

---

## `ROUTER003` — Missing header/body params

**Description:** Verifier tous headers obligatoires et body JSON.

**Action immediate:** Content-Type, Authorization, X-Country, X-Currency

**Investigation:**
1. Capturer request/response HTTP complet (masquer secrets).
2. Verifier headers X-Country CG et X-Currency XAF.
3. Si ambigu: transaction enquiry avant tout retry.
4. Logger transaction.id et reference_id Airtel.

**Prevention:** idempotence transaction.id, OAuth2 token refresh, PIN RSA.

---

## `ROUTER005` — Country route not configured

**Description:** Route pays non configuree cote Airtel.

**Action immediate:** Contacter support Airtel Africa

**Investigation:**
1. Capturer request/response HTTP complet (masquer secrets).
2. Verifier headers X-Country CG et X-Currency XAF.
3. Si ambigu: transaction enquiry avant tout retry.
4. Logger transaction.id et reference_id Airtel.

**Prevention:** idempotence transaction.id, OAuth2 token refresh, PIN RSA.

---

## `ROUTER006` — Invalid Country

**Description:** Code pays incorrect.

**Action immediate:** Utiliser CG pour Congo-Brazzaville

**Investigation:**
1. Capturer request/response HTTP complet (masquer secrets).
2. Verifier headers X-Country CG et X-Currency XAF.
3. Si ambigu: transaction enquiry avant tout retry.
4. Logger transaction.id et reference_id Airtel.

**Prevention:** idempotence transaction.id, OAuth2 token refresh, PIN RSA.

---

## `ROUTER007` — User Not authorized

**Description:** Compte non autorise pour le pays.

**Action immediate:** Verifier permissions compte developpeur

**Investigation:**
1. Capturer request/response HTTP complet (masquer secrets).
2. Verifier headers X-Country CG et X-Currency XAF.
3. Si ambigu: transaction enquiry avant tout retry.
4. Logger transaction.id et reference_id Airtel.

**Prevention:** idempotence transaction.id, OAuth2 token refresh, PIN RSA.

---

## `ROUTER112` — Invalid Currency

**Description:** Code devise incorrect.

**Action immediate:** XAF pour Congo

**Investigation:**
1. Capturer request/response HTTP complet (masquer secrets).
2. Verifier headers X-Country CG et X-Currency XAF.
3. Si ambigu: transaction enquiry avant tout retry.
4. Logger transaction.id et reference_id Airtel.

**Prevention:** idempotence transaction.id, OAuth2 token refresh, PIN RSA.

---

## `ROUTER114` — Error while Validating Pin

**Description:** Echec validation PIN.

**Action immediate:** Verifier chiffrement RSA PIN

**Investigation:**
1. Capturer request/response HTTP complet (masquer secrets).
2. Verifier headers X-Country CG et X-Currency XAF.
3. Si ambigu: transaction enquiry avant tout retry.
4. Logger transaction.id et reference_id Airtel.

**Prevention:** idempotence transaction.id, OAuth2 token refresh, PIN RSA.

---

## `ROUTER115` — Incorrect Pin

**Description:** PIN utilisateur incorrect.

**Action immediate:** Re-saisie PIN cote client

**Investigation:**
1. Capturer request/response HTTP complet (masquer secrets).
2. Verifier headers X-Country CG et X-Currency XAF.
3. Si ambigu: transaction enquiry avant tout retry.
4. Logger transaction.id et reference_id Airtel.

**Prevention:** idempotence transaction.id, OAuth2 token refresh, PIN RSA.

---

## `ROUTER116` — Incorrect Encrypted Pin

**Description:** Mecanisme chiffrement PIN invalide.

**Action immediate:** RSA 2048 OAEP SHA-256

**Investigation:**
1. Capturer request/response HTTP complet (masquer secrets).
2. Verifier headers X-Country CG et X-Currency XAF.
3. Si ambigu: transaction enquiry avant tout retry.
4. Logger transaction.id et reference_id Airtel.

**Prevention:** idempotence transaction.id, OAuth2 token refresh, PIN RSA.

---

## `ROUTER117` — Request Timeout

**Description:** Timeout requete — etat ambigu possible.

**Action immediate:** Transaction enquiry payments/refund

**Investigation:**
1. Capturer request/response HTTP complet (masquer secrets).
2. Verifier headers X-Country CG et X-Currency XAF.
3. Si ambigu: transaction enquiry avant tout retry.
4. Logger transaction.id et reference_id Airtel.

**Prevention:** idempotence transaction.id, OAuth2 token refresh, PIN RSA.

---

## `ROUTER119` — Invalid/Missing Currency

**Description:** Devise absente ou invalide.

**Action immediate:** Header X-Currency: XAF

**Investigation:**
1. Capturer request/response HTTP complet (masquer secrets).
2. Verifier headers X-Country CG et X-Currency XAF.
3. Si ambigu: transaction enquiry avant tout retry.
4. Logger transaction.id et reference_id Airtel.

**Prevention:** idempotence transaction.id, OAuth2 token refresh, PIN RSA.

---

## `ESB000001` — Something went wrong

**Description:** Erreur generique — etat ambigu.

**Action immediate:** Transaction enquiry

**Investigation:**
1. Capturer request/response HTTP complet (masquer secrets).
2. Verifier headers X-Country CG et X-Currency XAF.
3. Si ambigu: transaction enquiry avant tout retry.
4. Logger transaction.id et reference_id Airtel.

**Prevention:** idempotence transaction.id, OAuth2 token refresh, PIN RSA.

---

## `ESB000004` — Error initiating payment

**Description:** Echec initiation — ambigu.

**Action immediate:** Transaction enquiry

**Investigation:**
1. Capturer request/response HTTP complet (masquer secrets).
2. Verifier headers X-Country CG et X-Currency XAF.
3. Si ambigu: transaction enquiry avant tout retry.
4. Logger transaction.id et reference_id Airtel.

**Prevention:** idempotence transaction.id, OAuth2 token refresh, PIN RSA.

---

## `ESB000008` — Field validation error

**Description:** Champ body invalide.

**Action immediate:** Corriger payload + enquiry

**Investigation:**
1. Capturer request/response HTTP complet (masquer secrets).
2. Verifier headers X-Country CG et X-Currency XAF.
3. Si ambigu: transaction enquiry avant tout retry.
4. Logger transaction.id et reference_id Airtel.

**Prevention:** idempotence transaction.id, OAuth2 token refresh, PIN RSA.

---

## `ESB000010` — Request was Success

**Description:** Succes ESB.

**Action immediate:** Proceed

**Investigation:**
1. Capturer request/response HTTP complet (masquer secrets).
2. Verifier headers X-Country CG et X-Currency XAF.
3. Si ambigu: transaction enquiry avant tout retry.
4. Logger transaction.id et reference_id Airtel.

**Prevention:** idempotence transaction.id, OAuth2 token refresh, PIN RSA.

---

## `ESB000011` — Request was Failed

**Description:** Echec ESB.

**Action immediate:** Fail workflow

**Investigation:**
1. Capturer request/response HTTP complet (masquer secrets).
2. Verifier headers X-Country CG et X-Currency XAF.
3. Si ambigu: transaction enquiry avant tout retry.
4. Logger transaction.id et reference_id Airtel.

**Prevention:** idempotence transaction.id, OAuth2 token refresh, PIN RSA.

---

## `ESB000014` — Error fetching status

**Description:** Echec lecture statut.

**Action immediate:** Retry enquiry apres delai

**Investigation:**
1. Capturer request/response HTTP complet (masquer secrets).
2. Verifier headers X-Country CG et X-Currency XAF.
3. Si ambigu: transaction enquiry avant tout retry.
4. Logger transaction.id et reference_id Airtel.

**Prevention:** idempotence transaction.id, OAuth2 token refresh, PIN RSA.

---

## `ESB000033` — Invalid MSISDN Length

**Description:** Longueur MSISDN incorrecte.

**Action immediate:** Format MSISDN local

**Investigation:**
1. Capturer request/response HTTP complet (masquer secrets).
2. Verifier headers X-Country CG et X-Currency XAF.
3. Si ambigu: transaction enquiry avant tout retry.
4. Logger transaction.id et reference_id Airtel.

**Prevention:** idempotence transaction.id, OAuth2 token refresh, PIN RSA.

---

## `ESB000034` — Invalid Country Name

**Description:** Nom pays invalide.

**Action immediate:** CG

**Investigation:**
1. Capturer request/response HTTP complet (masquer secrets).
2. Verifier headers X-Country CG et X-Currency XAF.
3. Si ambigu: transaction enquiry avant tout retry.
4. Logger transaction.id et reference_id Airtel.

**Prevention:** idempotence transaction.id, OAuth2 token refresh, PIN RSA.

---

## `ESB000035` — Invalid Currency Code

**Description:** Devise invalide.

**Action immediate:** XAF

**Investigation:**
1. Capturer request/response HTTP complet (masquer secrets).
2. Verifier headers X-Country CG et X-Currency XAF.
3. Si ambigu: transaction enquiry avant tout retry.
4. Logger transaction.id et reference_id Airtel.

**Prevention:** idempotence transaction.id, OAuth2 token refresh, PIN RSA.

---

## `ESB000036` — Invalid MSISDN format

**Description:** MSISDN format ou prefix 0.

**Action immediate:** Corriger MSISDN

**Investigation:**
1. Capturer request/response HTTP complet (masquer secrets).
2. Verifier headers X-Country CG et X-Currency XAF.
3. Si ambigu: transaction enquiry avant tout retry.
4. Logger transaction.id et reference_id Airtel.

**Prevention:** idempotence transaction.id, OAuth2 token refresh, PIN RSA.

---

## `ESB000039` — Vendor not configured

**Description:** Vendor pas configure pour pays.

**Action immediate:** Support Airtel

**Investigation:**
1. Capturer request/response HTTP complet (masquer secrets).
2. Verifier headers X-Country CG et X-Currency XAF.
3. Si ambigu: transaction enquiry avant tout retry.
4. Logger transaction.id et reference_id Airtel.

**Prevention:** idempotence transaction.id, OAuth2 token refresh, PIN RSA.

---

## `ESB000041` — Duplicate External Transaction ID

**Description:** transaction.id deja utilise.

**Action immediate:** Nouvel ID ou enquiry

**Investigation:**
1. Capturer request/response HTTP complet (masquer secrets).
2. Verifier headers X-Country CG et X-Currency XAF.
3. Si ambigu: transaction enquiry avant tout retry.
4. Logger transaction.id et reference_id Airtel.

**Prevention:** idempotence transaction.id, OAuth2 token refresh, PIN RSA.

---

## `ESB000045` — Transaction Not Found

**Description:** ID introuvable.

**Action immediate:** Verifier transaction.id

**Investigation:**
1. Capturer request/response HTTP complet (masquer secrets).
2. Verifier headers X-Country CG et X-Currency XAF.
3. Si ambigu: transaction enquiry avant tout retry.
4. Logger transaction.id et reference_id Airtel.

**Prevention:** idempotence transaction.id, OAuth2 token refresh, PIN RSA.

---

## `0000900` — Ambiguous state

**Description:** Etat ambigu.

**Action immediate:** Check response_code + enquiry

**Investigation:**
1. Capturer request/response HTTP complet (masquer secrets).
2. Verifier headers X-Country CG et X-Currency XAF.
3. Si ambigu: transaction enquiry avant tout retry.
4. Logger transaction.id et reference_id Airtel.

**Prevention:** idempotence transaction.id, OAuth2 token refresh, PIN RSA.

---

## `DP01000001000` — Cash-In Ambiguous

**Description:** Cash-In en cours/ambigu.

**Action immediate:** GET /standard/v1/payments/{id}

**Investigation:**
1. Capturer request/response HTTP complet (masquer secrets).
2. Verifier headers X-Country CG et X-Currency XAF.
3. Si ambigu: transaction enquiry avant tout retry.
4. Logger transaction.id et reference_id Airtel.

**Prevention:** idempotence transaction.id, OAuth2 token refresh, PIN RSA.

---

## `DP01000001001` — Cash-In Success

**Description:** Cash-In reussi.

**Action immediate:** Crediter si workflow interne OK

**Investigation:**
1. Capturer request/response HTTP complet (masquer secrets).
2. Verifier headers X-Country CG et X-Currency XAF.
3. Si ambigu: transaction enquiry avant tout retry.
4. Logger transaction.id et reference_id Airtel.

**Prevention:** idempotence transaction.id, OAuth2 token refresh, PIN RSA.

---

## `DP01000001007` — Insufficient Funds

**Description:** Fonds insuffisants payer.

**Action immediate:** Message UX solde insuffisant

**Investigation:**
1. Capturer request/response HTTP complet (masquer secrets).
2. Verifier headers X-Country CG et X-Currency XAF.
3. Si ambigu: transaction enquiry avant tout retry.
4. Logger transaction.id et reference_id Airtel.

**Prevention:** idempotence transaction.id, OAuth2 token refresh, PIN RSA.

---

## `DP02100001002` — B2W Duplicate Transaction ID

**Description:** Doublon transaction B2W.

**Action immediate:** Nouvel ID unique

**Investigation:**
1. Capturer request/response HTTP complet (masquer secrets).
2. Verifier headers X-Country CG et X-Currency XAF.
3. Si ambigu: transaction enquiry avant tout retry.
4. Logger transaction.id et reference_id Airtel.

**Prevention:** idempotence transaction.id, OAuth2 token refresh, PIN RSA.

---

## `DP03520001001` — Refund Success TR

**Description:** Renversement reussi status TR.

**Action immediate:** Marquer refund complete

**Investigation:**
1. Capturer request/response HTTP complet (masquer secrets).
2. Verifier headers X-Country CG et X-Currency XAF.
3. Si ambigu: transaction enquiry avant tout retry.
4. Logger transaction.id et reference_id Airtel.

**Prevention:** idempotence transaction.id, OAuth2 token refresh, PIN RSA.

---

## `DP08700001001` — ATM Withdrawal Success

**Description:** Retrait GAB reussi.

**Action immediate:** Finaliser transaction

**Investigation:**
1. Capturer request/response HTTP complet (masquer secrets).
2. Verifier headers X-Country CG et X-Currency XAF.
3. Si ambigu: transaction enquiry avant tout retry.
4. Logger transaction.id et reference_id Airtel.

**Prevention:** idempotence transaction.id, OAuth2 token refresh, PIN RSA.

---

