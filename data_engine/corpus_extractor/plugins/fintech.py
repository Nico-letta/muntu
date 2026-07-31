"""Plugin fintech Afrique — runbooks, corpus synthetique, validation matrice erreurs."""

from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from ..config import ProjectConfig
    from ..engine import ExtractContext

AIRTEL_ERROR_CODES = [
    ("ROUTER001", "Wallet not configured", "Configurer wallet produit dans portail Airtel Developer.", "Dashboard -> Application Settings -> Wallet"),
    ("ROUTER003", "Missing header/body params", "Verifier tous headers obligatoires et body JSON.", "Content-Type, Authorization, X-Country, X-Currency"),
    ("ROUTER005", "Country route not configured", "Route pays non configuree cote Airtel.", "Contacter support Airtel Africa"),
    ("ROUTER006", "Invalid Country", "Code pays incorrect.", "Utiliser CG pour Congo-Brazzaville"),
    ("ROUTER007", "User Not authorized", "Compte non autorise pour le pays.", "Verifier permissions compte developpeur"),
    ("ROUTER112", "Invalid Currency", "Code devise incorrect.", "XAF pour Congo"),
    ("ROUTER114", "Error while Validating Pin", "Echec validation PIN.", "Verifier chiffrement RSA PIN"),
    ("ROUTER115", "Incorrect Pin", "PIN utilisateur incorrect.", "Re-saisie PIN cote client"),
    ("ROUTER116", "Incorrect Encrypted Pin", "Mecanisme chiffrement PIN invalide.", "RSA 2048 OAEP SHA-256"),
    ("ROUTER117", "Request Timeout", "Timeout requete — etat ambigu possible.", "Transaction enquiry payments/refund"),
    ("ROUTER119", "Invalid/Missing Currency", "Devise absente ou invalide.", "Header X-Currency: XAF"),
    ("ESB000001", "Something went wrong", "Erreur generique — etat ambigu.", "Transaction enquiry"),
    ("ESB000004", "Error initiating payment", "Echec initiation — ambigu.", "Transaction enquiry"),
    ("ESB000008", "Field validation error", "Champ body invalide.", "Corriger payload + enquiry"),
    ("ESB000010", "Request was Success", "Succes ESB.", "Proceed"),
    ("ESB000011", "Request was Failed", "Echec ESB.", "Fail workflow"),
    ("ESB000014", "Error fetching status", "Echec lecture statut.", "Retry enquiry apres delai"),
    ("ESB000033", "Invalid MSISDN Length", "Longueur MSISDN incorrecte.", "Format MSISDN local"),
    ("ESB000034", "Invalid Country Name", "Nom pays invalide.", "CG"),
    ("ESB000035", "Invalid Currency Code", "Devise invalide.", "XAF"),
    ("ESB000036", "Invalid MSISDN format", "MSISDN format ou prefix 0.", "Corriger MSISDN"),
    ("ESB000039", "Vendor not configured", "Vendor pas configure pour pays.", "Support Airtel"),
    ("ESB000041", "Duplicate External Transaction ID", "transaction.id deja utilise.", "Nouvel ID ou enquiry"),
    ("ESB000045", "Transaction Not Found", "ID introuvable.", "Verifier transaction.id"),
    ("0000900", "Ambiguous state", "Etat ambigu.", "Check response_code + enquiry"),
    ("DP01000001000", "Cash-In Ambiguous", "Cash-In en cours/ambigu.", "GET /standard/v1/payments/{id}"),
    ("DP01000001001", "Cash-In Success", "Cash-In reussi.", "Crediter si workflow interne OK"),
    ("DP01000001007", "Insufficient Funds", "Fonds insuffisants payer.", "Message UX solde insuffisant"),
    ("DP02100001002", "B2W Duplicate Transaction ID", "Doublon transaction B2W.", "Nouvel ID unique"),
    ("DP03520001001", "Refund Success TR", "Renversement reussi status TR.", "Marquer refund complete"),
    ("DP08700001001", "ATM Withdrawal Success", "Retrait GAB reussi.", "Finaliser transaction"),
]

MTN_ERROR_CODES = [
    ("409 RESOURCE_ALREADY_EXIST", "X-Reference-Id duplique", "Nouveau UUID v4 ou poll GET si 202 recu"),
    ("401 ACCESS DENIED DUE TO INVALID SUBSCRIPTION KEY", "Cle subscription invalide", "Primary/secondary key profil MTN"),
    ("404 RESOURCE NOT FOUND", "Reference ID inconnu", "Verifier POST initial a retourne 202"),
    ("400 REQUEST REJECTED/ BAD REQUEST", "Body/headers invalides", "UUID v4, currency, note <=160 chars"),
    ("403 FORBIDDEN IP", "IP non whitelist Disbursement", "Partager IP publique Account Manager"),
    ("500 NOT_ALLOWED", "Token sans permission", "Contact Account Manager MTN"),
    ("500 NOT_ALLOWED_TARGET_ENVIRONMENT", "Mauvais OpCo", "mtncongo pour Congo, sandbox pour tests"),
    ("500 INVALID_CALLBACK_URL_HOST", "Host callback mismatch", "Aligner providerCallbackHost"),
    ("500 INVALID_CURRENCY", "Devise non supportee", "EUR sandbox, XAF prod Congo"),
    ("503 SERVICE_UNAVAILABLE", "Plateforme indisponible", "Retry backoff + support MTN"),
    ("INTERNAL_PROCESSING_ERROR", "Erreur generique business", "Fonds insuffisants ou wallet down"),
    ("PAYEE_NOT_FOUND", "MSISDN payee invalide", "Format MSISDN + enregistrement MoMo"),
    ("PAYER_NOT_FOUND", "MSISDN payer invalide", "Format MSISDN + enregistrement MoMo"),
    ("COULD_NOT_PERFORM_TRANSACTION", "Timeout 5 min", "Re-initier avec nouvel ID"),
]

SYNTHETIC_TOPICS = [
    ("Diagnostiquer PENDING MoMo > 5 minutes", "momo-pending", "Verifier callback mtn:r2p, poll GET status, confirmer approbation client USSD."),
    ("Gerer ESB000041 duplicate Airtel", "airtel-duplicate", "Transaction enquiry avant retry, jamais reutiliser transaction.id."),
    ("Compensation cash-out FAILED", "momo-compensation", "increment balanceFcfa si CASH_OUT_MOMO FAILED via webhook ou poll."),
    ("Mapper DP03520001001 + TR", "airtel-refund", "Renversement reussi, success true, status TR."),
    ("Fix INVALID_CALLBACK_URL_HOST", "mtn-callback", "providerCallbackHost doit egaler host X-Callback-Url."),
    ("Distinction KYC vs SmartSelfie", "kyc-smartselfie", "kycStatus pour paiements, smartSelfieLastAuthSuccess pour step-up."),
    ("Valider NIN Nigeria 11 digits", "kyc-ng", "Regex ^\\d{11}$ pour NIN_V2 biometric."),
    ("Configurer mtncongo production", "mtn-opco", "MTN_MOMO_TARGET_ENVIRONMENT=mtncongo, currency XAF."),
    ("Webhook Smile ID duplicate", "smile-idempotent", "P2002 eventKey ignore silencieusement."),
    ("Bridge RJCT pas de credit", "bridge-failed", "FAILED sans increment wallet, ACSC seul credite."),
    ("OTP 410 Gone expire", "auth-otp", "TTL 5 min, deleteMany OTP expires, renvoyer code."),
    ("BigInt FCFA pas de float", "wallet-bigint", "Number() a la frontiere API, jamais division par 100."),
    ("Onafriq card freeze LC", "onafriq-freeze", "isFrozen true si cardStatus LC/IA/SC etc."),
    ("ROUTER001 Airtel wallet config", "airtel-router", "Configurer wallet portail developer."),
    ("TA TIP Airtel enquiry obligatoire", "airtel-ambiguous", "GET payments/{id}, pas de credit sur TIP."),
    ("409 MTN reutiliser referenceId", "mtn-409", "Poll GET si 202 recu, sinon nouveau UUID."),
    ("KYC CG document job_type 11", "kyc-cg", "Smile document verification Congo uniquement."),
    ("Headers CG XAF Airtel", "airtel-headers", "X-Country CG, X-Currency XAF systematiques."),
    ("Disbursement token separe MTN", "mtn-disbursement", "disbursement/token/ != collection token."),
    ("AIRTEL schema_only hors perimetre", "roadmap-airtel", "Pas de src/providers/airtel.service.ts."),
]


def export_airtel_runbooks(ctx: ExtractContext) -> None:
    parts = ["# Airtel Money — Runbooks par code erreur\n\n", "> UAT: openapiuat.airtel.cg | Prod: openapi.airtel.cg\n\n"]
    for code, title, desc, action in AIRTEL_ERROR_CODES:
        parts.append(f"## `{code}` — {title}\n\n")
        parts.append(f"**Description:** {desc}\n\n")
        parts.append(f"**Action immediate:** {action}\n\n")
        parts.append("**Investigation:**\n")
        parts.append("1. Capturer request/response HTTP complet (masquer secrets).\n")
        parts.append("2. Verifier headers X-Country CG et X-Currency XAF.\n")
        parts.append("3. Si ambigu: transaction enquiry avant tout retry.\n")
        parts.append("4. Logger transaction.id et reference_id Airtel.\n\n")
        parts.append("**Prevention:** idempotence transaction.id, OAuth2 token refresh, PIN RSA.\n\n---\n\n")
    ctx.write_corpus("30-system-integrations/airtel-error-runbooks-complete.md", "".join(parts))


def export_mtn_runbooks(ctx: ExtractContext) -> None:
    parts = ["# MTN MoMo — Runbooks par code erreur\n\n"]
    for code, title, action in MTN_ERROR_CODES:
        parts.append(f"## `{code}` — {title}\n\n")
        parts.append(f"**Remediation:** {action}\n\n")
        parts.append("**Contexte async:** RequestToPay/Transfer retournent 202.\n\n")
        parts.append("**Sandbox reproduction:** voir mtn-sandbox-test-matrix-full.md.\n\n---\n\n")
    ctx.write_corpus("30-system-integrations/mtn-error-runbooks-complete.md", "".join(parts))


def export_synthetic_corpus(ctx: ExtractContext) -> None:
    name = ctx.product_name
    parts = ["# Corpus synthetique — Paires entrainement supplementaires\n\n"]
    for i, (title, slug, answer) in enumerate(SYNTHETIC_TOPICS, 1):
        parts.append(f"## Paire synthetique {i}: {title}\n\n")
        parts.append(f"**Instruction:** En tant qu'ingenieur fintech Afrique, comment gerer: {title}?\n\n")
        parts.append(f"**Reponse:** {answer}\n\n")
        parts.append(f"**Contexte {name}:** Stack NestJS + Prisma + PostgreSQL. ")
        parts.append("Providers actifs: MTN_MOMO, SMILE_ID, ONAFRIQ, BRIDGE. ")
        parts.append("AIRTEL enum schema_only (hors perimetre deploye). Montants FCFA BigInt. MoMo async 202.\n\n")
        parts.append(f"**Slug:** `{slug}`\n\n---\n\n")
    ctx.write_corpus("35-business-flows/synthetic-training-corpus.md", "".join(parts))


def validate_error_matrix(ctx: ExtractContext, spec: dict) -> None:
    matrix_path = ctx.corpus / spec.get("matrix_file", "30-system-integrations/provider-official-error-matrix-normalized.md")
    if not matrix_path.exists():
        print("[WARN] Matrice erreurs normalisee absente")
        return
    matrix = matrix_path.read_text(encoding="utf-8")
    for doc in spec.get("marker_checks", []):
        src = ctx.resolve_repo_file(doc["source"])
        text = src.read_text(encoding="utf-8") if src.exists() else ""
        for marker in doc.get("markers", []):
            if text and marker not in text:
                print(f"[WARN] {marker} absent de {doc['source']}")
            if marker not in matrix:
                print(f"[WARN] {marker} absent de la matrice normalisee")


def run(ctx: ExtractContext, cfg: ProjectConfig) -> None:
    if cfg.feature_enabled("runbooks"):
        providers = cfg.feature("runbooks").get("providers", [])
        if "airtel" in providers:
            export_airtel_runbooks(ctx)
        if "mtn" in providers:
            export_mtn_runbooks(ctx)

    if cfg.feature_enabled("synthetic_corpus"):
        export_synthetic_corpus(ctx)

    if cfg.feature_enabled("error_matrix_validation"):
        validate_error_matrix(ctx, cfg.feature("error_matrix_validation"))

    print("[+] Plugin fintech complete")
