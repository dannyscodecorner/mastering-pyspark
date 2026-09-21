#!/usr/bin/env python3
"""Build, verify or serve the course. Uses only the Python standard library."""

import argparse
from collections import Counter
from functools import partial
import hashlib
from html.parser import HTMLParser
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
import json
import os
from pathlib import Path
import re
import shutil
import subprocess
import tempfile
from urllib.parse import unquote, urlsplit
from zipfile import ZipFile, ZipInfo, ZIP_DEFLATED


ROOT = Path(__file__).resolve().parents[1]
BUILD = ROOT / ".build"
DIST = ROOT / "dist"
DOCUMENTS = {
    "index.html": "index",
    "core-abstractions-reference.html": "core-reference",
    "joins-reference.html": "joins-reference",
}
EXCLUDED = {
    ".git", ".venv", "__pycache__", ".ipynb_checkpoints", "runs", "artifacts",
    "spark-warehouse", "metastore_db",
}
VOID = {"area", "base", "br", "col", "embed", "hr", "img", "input", "link", "meta", "param", "source", "track", "wbr"}


def files_under(folder):
    """Keep environments, run output and machine-local files out of the site."""
    for parent, dirs, files in os.walk(folder):
        dirs[:] = sorted(d for d in dirs if d not in EXCLUDED)
        for name in dirs + files:
            if (Path(parent) / name).is_symlink():
                raise ValueError(f"Use a regular repository file, not a symlink: {name}")
        for name in sorted(files):
            if name in {".DS_Store", "Thumbs.db", "derby.log", ".env"} or name.startswith(".env."):
                continue
            path = Path(parent) / name
            if path.suffix not in {".pyc", ".crc"}:
                yield path


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def input_hashes():
    result = {}
    for folder in ("slides/src", "slides/web", "labs", "tools"):
        for path in files_under(ROOT / folder):
            if path.parent == ROOT / "labs" and path.suffix == ".zip":
                continue
            result[path.relative_to(ROOT).as_posix()] = digest(path)
    return result


def tree_hashes(folder):
    return {p.relative_to(folder).as_posix(): digest(p) for p in files_under(folder)}


class Markup(HTMLParser):
    def __init__(self, path):
        super().__init__(convert_charrefs=True)
        self.events, self.links, self.slides, self.ids = [], [], [], []
        self.feed(path.read_text(encoding="utf-8"))

    def handle_starttag(self, tag, attrs):
        attrs = dict(attrs)
        if "id" in attrs:
            self.ids.append(attrs["id"])
        if tag == "section" and "slide" in attrs.get("class", "").split():
            self.slides.append(attrs.get("id", ""))
        for name in ("href", "src", "xlink:href"):
            if name in attrs:
                self.links.append(attrs[name])
        self.events.append(("start", tag, sorted(attrs.items())))

    def handle_startendtag(self, tag, attrs):
        self.handle_starttag(tag, attrs)
        if tag not in VOID:
            self.handle_endtag(tag)

    def handle_endtag(self, tag):
        if tag not in VOID:
            self.events.append(("end", tag))

    def handle_data(self, data):
        if data.strip():
            self.events.append(("text", data))


def verify_links(site):
    """Resolve local HTML/SVG links and CSS resources entirely inside the site."""
    markup = {p.resolve(): Markup(p) for p in site.rglob("*") if p.suffix in {".html", ".svg"}}
    findings = []
    for path, parsed in markup.items():
        duplicates = [key for key, count in Counter(parsed.ids).items() if count > 1]
        if duplicates:
            findings.append(f"{path.relative_to(site)}: duplicate IDs {duplicates}")
    references = [(path, url) for path, parsed in markup.items() for url in parsed.links]
    for path in site.rglob("*.css"):
        for url in re.findall(r"url\(\s*[\"']?([^\)\"']+)", path.read_text(encoding="utf-8")):
            # SVG markers referenced by CSS belong to the consuming document.
            if not url.startswith("#"):
                references.append((path, url.strip()))
    for source, url in references:
        parts = urlsplit(url)
        if parts.scheme or parts.netloc:
            continue
        target = (source.parent / unquote(parts.path)).resolve() if parts.path else source
        if parts.path.startswith("/") or not target.is_relative_to(site):
            findings.append(f"{source.relative_to(site)}: resource escapes site: {url}")
        elif not target.is_file():
            findings.append(f"{source.relative_to(site)}: missing resource: {url}")
        elif parts.fragment and target in markup and not ({parts.fragment, unquote(parts.fragment)} & set(markup[target].ids)):
            findings.append(f"{source.relative_to(site)}: missing fragment: {url}")
    if findings:
        raise ValueError("\n".join(findings))
    return markup


def verify_lab(lab):
    """Check that the optional notebook still represents the editable lesson."""
    script, notebook = lab / "hands_on.py", lab / "hands-on.ipynb"
    if not script.is_file() or not notebook.is_file():
        return
    expected, kind, lines = [], None, []
    for line in script.read_text(encoding="utf-8").splitlines() + ["# %%"]:
        if line in {"# %%", "# %% [markdown]"}:
            if kind is not None:
                body = "\n".join(lines).strip()
                if kind == "markdown":
                    body = "\n".join(p[2:] if p.startswith("# ") else p[1:] for p in body.splitlines())
                expected.append((kind, body))
            kind, lines = ("markdown" if "[markdown]" in line else "code"), []
        elif kind is not None:
            lines.append(line)
    actual = json.loads(notebook.read_text(encoding="utf-8"))["cells"]
    actual = [(c["cell_type"], "".join(c["source"]) if isinstance(c["source"], list) else c["source"]) for c in actual]
    if actual != expected:
        raise ValueError(f"Regenerate {lab.name}/hands-on.ipynb from hands_on.py; the cells differ.")


def binary_path():
    return BUILD / "native/oven/release" / ("main.exe" if os.name == "nt" else "main")


def native_document(target):
    return subprocess.check_output([str(binary_path())], cwd=ROOT / "slides", env={**os.environ, "INCAN_DECK": target})


def check_site(site, compare_original=None):
    parsed = verify_links(site)
    report = {}
    for filename, target in DOCUMENTS.items():
        path = site / filename
        if path.read_bytes() != native_document(target):
            raise ValueError(f"{filename} differs from the native generator; rebuild the site.")
        document = parsed[path]
        if not document.slides or not all(document.slides):
            raise ValueError(f"{filename}: every slide needs a stable ID.")
        if compare_original:
            old = Markup(compare_original / filename)
            if document.events != old.events:
                raise ValueError(f"{filename}: markup differs from the supplied preservation baseline.")
        report[filename] = {"slides": len(document.slides), "markup_events": len(document.events)}
    for lab in (site / "labs").iterdir():
        if lab.is_dir():
            verify_lab(lab)
    return report


def package_lab(lab, output):
    with ZipFile(output, "w", compression=ZIP_DEFLATED) as bundle:
        for path in files_under(lab):
            entry = ZipInfo((Path(lab.name) / path.relative_to(lab)).as_posix(), date_time=(1980, 1, 1, 0, 0, 0))
            entry.compress_type = ZIP_DEFLATED
            entry.external_attr = 0o644 << 16
            bundle.writestr(entry, path.read_bytes())


def build(compare_original):
    BUILD.mkdir(exist_ok=True)
    compiler = os.environ.get("INCAN_BINARY", "incan")
    version = subprocess.check_output([compiler, "--version"], text=True).strip()
    print(version, flush=True)
    before = input_hashes()
    env = {**os.environ, "INCAN_HOME": str(BUILD / "incan-home"), "CARGO_TARGET_DIR": str(BUILD / "cargo")}
    subprocess.run([compiler, "check", "slides/src/main.incn"], cwd=ROOT, env=env, check=True)
    subprocess.run([compiler, "build", "slides/src/main.incn", ".build/native", "--report", "json", "--report-output", ".build/build-report.json"], cwd=ROOT, env=env, check=True)
    with tempfile.TemporaryDirectory(prefix="course-", dir=BUILD) as temporary:
        site = Path(temporary).resolve() / "site"
        shutil.copytree(ROOT / "slides/web", site)
        for filename, target in DOCUMENTS.items():
            (site / filename).write_bytes(native_document(target))
        for path in files_under(ROOT / "labs"):
            if path.parent == ROOT / "labs" and path.suffix == ".zip":
                continue
            destination = site / path.relative_to(ROOT)
            destination.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(path, destination)
        for lab in (site / "labs").iterdir():
            if lab.is_dir():
                package_lab(lab, site / "labs" / f"{lab.name}-lab.zip")
        report = check_site(site, compare_original)
        if before != input_hashes():
            raise ValueError("Course sources changed during the build; run the build again.")
        receipt = {"compiler": version, "inputs": before, "binary_sha256": digest(binary_path()), "site": tree_hashes(site), "documents": report}
        # Only replace the previous generated site after all checks have passed.
        if DIST.exists():
            DIST.rename(Path(temporary) / "previous-site")
        site.rename(DIST)
    (BUILD / "course-build.json").write_text(json.dumps(receipt, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(report, indent=2))
    print("Built dist/ with local assets, references, labs and lab downloads.")


def verify(compare_original):
    receipt = json.loads((BUILD / "course-build.json").read_text(encoding="utf-8"))
    if input_hashes() != receipt["inputs"]:
        raise ValueError("Course inputs have changed since the last build; run the build again.")
    if digest(binary_path()) != receipt["binary_sha256"] or tree_hashes(DIST) != receipt["site"]:
        raise ValueError("Generated files have changed since the last build; run the build again.")
    report = check_site(DIST, compare_original)
    print(json.dumps(report, indent=2))
    print("Verified current sources, native output, notebook cells and all local HTML/SVG/CSS links.")


class PreviewHandler(SimpleHTTPRequestHandler):
    def end_headers(self):
        self.send_header("Cache-Control", "no-cache")
        super().end_headers()


def serve(port):
    if not (DIST / "index.html").is_file():
        raise ValueError("No built course yet. Run: python3 tools/course.py build")
    handler = partial(PreviewHandler, directory=str(DIST))
    try:
        server = ThreadingHTTPServer(("127.0.0.1", port), handler)
    except OSError:
        server = ThreadingHTTPServer(("127.0.0.1", 0), handler)
    print(f"Course preview: http://127.0.0.1:{server.server_port}/\nPress Ctrl+C to stop.", flush=True)
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        pass
    finally:
        server.server_close()


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("command", choices=("build", "verify", "serve"))
    parser.add_argument("--compare-original", type=Path, help="Optionally compare slide markup with a preserved HTML corpus.")
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
