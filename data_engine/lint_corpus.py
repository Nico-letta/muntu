#!/usr/bin/env python3
"""Linter basique du corpus AfriWallet avant compilation."""

from __future__ import annotations

import re
import sys
from pathlib import Path

DATA_ENGINE = Path(__file__).resolve().parent
CORPUS_RAW = DATA_ENGINE / "corpus_raw"
MANIFEST = CORPUS_RAW / "manifest.json"


def _load_prisma_schema_path() -> Path:
    if MANIFEST.exists():
        import json
        repos = json.loads(MANIFEST.read_text(encoding="utf-8")).get("source_repos", {})
        codebase = Path(repos.get("afriwallet_codebase", "D:/zeno"))
        return codebase / "prisma" / "schema.prisma"
    return Path("D:/zeno/prisma/schema.prisma")


PRISMA_SCHEMA = _load_prisma_schema_path()

# Modèles Prisma canoniques (source de vérité)
PRISMA_MODELS = {
    "User",
    "Wallet",
    "Transaction",
    "VirtualCard",
    "OtpRequest",
    "WebhookEvent",
}

# Enums schema_only — mentions d'implémentation = warning
GHOST_FEATURES = {
    "CASH_IN_AIRTEL": "AIRTEL_MOMO non implémenté",
    "CARD_PAYMENT": "CARD_PAYMENT schema_only",
    "CARD_REFUND": "CARD_REFUND schema_only",
    "PaymentProvider.AIRTEL": "AIRTEL provider non implémenté",
}

# Chemins obsolètes post-v4
DEPRECATED_PATHS = [
    "35-use-cases",
    "15-case-studies",
    "90-codebase-constraints/fintech-error-codes",
    "30-system-integrations/providers/airtel-money",
    "05-fintech-local",
    "06-use-cases",
]

# eventKey patterns documentés
EVENT_KEY_PATTERNS = [
    r"mtn:r2p:\{referenceId\}",
    r"mtn:r2p:",
    r"smile:",
    r"onafriq:",
    r"bridge:payments:",
]


def load_prisma_models() -> set[str]:
    if not PRISMA_SCHEMA.exists():
        return PRISMA_MODELS
    text = PRISMA_SCHEMA.read_text(encoding="utf-8")
    found = set(re.findall(r"^model\s+(\w+)\s+\{", text, re.MULTILINE))
    return found or PRISMA_MODELS


def collect_markdown_files() -> list[Path]:
    files: list[Path] = []
    for ext in ("*.md",):
        files.extend(CORPUS_RAW.rglob(ext))
    skip = {"README.md", "CONSOLIDATION-MAP.md"}
    return sorted(p for p in files if p.name not in skip)


def lint_file(path: Path, prisma_models: set[str]) -> tuple[list[str], list[str]]:
    errors: list[str] = []
    warnings: list[str] = []
    rel = path.relative_to(CORPUS_RAW).as_posix()
    text = path.read_text(encoding="utf-8")

    for deprecated in DEPRECATED_PATHS:
        if deprecated in text:
            warnings.append(f"{rel}: chemin obsolete '{deprecated}'")

    # Modèles Prisma mentionnés (backticks ou "model X")
    mentioned_models = set(re.findall(r"`(\w+)`", text))
    mentioned_models.update(re.findall(r"model\s+(\w+)", text, re.I))
    prisma_mentions = mentioned_models & {"User", "Wallet", "Transaction", "VirtualCard", "OtpRequest", "WebhookEvent"}
    unknown = prisma_mentions - prisma_models
    if unknown:
        errors.append(f"{rel}: modeles Prisma inconnus {unknown}")

    # Ghost features avec langage d'implémentation
    impl_patterns = [
        r"implement(?:e|é|ation)",
        r"service\s+.*Airtel",
        r"src/providers/airtel",
        r"POST\s+/payments/.*airtel",
    ]
    for ghost, msg in GHOST_FEATURES.items():
        if ghost in text:
            for pat in impl_patterns:
                if re.search(pat, text, re.I):
                    if "90-codebase-constraints" not in rel and "NON IMPL" not in text.upper():
                        warnings.append(f"{rel}: {msg} mais langage implementation detecte ({pat})")
                    break

    # provider-error-codes ne doit pas etre dans 90
    if "fintech-error-codes" in rel and "90-codebase" in rel:
        errors.append(f"{rel}: codes erreur providers doivent etre dans 30-system-integrations/")

    return errors, warnings


def lint_event_keys(files: list[Path]) -> list[str]:
    warnings: list[str] = []
    corpus_text = "\n".join(p.read_text(encoding="utf-8") for p in files)
    if "eventKey" in corpus_text:
        if not any(p.search(corpus_text) for p in [re.compile(x) for x in EVENT_KEY_PATTERNS]):
            warnings.append("global: eventKey mentionne sans pattern mtn:r2p/smile/onafriq/bridge")
    return warnings


def run_lint() -> int:
    prisma_models = load_prisma_models()
    files = collect_markdown_files()
    all_errors: list[str] = []
    all_warnings: list[str] = []

    print(f"[*] Lint corpus — {len(files)} fichiers markdown, {len(prisma_models)} modeles Prisma")

    for path in files:
        errs, warns = lint_file(path, prisma_models)
        all_errors.extend(errs)
        all_warnings.extend(warns)

    all_warnings.extend(lint_event_keys(files))

    for w in all_warnings:
        print(f"[WARN] {w}")
    for e in all_errors:
        print(f"[ERROR] {e}")

    if all_errors:
        print(f"[-] Lint echoue — {len(all_errors)} erreur(s), {len(all_warnings)} avertissement(s)")
        return 1

    print(f"[+] Lint OK — {len(all_warnings)} avertissement(s)")
    return 0


if __name__ == "__main__":
    sys.exit(run_lint())
