"""Package the workshop without local environments, caches or run output."""

from pathlib import Path
from zipfile import ZIP_DEFLATED, ZipFile

root = Path(__file__).resolve().parents[1]
excluded = {".venv", "__pycache__", ".ipynb_checkpoints", "runs", "artifacts", "spark-warehouse", "metastore_db"}
output = root.parent / "chapter08-lab.zip"
with ZipFile(output, "w", compression=ZIP_DEFLATED) as bundle:
    for path in sorted(root.rglob("*")):
        relative = path.relative_to(root)
        if not path.is_file() or excluded.intersection(relative.parts):
            continue
        if path.name in {".DS_Store", "derby.log"} or path.suffix in {".pyc", ".crc"}:
            continue
        bundle.write(path, Path(root.name) / relative)
print(f"Packaged {output.name}")
