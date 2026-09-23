"""Package the workshop without local environments, caches or run output."""

import os
from collections.abc import Iterator
from pathlib import Path
from zipfile import ZIP_DEFLATED, ZipFile, ZipInfo

EXCLUDED_DIRECTORIES = {
    ".ruff_cache",
    ".git",
    ".venv",
    "__pycache__",
    ".ipynb_checkpoints",
    "runs",
    "learner_work",
    "artifacts",
    "spark-warehouse",
    "metastore_db",
}
EXCLUDED_FILES = {".DS_Store", "Thumbs.db", "derby.log", ".env"}


def is_local_file(path: Path) -> bool:
    """Identify machine-local files that must stay out of the downloadable project."""
    return (
        path.name in EXCLUDED_FILES
        or path.name.startswith(".env.")
        or path.suffix in {".pyc", ".crc"}
    )


def lab_files(root: Path) -> Iterator[Path]:
    """Walk publishable files, pruning local directories and rejecting included symlinks."""
    for parent, directories, files in os.walk(root):
        directories[:] = sorted(name for name in directories if name not in EXCLUDED_DIRECTORIES)
        for name in directories + files:
            if (Path(parent) / name).is_symlink():
                raise ValueError(f"Use a regular repository file, not a symlink: {name}")
        for name in sorted(files):
            path = Path(parent) / name
            if is_local_file(path) or (path.parent == root and path.suffix == ".zip"):
                continue
            yield path


def package_lab(root: Path, output: Path) -> None:
    """Package the lab and canonical course licence without local files or old downloads."""
    licence = root.parent / "LICENSE"
    if licence.is_symlink():
        raise ValueError("Use a regular course LICENSE file, not a symlink.")
    if not licence.is_file():
        raise ValueError(f"Missing course licence: {licence}")
    sources = [licence, *lab_files(root)]
    with ZipFile(output, "w", compression=ZIP_DEFLATED) as bundle:
        for path in sources:
            archive_path = path.relative_to(root.parent)
            entry = ZipInfo(archive_path.as_posix(), date_time=(1980, 1, 1, 0, 0, 0))
            entry.compress_type = ZIP_DEFLATED
            entry.external_attr = 0o644 << 16
            bundle.writestr(entry, path.read_bytes())


def main() -> None:
    """Create the GitHub Release attachment under the repository's ignored build directory."""
    root = Path(__file__).resolve().parents[1]
    output = root.parent / ".build/releases/pyspark-labs.zip"
    output.parent.mkdir(parents=True, exist_ok=True)
    package_lab(root, output)
    print(f"Packaged {output}")


if __name__ == "__main__":
    main()
