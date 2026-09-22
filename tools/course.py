#!/usr/bin/env python3
"""Build, verify or serve the course using only the Python standard library."""

import argparse
import hashlib
import json
import os
import re
import shutil
import subprocess
import tempfile
from collections import Counter
from collections.abc import Iterator
from functools import partial
from html.parser import HTMLParser
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import unquote, urlsplit

ROOT = Path(__file__).resolve().parents[1]
BUILD = ROOT / ".build"
DIST = ROOT / "dist"
DOCUMENTS = {
    "index.html": "index",
    "core-abstractions-reference.html": "core-reference",
    "joins-reference.html": "joins-reference",
}
EXCLUDED = {
    ".ruff_cache",
    ".git",
    ".venv",
    "__pycache__",
    ".ipynb_checkpoints",
    "runs",
    "artifacts",
    "spark-warehouse",
    "metastore_db",
}
LOCAL_FILES = {".DS_Store", "Thumbs.db", "derby.log", ".env"}
VOID = {
    "area",
    "base",
    "br",
    "col",
    "embed",
    "hr",
    "img",
    "input",
    "link",
    "meta",
    "param",
    "source",
    "track",
    "wbr",
}


def is_local_file(path: Path) -> bool:
    """Identify machine-local files excluded from source receipts and publication."""
    return (
        path.name in LOCAL_FILES or path.name.startswith(".env.") or path.suffix in {".pyc", ".crc"}
    )


def files_under(folder: Path) -> Iterator[Path]:
    """Yield repository files in stable order, pruning local output and rejecting symlinks."""
    for parent, directories, files in os.walk(folder):
        directories[:] = sorted(name for name in directories if name not in EXCLUDED)
        for name in directories + files:
            if (Path(parent) / name).is_symlink():
                raise ValueError(f"Use a regular repository file, not a symlink: {name}")
        for name in sorted(files):
            path = Path(parent) / name
            if not is_local_file(path):
                yield path


def lab_files(lab: Path) -> Iterator[Path]:
    """Yield lab sources while excluding downloads generated beside them."""
    for path in files_under(lab):
        if path.parent == lab and path.suffix == ".zip":
            continue
        yield path


def digest(path: Path) -> str:
    """Return the SHA-256 digest of one file's bytes."""
    return hashlib.sha256(path.read_bytes()).hexdigest()


def input_hashes() -> dict[str, str]:
    """Record the authored build inputs without including generated lab downloads."""
    result = {}
    for folder in ("slides/src", "slides/web", "labs", "tools"):
        root = ROOT / folder
        paths = lab_files(root) if folder == "labs" else files_under(root)
        result.update({path.relative_to(ROOT).as_posix(): digest(path) for path in paths})
    return result


def tree_hashes(folder: Path) -> dict[str, str]:
    """Record relative paths and file hashes for a publishable directory tree."""
    return {path.relative_to(folder).as_posix(): digest(path) for path in files_under(folder)}


class Markup(HTMLParser):
    """Collect structural events, references and IDs without rendering HTML or SVG."""

    def __init__(self, path: Path) -> None:
        """Parse a UTF-8 document for link and native-output verification."""
        super().__init__(convert_charrefs=True)
        self.events = []
        self.links = []
        self.slides = []
        self.ids = []
        self.feed(path.read_text(encoding="utf-8"))

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        """Record IDs, slide markers, resource references and normalised attributes."""
        attributes = dict(attrs)
        if "id" in attributes:
            self.ids.append(attributes["id"])
        if tag == "section" and "slide" in attributes.get("class", "").split():
            self.slides.append(attributes.get("id", ""))
        self.links.extend(
            attributes[name] for name in ("href", "src", "xlink:href") if name in attributes
        )
        self.events.append(("start", tag, sorted(attributes.items())))

    def handle_startendtag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        """Normalise self-closing markup without inventing end tags for void elements."""
        self.handle_starttag(tag, attrs)
        if tag not in VOID:
            self.handle_endtag(tag)

    def handle_endtag(self, tag: str) -> None:
        """Record explicit end tags except those belonging to HTML void elements."""
        if tag not in VOID:
            self.events.append(("end", tag))

    def handle_data(self, data: str) -> None:
        """Preserve meaningful text while ignoring whitespace-only formatting nodes."""
        if data.strip():
            self.events.append(("text", data))


def css_references(site: Path) -> Iterator[tuple[Path, str]]:
    """Yield CSS resource URLs; fragment-only SVG markers belong to consuming documents."""
    for path in site.rglob("*.css"):
        for url in re.findall(r"url\(\s*[\"']?([^\)\"']+)", path.read_text(encoding="utf-8")):
            if not url.startswith("#"):
                yield path, url.strip()


def link_problem(site: Path, markup: dict[Path, Markup], source: Path, url: str) -> str | None:
    """Describe a broken local reference, ignoring links to external destinations."""
    parts = urlsplit(url)
    if parts.scheme or parts.netloc:
        return None
    target = (source.parent / unquote(parts.path)).resolve() if parts.path else source
    prefix = source.relative_to(site)
    if parts.path.startswith("/") or not target.is_relative_to(site):
        return f"{prefix}: resource escapes site: {url}"
    if not target.is_file():
        return f"{prefix}: missing resource: {url}"
    if not parts.fragment or target not in markup:
        return None
    fragments = {parts.fragment, unquote(parts.fragment)}
    if fragments.isdisjoint(markup[target].ids):
        return f"{prefix}: missing fragment: {url}"
    return None


def verify_links(site: Path) -> dict[Path, Markup]:
    """Check duplicate IDs and resolve HTML, SVG and CSS references inside the site."""
    site = site.resolve()
    markup = {
        path.resolve(): Markup(path) for path in site.rglob("*") if path.suffix in {".html", ".svg"}
    }
    findings = []
    for path, parsed in markup.items():
        duplicates = [key for key, count in Counter(parsed.ids).items() if count > 1]
        if duplicates:
            findings.append(f"{path.relative_to(site)}: duplicate IDs {duplicates}")
    references = [(path, url) for path, parsed in markup.items() for url in parsed.links]
    references.extend(css_references(site))
    for source, url in references:
        problem = link_problem(site, markup, source, url)
        if problem:
            findings.append(problem)
    if findings:
        raise ValueError("\n".join(findings))
    return markup


def cell_source(kind: str, lines: list[str]) -> str:
    """Decode a VS Code cell using the notebook author's Markdown comment convention."""
    body = "\n".join(lines).strip()
    if kind == "code":
        return body
    return "\n".join(line[2:] if line.startswith("# ") else line[1:] for line in body.splitlines())


def script_cells(script: str) -> Iterator[tuple[str, str]]:
    """Yield canonical cell kinds and source text without requiring notebook dependencies."""
    kind = None
    lines = []
    for line in script.splitlines() + ["# %%"]:
        if line not in {"# %%", "# %% [markdown]"}:
            if kind is not None:
                lines.append(line)
            continue
        if kind is not None:
            yield kind, cell_source(kind, lines)
        kind = "markdown" if "[markdown]" in line else "code"
        lines = []


def verify_lab(lab: Path) -> None:
    """Require the notebook to contain exactly the editable lesson's cells in order."""
    script, notebook = lab / "hands_on.py", lab / "hands-on.ipynb"
    if not script.is_file() or not notebook.is_file():
        raise ValueError(f"Lab needs hands_on.py and hands-on.ipynb: {lab}")
    expected = list(script_cells(script.read_text(encoding="utf-8")))
    cells = json.loads(notebook.read_text(encoding="utf-8"))["cells"]
    actual = [(cell["cell_type"], "".join(cell["source"])) for cell in cells]
    if actual != expected:
        raise ValueError(
            f"Regenerate {lab.name}/hands-on.ipynb from hands_on.py; the cells differ."
        )


def binary_path() -> Path:
    """Locate the native slide generator produced by this checkout's Oven build."""
    return BUILD / "native/oven/release" / ("main.exe" if os.name == "nt" else "main")


def native_document(target: str) -> bytes:
    """Render one document through the native Incan executable."""
    return subprocess.check_output(
        [str(binary_path())], cwd=ROOT / "slides", env={**os.environ, "INCAN_DECK": target}
    )


def check_document(path: Path, target: str, document: Markup, original: Path | None) -> None:
    """Verify native bytes, slide IDs and an optional historical markup baseline."""
    if path.read_bytes() != native_document(target):
        raise ValueError(f"{path.name} differs from the native generator; rebuild the site.")
    if not document.slides or not all(document.slides):
        raise ValueError(f"{path.name}: every slide needs a stable ID.")
    if original is not None and document.events != Markup(original / path.name).events:
        raise ValueError(f"{path.name}: markup differs from the supplied preservation baseline.")


def check_site(site: Path, compare_original: Path | None = None) -> dict[str, dict[str, int]]:
    """Validate document generation, local resources and the packaged notebook lesson."""
    site = site.resolve()
    parsed = verify_links(site)
    report = {}
    for filename, target in DOCUMENTS.items():
        path = site / filename
        document = parsed[path]
        check_document(path, target, document, compare_original)
        report[filename] = {"slides": len(document.slides), "markup_events": len(document.events)}
    verify_lab(site / "labs")
    return report


def compile_slides(compiler: str) -> None:
    """Type-check and build the renderer with compiler state isolated to this checkout."""
    env = {
        **os.environ,
        "INCAN_HOME": str(BUILD / "incan-home"),
        "CARGO_TARGET_DIR": str(BUILD / "cargo"),
    }
    subprocess.run([compiler, "check", "slides/src/main.incn"], cwd=ROOT, env=env, check=True)
    subprocess.run(
        [
            compiler,
            "build",
            "slides/src/main.incn",
            ".build/native",
            "--report",
            "json",
            "--report-output",
            ".build/build-report.json",
        ],
        cwd=ROOT,
        env=env,
        check=True,
    )


def populate_site(site: Path) -> None:
    """Assemble native documents, browser assets and the guided lab files."""
    shutil.copytree(ROOT / "slides/web", site)
    for filename, target in DOCUMENTS.items():
        (site / filename).write_bytes(native_document(target))
    for path in lab_files(ROOT / "labs"):
        destination = site / path.relative_to(ROOT)
        destination.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(path, destination)


def build(compare_original: Path | None) -> None:
    """Build and validate a temporary site before replacing the previous generated output."""
    BUILD.mkdir(exist_ok=True)
    compiler = os.environ.get("INCAN_BINARY", "incan")
    version = subprocess.check_output([compiler, "--version"], text=True).strip()
    print(version, flush=True)
    before = input_hashes()
    compile_slides(compiler)
    with tempfile.TemporaryDirectory(prefix="course-", dir=BUILD) as temporary:
        site = Path(temporary).resolve() / "site"
        populate_site(site)
        report = check_site(site, compare_original)
        if before != input_hashes():
            raise ValueError("Course sources changed during the build; run the build again.")
        receipt = {
            "compiler": version,
            "inputs": before,
            "binary_sha256": digest(binary_path()),
            "site": tree_hashes(site),
            "documents": report,
        }
        if DIST.exists():
            DIST.rename(Path(temporary) / "previous-site")
        site.rename(DIST)
    (BUILD / "course-build.json").write_text(json.dumps(receipt, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(report, indent=2))
    print("Built dist/ with local assets, references and labs.")


def verify(compare_original: Path | None) -> None:
    """Reject stale inputs or altered output, then rerun the full site verification."""
    receipt = json.loads((BUILD / "course-build.json").read_text(encoding="utf-8"))
    if input_hashes() != receipt["inputs"]:
        raise ValueError("Course inputs have changed since the last build; run the build again.")
    if digest(binary_path()) != receipt["binary_sha256"] or tree_hashes(DIST) != receipt["site"]:
        raise ValueError("Generated files have changed since the last build; run the build again.")
    report = check_site(DIST, compare_original)
    print(json.dumps(report, indent=2))
    print(
        "Verified current sources, native output, notebook cells and all local HTML/SVG/CSS links."
    )


class PreviewHandler(SimpleHTTPRequestHandler):
    """Serve local preview files without retaining stale browser responses."""

    def end_headers(self) -> None:
        """Add the preview cache policy before finishing each HTTP response header."""
        self.send_header("Cache-Control", "no-cache")
        super().end_headers()


def serve(port: int) -> None:
    """Serve the built course on loopback, falling back to an available port."""
    if not (DIST / "index.html").is_file():
        raise ValueError("No built course yet. Run: python3 tools/course.py build")
    handler = partial(PreviewHandler, directory=str(DIST))
    try:
        server = ThreadingHTTPServer(("127.0.0.1", port), handler)
    except OSError:
        server = ThreadingHTTPServer(("127.0.0.1", 0), handler)
    print(
        f"Course preview: http://127.0.0.1:{server.server_port}/\nPress Ctrl+C to stop.", flush=True
    )
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        pass
    finally:
        server.server_close()


def main() -> None:
    """Dispatch the build, verification or local preview command."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("command", choices=("build", "verify", "serve"))
    parser.add_argument(
        "--compare-original", type=Path, help="Compare markup with a preserved HTML corpus."
    )
    parser.add_argument("--port", type=int, default=8766)
    args = parser.parse_args()
    original = args.compare_original.resolve() if args.compare_original else None
    if args.command == "build":
        build(original)
    elif args.command == "verify":
        verify(original)
    else:
        serve(args.port)


if __name__ == "__main__":
    try:
        main()
    except (OSError, ValueError, subprocess.CalledProcessError) as error:
        raise SystemExit(str(error))
