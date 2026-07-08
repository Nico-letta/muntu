"""Chargement et validation des fichiers project.config.json."""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any


@dataclass
class ProjectConfig:
    """Configuration d'un projet extrait vers corpus_raw."""

    project_id: str
    project_name: str
    engine_name: str
    codebase_ref: str
    source_path: Path
    corpus_staging: Path
    repo_root: Path
    corpus_output: Path
    features: dict[str, Any] = field(default_factory=dict)
    branding: dict[str, Any] = field(default_factory=dict)
    cleanup_legacy_artifacts: list[str] = field(default_factory=list)
    config_path: Path | None = None

    @classmethod
    def from_dict(cls, data: dict[str, Any], config_path: Path, defaults_repo_root: Path) -> ProjectConfig:
        repo_root = Path(data.get("repo_root", defaults_repo_root))
        if not repo_root.is_absolute():
            repo_root = (config_path.parent / repo_root).resolve()

        source = Path(data["source_path"])
        if not source.is_absolute():
            source = (repo_root / source).resolve()

        staging_raw = data.get("corpus_staging", str(source / "fintech-corpus"))
        staging = Path(staging_raw)
        if not staging.is_absolute():
            staging = (repo_root / staging).resolve()

        corpus_out = Path(data.get("corpus_output", "data_engine/corpus_raw"))
        if not corpus_out.is_absolute():
            corpus_out = (repo_root / corpus_out).resolve()

        return cls(
            project_id=data.get("project_id", "unknown"),
            project_name=data["project_name"],
            engine_name=data.get("engine_name", "MUNTU"),
            codebase_ref=data.get("codebase_ref", "codebase"),
            source_path=source,
            corpus_staging=staging,
            repo_root=repo_root,
            corpus_output=corpus_out,
            features=data.get("features", {}),
            branding=data.get("branding", {}),
            cleanup_legacy_artifacts=data.get("cleanup_legacy_artifacts", []),
            config_path=config_path,
        )

    def feature_enabled(self, name: str) -> bool:
        feat = self.features.get(name)
        if feat is None:
            return False
        if isinstance(feat, bool):
            return feat
        if isinstance(feat, dict):
            return feat.get("enabled", True)
        return bool(feat)

    def feature(self, name: str) -> dict[str, Any]:
        feat = self.features.get(name, {})
        return feat if isinstance(feat, dict) else {}


def load_project_config(path: Path, defaults_repo_root: Path | None = None) -> ProjectConfig:
    if not path.exists():
        raise FileNotFoundError(f"Configuration introuvable: {path}")
    data = json.loads(path.read_text(encoding="utf-8"))
    root = defaults_repo_root or path.resolve().parents[2]
    return ProjectConfig.from_dict(data, path.resolve(), root)
