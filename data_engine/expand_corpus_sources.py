#!/usr/bin/env python3
"""CLI — MUNTU Data Engine : expansion corpus pilotée par configuration."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

DATA_ENGINE = Path(__file__).resolve().parent
DEFAULT_CONFIG = DATA_ENGINE / "configs" / "afriwallet.json"
FALLBACK_CONFIG = DATA_ENGINE / "configs" / "afriwallet.example.json"


def resolve_config_path(arg: str | None) -> Path:
    if arg:
        p = Path(arg)
        return p if p.is_absolute() else (Path.cwd() / p).resolve()
    if DEFAULT_CONFIG.exists():
        return DEFAULT_CONFIG
    if FALLBACK_CONFIG.exists():
        print(f"[WARN] Config locale absente — utilisation de {FALLBACK_CONFIG.name}")
        print("       Copiez afriwallet.example.json -> afriwallet.json et ajustez source_path.")
        return FALLBACK_CONFIG
    raise FileNotFoundError(
        f"Aucune config trouvée. Créez {DEFAULT_CONFIG} ou passez --config configs/votre_projet.json"
    )


def main() -> int:
    parser = argparse.ArgumentParser(
        description="MUNTU ExtractionEngine — export corpus_raw depuis une config projet",
    )
    parser.add_argument(
        "--config", "-c",
        help="Chemin vers project.config.json (defaut: configs/afriwallet.json)",
    )
    args = parser.parse_args()

    try:
        config_path = resolve_config_path(args.config)
    except FileNotFoundError as exc:
        print(f"[-] {exc}")
        return 1

    from corpus_extractor.config import load_project_config
    from corpus_extractor.engine import ExtractionEngine

    repo_root = DATA_ENGINE.parent
    config = load_project_config(config_path, defaults_repo_root=repo_root)
    ExtractionEngine(config).run()
    return 0


if __name__ == "__main__":
    sys.exit(main())
