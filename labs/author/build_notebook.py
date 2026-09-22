"""Build the optional notebook and HTML reference from the editable lesson.

Run with the locked notebook and author dependency groups. Add ``--execute`` to
run every cell using the same Python interpreter as this utility.
"""

import argparse
import json
import os
import sys
import tempfile
from collections.abc import Iterator
from contextlib import contextmanager
from pathlib import Path

import nbformat
from nbclient import NotebookClient
from nbconvert import HTMLExporter
from nbformat import NotebookNode


def make_cell(kind: str, lines: list[str]) -> NotebookNode:
    """Convert one VS Code cell, removing Python comments from Markdown."""
    body = "\n".join(lines).strip()
    if kind == "code":
        return nbformat.v4.new_code_cell(body)
    markdown = "\n".join(
        line[2:] if line.startswith("# ") else line[1:] for line in body.splitlines()
    )
    return nbformat.v4.new_markdown_cell(markdown)


def lesson_cells(script: str) -> Iterator[NotebookNode]:
    """Yield marked lesson cells, ignoring any module preamble before the first marker."""
    kind = None
    lines = []
    for line in script.splitlines() + ["# %%"]:
        if line not in {"# %%", "# %% [markdown]"}:
            if kind is not None:
                lines.append(line)
            continue
        if kind is not None:
            yield make_cell(kind, lines)
        kind = "markdown" if "[markdown]" in line else "code"
        lines = []


def code_sources(notebook: NotebookNode) -> list[str]:
    """Return executable cell sources in teaching order for output invalidation."""
    return [cell.source for cell in notebook.cells if cell.cell_type == "code"]


def preserve_cell_state(previous: NotebookNode, current: NotebookNode) -> None:
    """Keep matching cell IDs; retain outputs only when all executable code is unchanged."""
    unchanged = code_sources(previous) == code_sources(current)
    for before, after in zip(previous.cells, current.cells):
        if before.cell_type != after.cell_type or before.source.strip() != after.source:
            continue
        after.id = before.id
        if unchanged and after.cell_type == "code":
            after.outputs = before.outputs
            after.execution_count = before.execution_count


def build_notebook(root: Path) -> NotebookNode:
    """Read the canonical lesson and preserve still-valid state from its previous notebook."""
    script = (root / "hands_on.py").read_text(encoding="utf-8")
    notebook = nbformat.v4.new_notebook(cells=list(lesson_cells(script)))
    notebook.metadata.kernelspec = {
        "display_name": "Python 3",
        "language": "python",
        "name": "python3",
    }
    previous_path = root / "hands-on.ipynb"
    if previous_path.exists():
        preserve_cell_state(nbformat.read(previous_path, as_version=4), notebook)
    return notebook


@contextmanager
def temporary_environment(settings: dict[str, str]) -> Iterator[None]:
    """Apply process settings for one operation and restore their original presence and values."""
    previous = {name: os.environ.get(name) for name in settings}
    os.environ.update(settings)
    try:
        yield
    finally:
        for name, value in previous.items():
            if value is None:
                os.environ.pop(name, None)
            else:
                os.environ[name] = value


@contextmanager
def notebook_kernel() -> Iterator[str]:
    """Provide an isolated kernel for this interpreter, restoring Jupyter settings on exit."""
    with tempfile.TemporaryDirectory(prefix="dcc-notebook-") as temporary:
        root = Path(temporary)
        kernel_name = "dcc-workshop"
        kernel = root / "kernels" / kernel_name
        kernel.mkdir(parents=True)
        specification = {
            "argv": [sys.executable, "-m", "ipykernel_launcher", "-f", "{connection_file}"],
            "display_name": "DCC workshop validation",
            "language": "python",
        }
        (kernel / "kernel.json").write_text(json.dumps(specification), encoding="utf-8")
        with temporary_environment(
            {
                "JUPYTER_PATH": str(root),
                "JUPYTER_RUNTIME_DIR": str(root / "runtime"),
            }
        ):
            yield kernel_name


def execute_notebook(notebook: NotebookNode, root: Path) -> None:
    """Execute every cell from the lab directory with a temporary, matching Python kernel."""
    with notebook_kernel() as kernel_name:
        client = NotebookClient(
            notebook,
            timeout=180,
            kernel_name=kernel_name,
            resources={"metadata": {"path": str(root)}},
        )
        client.execute()


def save_notebook(notebook: NotebookNode, root: Path) -> None:
    """Validate the notebook and write its notebook and HTML representations."""
    nbformat.validate(notebook)
    html, _ = HTMLExporter(template_name="lab").from_notebook_node(notebook)
    nbformat.write(notebook, root / "hands-on.ipynb")
    (root / "hands-on.html").write_text(html, encoding="utf-8")


def main() -> None:
    """Build the lab reference, executing it only when explicitly requested."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--execute", action="store_true")
    args = parser.parse_args()
    root = Path(__file__).resolve().parents[1]
    notebook = build_notebook(root)
    if args.execute:
        execute_notebook(notebook, root)
    save_notebook(notebook, root)
    print(f"Built {len(notebook.cells)} cells; executed: {args.execute}")


if __name__ == "__main__":
    main()
