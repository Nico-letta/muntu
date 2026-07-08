"""Extracteurs generiques et orchestrateur — moteur aveugle pilote par config."""

from __future__ import annotations

import json
import re
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Iterable

from .config import ProjectConfig


@dataclass
class ExtractContext:
    cfg: ProjectConfig

    @property
    def codebase(self) -> Path:
        return self.cfg.source_path

    @property
    def staging(self) -> Path:
        return self.cfg.corpus_staging

    @property
    def corpus(self) -> Path:
        return self.cfg.corpus_output

    @property
    def repo_root(self) -> Path:
        return self.cfg.repo_root

    @property
    def product_name(self) -> str:
        return self.cfg.project_name

    @property
    def engine_name(self) -> str:
        return self.cfg.engine_name

    def source_ref(self, rel_path: str) -> str:
        return f"{self.cfg.codebase_ref}/{rel_path.lstrip('/')}"

    def sanitize(self, text: str) -> str:
        branding = self.cfg.branding
        for alias in branding.get("path_aliases", []):
            text = text.replace(alias["from"], alias["to"])
        for repl in branding.get("text_replacements", []):
            if repl.get("regex"):
                text = re.sub(repl["pattern"], repl["repl"], text)
            else:
                text = text.replace(repl["pattern"], repl["repl"])
        return text

    def write_corpus(self, rel_out: str | Path, content: str) -> None:
        path = self.corpus / rel_out if isinstance(rel_out, str) else rel_out
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(self.sanitize(content), encoding="utf-8")

    def resolve_repo_file(self, rel: str) -> Path:
        p = Path(rel)
        return p if p.is_absolute() else self.repo_root / rel


def _should_skip(path: Path, exclude_dirs: Iterable[str]) -> bool:
    return any(part in exclude_dirs for part in path.parts)


def iter_source_files(
    root: Path,
    extensions: list[str],
    exclude_dirs: list[str],
) -> list[Path]:
    if not root.exists():
        return []
    ext_set = {e if e.startswith(".") else f".{e}" for e in extensions}
    files: list[Path] = []
    for path in sorted(root.rglob("*")):
        if not path.is_file():
            continue
        if _should_skip(path, exclude_dirs):
            continue
        if path.suffix.lower() in ext_set:
            files.append(path)
    return files


def export_src_bundle(ctx: ExtractContext, spec: dict[str, Any]) -> None:
    src_subdir = spec.get("src_subdir", "src")
    src_root = ctx.codebase / src_subdir
    extensions = spec.get("extensions", [".js", ".ts", ".tsx"])
    exclude = spec.get("exclude_dirs", ["node_modules", "dist", ".next"])
    output = spec["output"]
    fence_lang = spec.get("fence_lang", "typescript")
    title = spec.get("title") or f"{ctx.product_name} — Source Bundle"

    if not src_root.exists():
        print(f"[WARN] Source root absent: {src_root}")
        return

    print(f"[*] Extraction bundle depuis {src_root}")
    parts = [
        f"# {title}\n\n",
        f"> Fichiers sous `{ctx.source_ref(src_subdir + '/')}` "
        f"pour entrainement MoE {ctx.engine_name}.\n\n",
    ]
    for path in iter_source_files(src_root, extensions, exclude):
        rel = path.relative_to(ctx.codebase).as_posix()
        code = ctx.sanitize(path.read_text(encoding="utf-8"))
        parts.append(f"## `{rel}`\n\n```{fence_lang}\n{code}\n```\n\n")

    ctx.write_corpus(output, "".join(parts))


def export_schema_prisma(ctx: ExtractContext, spec: dict[str, Any]) -> None:
    rel = spec.get("path", "prisma/schema.prisma")
    output = spec.get("output", "25-database-storage/schema-prisma-full.md")
    src = ctx.codebase / rel
    if not src.exists():
        print(f"[WARN] Prisma schema absent: {src}")
        return
    code = src.read_text(encoding="utf-8")
    ctx.write_corpus(
        output,
        f"# Prisma Schema — {ctx.product_name} (source complete)\n\n"
        f"> Source: `{ctx.source_ref(rel)}`\n\n"
        f"```prisma\n{code}\n```\n",
    )


def export_golden_snippet_md(ctx: ExtractContext, item: dict[str, Any]) -> None:
    rel_src = item["source"]
    src = ctx.codebase / rel_src
    if not src.exists():
        print(f"[WARN] Missing source {src}")
        return
    layer = item["layer"]
    name = item["name"]
    description = item.get("description", "")
    lang = item.get("lang", "typescript")
    code = ctx.sanitize(src.read_text(encoding="utf-8"))
    content = (
        f"# Golden Snippet — `{rel_src}`\n\n"
        f"> **Couche:** `{layer}` · **Source:** `{ctx.source_ref(rel_src)}`\n\n"
        f"{description}\n\n"
        f"```{lang}\n{code}\n```\n"
    )
    ctx.write_corpus(f"{layer}/golden-snippets/{name}.md", content)


def _render_header(ctx: ExtractContext, header: str, rel_src: str) -> str:
    if not header:
        return ""
    return (
        header.replace("{product_name}", ctx.product_name)
        .replace("{engine_name}", ctx.engine_name)
        .replace("{source_ref}", ctx.source_ref(rel_src))
    )


def export_golden_ts_snippet(ctx: ExtractContext, item: dict[str, Any]) -> None:
    rel_src = item["source"]
    output = item["output"]
    header = _render_header(ctx, item.get("header", ""), rel_src)
    ranges = item.get("line_ranges")
    src = ctx.codebase / rel_src
    if not src.exists():
        print(f"[WARN] Missing TS source {src}")
        return
    lines = src.read_text(encoding="utf-8").splitlines()
    if ranges:
        chunks = ["\n".join(lines[s - 1 : e]) for s, e in ranges]
        body = "\n\n// --- excerpt ---\n\n".join(chunks)
    else:
        body = "\n".join(lines)
    ctx.write_corpus(output, header + body + "\n")


def export_test_specs(ctx: ExtractContext, spec: dict[str, Any]) -> None:
    test_dir = ctx.codebase / spec.get("test_dir", "test")
    if not test_dir.exists():
        return
    extensions = spec.get("extensions", [".ts"])
    fence = spec.get("fence_lang", "typescript")
    output = spec["output"]
    parts = [f"# {ctx.product_name} E2E Test Specifications\n\n"]
    for path in iter_source_files(test_dir, extensions, []):
        code = ctx.sanitize(path.read_text(encoding="utf-8"))
        parts.append(f"## `{path.name}`\n\n```{fence}\n{code}\n```\n\n")
    ctx.write_corpus(output, "".join(parts))


def export_static_files(ctx: ExtractContext, spec: dict[str, Any]) -> None:
    for item in spec.get("items", []):
        rel_src = item["source"]
        src = ctx.codebase / rel_src
        if not src.exists():
            print(f"[WARN] Fichier statique absent: {src}")
            continue
        raw = ctx.sanitize(src.read_text(encoding="utf-8"))
        if item.get("as_code"):
            fence = item.get("fence_lang", "text")
            body = f"```\n{raw}\n```" if fence == "text" else f"```{fence}\n{raw}\n```"
            content = (
                f"# {item.get('title', rel_src)}\n\n"
                f"> Source: `{ctx.source_ref(rel_src)}`\n\n"
                f"{body}\n"
            )
        elif item.get("wrap_markdown"):
            content = (
                f"# {item.get('title', rel_src)}\n\n"
                f"> Source: `{ctx.source_ref(rel_src)}`\n\n"
                f"{raw}\n"
            )
        else:
            content = raw
        ctx.write_corpus(item["output"], content)


def export_env_template(ctx: ExtractContext, spec: dict[str, Any]) -> None:
    output = spec["output"]
    if spec.get("inline"):
        body = spec["inline"]
    else:
        src = ctx.codebase / spec.get("source", ".env.example")
        if not src.exists():
            print(f"[WARN] Env template absent: {src}")
            return
        body = src.read_text(encoding="utf-8")
    header = spec.get(
        "header",
        f"# {ctx.product_name} Environment Variables\n\n"
        f"> Template sans secrets — source: `{ctx.source_ref('.env.example')}`\n\n",
    )
    ctx.write_corpus(output, header + body)


def export_instruction_pairs(ctx: ExtractContext, spec: dict[str, Any]) -> None:
    rel = spec.get("path", "training/instruction-response.jsonl")
    jsonl = ctx.staging / rel
    if not jsonl.exists():
        print(f"[WARN] Missing {jsonl}")
        return
    output = spec.get("output", "35-business-flows/instruction-response-pairs.md")
    parts = [
        f"# Instruction-Response Training Pairs ({ctx.product_name})\n\n",
        f"> Source: {ctx.source_ref(f'fintech-corpus/{rel}')}\n\n",
    ]
    for i, line in enumerate(jsonl.read_text(encoding="utf-8").strip().splitlines(), 1):
        obj = json.loads(line)
        meta = obj.get("metadata", {})
        parts.append(f"## Pair {i}\n\n")
        parts.append(f"**Instruction:** {obj.get('instruction', '')}\n\n")
        parts.append(f"**Output:** {obj.get('output', '')}\n\n")
        parts.append(
            f"*Domain:* `{meta.get('domain', '')}` | "
            f"*Country:* `{meta.get('country', 'global')}` | "
            f"*Difficulty:* `{meta.get('difficulty', '')}`\n\n---\n\n"
        )
    ctx.write_corpus(output, "".join(parts))


def export_multi_turn_scenarios(ctx: ExtractContext, spec: dict[str, Any]) -> None:
    rel = spec.get("path", "training/scenarios-multi-turn.jsonl")
    jsonl = ctx.staging / rel
    if not jsonl.exists():
        return
    output = spec.get("output", "35-business-flows/multi-turn-scenarios.md")
    parts = [f"# Multi-Turn Training Scenarios ({ctx.product_name})\n\n"]
    for i, line in enumerate(jsonl.read_text(encoding="utf-8").strip().splitlines(), 1):
        obj = json.loads(line)
        parts.append(f"## Scenario {i}\n\n")
        for msg in obj.get("messages", []):
            parts.append(f"**{msg.get('role', 'unknown').upper()}:**\n\n{msg.get('content', '')}\n\n")
        parts.append(f"*Metadata:* `{json.dumps(obj.get('metadata', {}), ensure_ascii=False)}`\n\n---\n\n")
    ctx.write_corpus(output, "".join(parts))


def export_legacy_knowledge(ctx: ExtractContext, spec: dict[str, Any]) -> None:
    rel = spec.get("path", "legacy/knowledge-json")
    legacy = ctx.staging / rel
    if not legacy.exists():
        return
    out_dir_rel = spec.get("output_dir", "40-compliance-rules/legacy-knowledge")
    for path in sorted(legacy.glob("*.json")):
        raw = path.read_text(encoding="utf-8")
        try:
            pretty = json.dumps(json.loads(raw), indent=2, ensure_ascii=False)
            body = f"```json\n{pretty}\n```"
        except json.JSONDecodeError:
            body = f"```json\n{raw}\n```"
        ctx.write_corpus(f"{out_dir_rel}/{path.stem}.md", f"# Legacy Knowledge — {path.stem}\n\n{body}\n")


def export_postman_and_env(ctx: ExtractContext, spec: dict[str, Any]) -> None:
    out_dir = spec.get("output_dir", "30-system-integrations/source-docs")
    for mapping in spec.get("postman_files", []):
        src = ctx.codebase / mapping["source"]
        if src.exists():
            ctx.write_corpus(f"{out_dir}/{mapping['output']}", src.read_text(encoding="utf-8"))
    env_rel = spec.get("env_example")
    if env_rel:
        env = ctx.codebase / env_rel
        if env.exists():
            ctx.write_corpus(
                f"{out_dir}/{spec.get('env_output', 'env-example.txt')}",
                f"# {ctx.product_name} Environment Variables\n\n" + env.read_text(encoding="utf-8"),
            )


def export_postman_narrative(ctx: ExtractContext, spec: dict[str, Any]) -> None:
    src_rel = spec["source"]
    src = ctx.codebase / src_rel
    if not src.exists():
        return
    raw = ctx.sanitize(src.read_text(encoding="utf-8"))
    output = spec["output"]
    folders = spec.get("folders_description", "")
    ctx.write_corpus(
        output,
        f"# {ctx.product_name} — Reference API Postman\n\n"
        f"> Source: `{ctx.source_ref(src_rel)}`\n\n"
        f"{folders}\n\n"
        "## Collection JSON complete\n\n"
        f"```json\n{raw}\n```\n",
    )


def export_provider_docs(ctx: ExtractContext, spec: dict[str, Any]) -> None:
    out_dir = spec.get("output_dir", "30-system-integrations/source-docs")
    for doc in spec.get("documents", []):
        src = ctx.resolve_repo_file(doc["source"])
        if not src.exists():
            print(f"[WARN] Doc provider absent: {src}")
            continue
        text = src.read_text(encoding="utf-8")
        for out in doc.get("outputs", []):
            if out.get("type") == "copy":
                ctx.write_corpus(f"{out_dir}/{out['file']}", text)
            elif out.get("type") == "airtel_split":
                lines = text.splitlines()
                ussd_end = out.get("ussd_lines", 60)
                api_start = out.get("api_start_line", 853)
                combined = (
                    "# Airtel Money USSD and Banking (Congo)\n\n"
                    + "\n".join(lines[:ussd_end])
                    + "\n\n# Airtel Africa Open API Reference\n\n"
                    + "\n".join(lines[api_start:])
                )
                ctx.write_corpus(f"{out_dir}/{out['file']}", combined)
            elif out.get("type") == "mtn_sandbox_matrix":
                _export_mtn_sandbox_matrix(ctx, src, out["file"])


def _export_mtn_sandbox_matrix(ctx: ExtractContext, momo: Path, out_file: str) -> None:
    lines = momo.read_text(encoding="utf-8").splitlines()
    start = next((i for i, l in enumerate(lines) if "Sandbox Use Case\tTesting Values" in l), None)
    end = next((i for i, l in enumerate(lines) if l.strip() == "← Use CasesCommon Error Codes →"), None)
    if start is None or end is None:
        return
    block = "\n".join(lines[start:end])
    ctx.write_corpus(
        out_file,
        "# MTN MoMo Sandbox Test Matrix (complete)\n\n"
        "> Source: Momo documentation.txt — Sandbox Use Cases section\n\n"
        f"```\n{block}\n```\n",
    )


def export_dir_copy(ctx: ExtractContext, spec: dict[str, Any]) -> None:
    src = ctx.codebase / spec["source"]
    if not src.exists():
        return
    out_dir = spec["output_dir"]
    for path in src.glob(spec.get("glob", "*")):
        if path.is_file():
            ctx.write_corpus(f"{out_dir}/{path.name}", path.read_text(encoding="utf-8"))


def export_knowledge_chunks(ctx: ExtractContext, spec: dict[str, Any]) -> None:
    rel = spec.get("path", "training/knowledge-chunks-rag.jsonl")
    jsonl = ctx.staging / rel
    if not jsonl.exists():
        return
    output = spec.get("output", "35-business-flows/knowledge-chunks-expanded.md")
    parts = ["# Knowledge Chunks RAG — Version enrichie\n\n"]
    for line in jsonl.read_text(encoding="utf-8").strip().splitlines():
        chunk = json.loads(line)
        meta = chunk.get("metadata", {})
        tags = ", ".join(meta.get("tags", []))
        domain = meta.get("domain", "")
        country = meta.get("country", "multi")
        cid = chunk.get("id", "unknown")
        parts.append(f"## Chunk: `{cid}`\n\n")
        parts.append(f"**Domaine:** `{domain}` | **Pays:** `{country}` | **Tags:** {tags}\n\n")
        parts.append(f"**Source:** `{meta.get('source_file', '')}`\n\n")
        parts.append("### Contenu canonique\n\n")
        parts.append(f"{chunk.get('text', '')}\n\n")
        parts.append(f"### Implications integration {ctx.product_name}\n\n")
        parts.append(
            f"Ce chunk ancre l'expert MoE `{domain}` pour le marche `{country}`. "
            f"Croiser avec `providerTxId`, `eventKey`, schema Prisma.\n\n"
        )
        parts.append("---\n\n")
    ctx.write_corpus(output, "".join(parts))


def cleanup_legacy_artifacts(ctx: ExtractContext) -> None:
    for rel in ctx.cfg.cleanup_legacy_artifacts:
        path = ctx.corpus / rel
        if path.exists():
            path.unlink()
            print(f"[*] Supprime artefact legacy: {rel}")


class ExtractionEngine:
    """Orchestrateur : lit la config, execute les extracteurs actives."""

    def __init__(self, config: ProjectConfig) -> None:
        self.config = config
        self.ctx = ExtractContext(config)

    def run(self) -> None:
        cfg = self.config
        ctx = self.ctx
        print(f"[*] MUNTU ExtractionEngine — projet `{cfg.project_id}` ({cfg.project_name})")
        print(f"    codebase: {cfg.source_path}")
        print(f"    corpus:   {cfg.corpus_output}")

        cleanup_legacy_artifacts(ctx)

        if cfg.feature_enabled("provider_docs"):
            export_provider_docs(ctx, cfg.feature("provider_docs"))

        if cfg.feature_enabled("extract_prisma"):
            export_schema_prisma(ctx, cfg.feature("extract_prisma"))

        if cfg.feature_enabled("extract_src_bundle"):
            export_src_bundle(ctx, cfg.feature("extract_src_bundle"))

        feat_md = cfg.feature("golden_snippets_md")
        if cfg.feature_enabled("golden_snippets_md"):
            for item in feat_md.get("items", []):
                export_golden_snippet_md(ctx, item)

        feat_ts = cfg.feature("golden_snippets_ts")
        if cfg.feature_enabled("golden_snippets_ts"):
            for item in feat_ts.get("items", []):
                export_golden_ts_snippet(ctx, item)

        if cfg.feature_enabled("training_pairs"):
            export_instruction_pairs(ctx, cfg.feature("training_pairs"))

        if cfg.feature_enabled("multi_turn_scenarios"):
            export_multi_turn_scenarios(ctx, cfg.feature("multi_turn_scenarios"))

        if cfg.feature_enabled("legacy_knowledge"):
            export_legacy_knowledge(ctx, cfg.feature("legacy_knowledge"))

        if cfg.feature_enabled("postman"):
            feat_pm = cfg.feature("postman")
            export_postman_and_env(ctx, feat_pm)
            if feat_pm.get("narrative"):
                export_postman_narrative(ctx, feat_pm["narrative"])

        if cfg.feature_enabled("test_specs"):
            export_test_specs(ctx, cfg.feature("test_specs"))

        if cfg.feature_enabled("smile_templates"):
            export_dir_copy(ctx, cfg.feature("smile_templates"))

        if cfg.feature_enabled("knowledge_chunks"):
            export_knowledge_chunks(ctx, cfg.feature("knowledge_chunks"))

        if cfg.feature_enabled("static_files"):
            export_static_files(ctx, cfg.feature("static_files"))

        if cfg.feature_enabled("env_template"):
            export_env_template(ctx, cfg.feature("env_template"))

        from .plugins import fintech as fintech_plugin

        fintech_plugin.run(ctx, cfg)
        print("[+] Corpus source expansion complete")
