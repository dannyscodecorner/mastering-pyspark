"""Build the optional notebook and preview from hands_on.py.

uv run --locked --group notebook --group author author/build_notebook.py --execute
"""

import argparse
import json
import os
from pathlib import Path
import sys
import tempfile

import nbformat
from nbconvert import HTMLExporter


def lesson_cells(script):
    kind = None
    lines = []
    for line in script.splitlines() + ["# %%"]:
        if line in {"# %%", "# %% [markdown]"}:
            if kind is not None:
                body = "\n".join(lines).strip()
                if kind == "markdown":
                    body = "\n".join(
                        part[2:] if part.startswith("# ") else part[1:]
                        for part in body.splitlines()
                    )
                    yield nbformat.v4.new_markdown_cell(body)
                else:
                    yield nbformat.v4.new_code_cell(body)
            kind = "markdown" if "[markdown]" in line else "code"
            lines = []
        elif kind is not None:
            lines.append(line)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--execute", action="store_true")
    args = parser.parse_args()
    root = Path(__file__).resolve().parents[1]
    notebook_path = root / "hands-on.ipynb"
    old = nbformat.read(notebook_path, as_version=4) if notebook_path.exists() else None
    nb = nbformat.v4.new_notebook(cells=list(lesson_cells((root / "hands_on.py").read_text())))
    nb.metadata.kernelspec = {"display_name": "Python 3", "language": "python", "name": "python3"}
    # Preserve cell identity and existing outputs only when all lesson code is unchanged.
    unchanged = old is not None and [c.source for c in old.cells if c.cell_type == "code"] == [c.source for c in nb.cells if c.cell_type == "code"]
    if old is not None:
        for before, after in zip(old.cells, nb.cells):
            if before.cell_type == after.cell_type and before.source.strip() == after.source:
                after.id = before.id
                if unchanged and after.cell_type == "code":
                    after.outputs = before.outputs
                    after.execution_count = before.execution_count
    if args.execute:
        from nbclient import NotebookClient

        with tempfile.TemporaryDirectory(prefix="dcc-notebook-") as temporary:
            kernel_root = Path(temporary)
            kernel = kernel_root / "kernels" / "dcc-workshop"
            kernel.mkdir(parents=True)
            (kernel / "kernel.json").write_text(json.dumps({
                "argv": [sys.executable, "-m", "ipykernel_launcher", "-f", "{connection_file}"],
                "display_name": "DCC workshop validation", "language": "python",
            }))
            os.environ["JUPYTER_PATH"] = str(kernel_root)
            os.environ["JUPYTER_RUNTIME_DIR"] = str(kernel_root / "runtime")
            NotebookClient(nb, timeout=180, kernel_name="dcc-workshop", resources={"metadata": {"path": str(root)}}).execute()
    nbformat.validate(nb)
    nbformat.write(nb, notebook_path)
    html, _ = HTMLExporter(template_name="lab").from_notebook_node(nb)
    (root / "hands-on.html").write_text(html)
    print(f"Built {len(nb.cells)} cells; executed: {args.execute}")


if __name__ == "__main__":
    main()
