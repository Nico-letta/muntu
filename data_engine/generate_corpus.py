import os
import re
import subprocess
import sys

COMPILE_EXTENSIONS = (".md", ".tsx", ".ts", ".txt")
SKIP_FILES = {"README.md", "CONSOLIDATION-MAP.md"}

SUBFOLDER_ORDER = {
    "input-boundaries": 10,
    "execution-lifecycle": 20,
    "error-resilience": 30,
    "providers": 40,
}


def _path_sort_key(relative_path: str) -> tuple:
    parts = relative_path.replace("\\", "/").split("/")
    keys: list[tuple] = []
    for part in parts:
        is_file = re.search(r"\.(md|tsx|ts|txt)$", part, re.I)
        if is_file:
            keys.append((1, 0, part.lower()))
            continue
        numbered = re.match(r"^(\d+)-", part)
        if numbered:
            keys.append((0, int(numbered.group(1)), part.lower()))
        elif part in SUBFOLDER_ORDER:
            keys.append((1, SUBFOLDER_ORDER[part], part.lower()))
        else:
            keys.append((1, 50, part.lower()))
    return tuple(keys)


def collect_files(raw_dir: str) -> list[tuple[str, str]]:
    """Collecte et trie déterministiquement tous les fichiers compilables."""
    collected: list[tuple[tuple, str, str]] = []
    for root, _, file_names in os.walk(raw_dir):
        for file in file_names:
            if not file.endswith(COMPILE_EXTENSIONS) or file in SKIP_FILES:
                continue
            full_path = os.path.join(root, file)
            relative_path = os.path.relpath(full_path, raw_dir)
            collected.append(
                (_path_sort_key(relative_path), relative_path.replace("\\", "/"), full_path)
            )
    collected.sort(key=lambda item: item[0])
    return [(full, rel) for _, rel, full in collected]


def run_corpus_linter() -> bool:
    """Execute lint_corpus.py avant compilation. Retourne True si OK."""
    lint_script = os.path.join(os.path.dirname(os.path.abspath(__file__)), "lint_corpus.py")
    if not os.path.exists(lint_script):
        print("[WARN] lint_corpus.py introuvable — compilation sans lint")
        return True
    result = subprocess.run([sys.executable, lint_script], capture_output=False)
    return result.returncode == 0


def generate_pretrain_corpus():
    base_dir = os.path.dirname(os.path.abspath(__file__))
    raw_dir = os.path.join(base_dir, "corpus_raw")
    output_dir = os.path.join(base_dir, "_output")
    output_file = os.path.join(output_dir, "corpus_pretrain.txt")

    if not os.path.exists(output_dir):
        os.makedirs(output_dir)

    print("[*] Demarrage de la compilation du corpus MUNTU...")

    if not run_corpus_linter():
        print("[-] Compilation annulee — corriger les erreurs de lint")
        sys.exit(1)

    collected_text: list[str] = []
    files = collect_files(raw_dir)

    for file_path, relative_path in files:
        try:
            with open(file_path, "r", encoding="utf-8") as f:
                content = f.read()
            collected_text.append(f"\n--- START FILE: {relative_path} ---\n")
            collected_text.append(content)
            collected_text.append(f"\n--- END FILE: {relative_path} ---\n")
        except Exception as e:
            print(f"[-] Erreur de lecture sur {relative_path}: {e}")

    with open(output_file, "w", encoding="utf-8") as f_out:
        f_out.write("".join(collected_text))

    size_mo = os.path.getsize(output_file) / (1024 * 1024)
    print(f"[+] {len(files)} fichiers compiles -> {output_file} ({size_mo:.2f} Mo)")


if __name__ == "__main__":
    generate_pretrain_corpus()
