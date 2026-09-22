"""Generate one learner and one solution notebook per exercise.

Run from labs with ``uv run --locked --group notebook --group author
-m author.build_notebook``. Add ``--execute`` to validate reference completions in
separate kernels. Learner notebooks always have empty outputs and unfinished tasks.
"""

import argparse
import copy
import hashlib
import html
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

from .lesson_source import EXERCISES, exercise_cells, exercise_ids


def code_sources(notebook: NotebookNode) -> list[str]:
    """Return executable cell sources in teaching order for output invalidation."""
    return [cell.source for cell in notebook.cells if cell.cell_type == "code"]


def preserve_cell_state(previous: NotebookNode, current: NotebookNode) -> None:
    """Retain matching outputs only when every executable cell is unchanged."""
    unchanged = code_sources(previous) == code_sources(current)
    previous_cells = {cell.id: cell for cell in previous.cells}
    for after in current.cells:
        before = previous_cells.get(after.id)
        if before is None or before.cell_type != after.cell_type or before.source != after.source:
            continue
        if unchanged and after.cell_type == "code":
            after.outputs = before.outputs
            after.execution_count = before.execution_count


def source_digest(root: Path) -> str:
    """Invalidate all saved solution results if a lesson or supporting implementation changes."""
    digest = hashlib.sha256()
    for path in [*sorted(root.glob("*.py")), *sorted((root / "author").glob("*.py"))]:
        digest.update(str(path.relative_to(root)).encode())
        digest.update(path.read_bytes())
    return digest.hexdigest()


def build_notebook(root: Path, exercise: str, *, solved: bool = False) -> NotebookNode:
    """Select one exercise's cells; never retain answers or outputs in a learner copy."""
    selected = exercise_cells(
        (root / "hands_on.py").read_text(encoding="utf-8"), exercise, solved=solved
    )
    cells = []
    for item in selected:
        factory = (
            nbformat.v4.new_code_cell if item["kind"] == "code" else nbformat.v4.new_markdown_cell
        )
        tags = [item["role"]] + (["optional"] if item["depth"] == "zoom" else [])
        cell = factory(item["source"], id=item["id"], metadata={"tags": tags})
        cells.append(cell)
    notebook = nbformat.v4.new_notebook(cells=cells)
    notebook.metadata.kernelspec = {
        "display_name": "Python 3.12 (.venv)",
        "language": "python",
        "name": "python3",
    }
    notebook.metadata.workshop = {
        "exercise": exercise,
        "solved": solved,
        "source_digest": source_digest(root),
    }
    path = notebook_path(root, exercise, solved=solved)
    if solved and path.exists():
        previous = nbformat.read(path, as_version=4)
        if (
            previous.metadata.get("workshop", {}).get("source_digest")
            == notebook.metadata.workshop.source_digest
        ):
            preserve_cell_state(previous, notebook)
            if "executed_depth" in previous.metadata.workshop:
                notebook.metadata.workshop.executed_depth = (
                    previous.metadata.workshop.executed_depth
                )
    return notebook


def notebook_path(root: Path, exercise: str, *, solved: bool) -> Path:
    """Use parallel directories for learner exercises and deliberately separate solutions."""
    folder = "solutions" if solved else "notebooks"
    return root / folder / f"{EXERCISES[exercise].slug}.ipynb"


@contextmanager
def temporary_environment(settings: dict[str, str]) -> Iterator[None]:
    """Apply process settings for one operation and restore their original values."""
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
    """Provide an isolated kernel for this interpreter without modifying user kernels."""
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
            {"JUPYTER_PATH": str(root), "JUPYTER_RUNTIME_DIR": str(root / "runtime")}
        ):
            yield kernel_name


def execute_notebook(notebook: NotebookNode, directory: Path, *, core_only: bool = False) -> None:
    """Validate a fresh kernel with all optional cells, or prove the core skips them safely."""
    execution = copy.deepcopy(notebook)
    if core_only:
        execution.cells = [
            cell for cell in execution.cells if "optional" not in cell.metadata.get("tags", [])
        ]
    with notebook_kernel() as kernel_name:
        NotebookClient(
            execution,
            timeout=180,
            kernel_name=kernel_name,
            resources={"metadata": {"path": str(directory)}},
        ).execute()
    completed = {cell.id: cell for cell in execution.cells if cell.cell_type == "code"}
    for cell in notebook.cells:
        if cell.cell_type == "code":
            cell.outputs, cell.execution_count = [], None
        if cell.id in completed:
            cell.outputs = completed[cell.id].outputs
            cell.execution_count = completed[cell.id].execution_count
    notebook.metadata.workshop.executed_depth = "core" if core_only else "all"


def portable_output_text(text: str, root: Path) -> str:
    """Label author-specific paths without changing the recorded computation results."""
    return text.replace(sys.executable, "<validation-python>").replace(str(root), "<lab-root>")


def normalise_output_paths(notebook: NotebookNode, root: Path) -> None:
    """Replace this machine's paths in saved output with explicit portable placeholders."""
    for cell in notebook.cells:
        for output in cell.get("outputs", []):
            if "text" in output:
                output.text = portable_output_text(output.text, root)
            if "text/plain" in output.get("data", {}):
                output.data["text/plain"] = portable_output_text(output.data["text/plain"], root)
    notebook.metadata.workshop.output_path_placeholder = (
        "<lab-root> replaces the local lab directory; "
        "<validation-python> replaces the interpreter path in saved outputs"
    )


def save_notebook(notebook: NotebookNode, path: Path) -> None:
    """Save a validated notebook and a lightweight, offline HTML preview."""
    root = next(parent for parent in path.parents if (parent / "hands_on.py").is_file())
    normalise_output_paths(notebook, root)
    nbformat.validate(notebook)
    path.parent.mkdir(parents=True, exist_ok=True)
    nbformat.write(notebook, path)
    exporter = HTMLExporter(
        template_name="basic", exclude_input_prompt=True, exclude_output_prompt=True
    )
    body, _ = exporter.from_notebook_node(notebook)
    # Preview navigation stays in HTML; the index offers explicit notebook downloads.
    body = body.replace(".ipynb", ".html")
    title = html.escape(EXERCISES[notebook.metadata.workshop.exercise].title)
    stylesheet = "../" * len(path.parent.relative_to(root).parts) + "notebook.css"
    page = f'<!doctype html><html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1"><title>{title}</title><link rel="stylesheet" href="{stylesheet}"></head><body><main>{body}</main></body></html>'
    # Spark's text plans can end lines with spaces; the HTML keeps their visible content.
    page = "\n".join(line.rstrip() for line in page.splitlines()) + "\n"
    path.with_suffix(".html").write_text(page, encoding="utf-8")


def save_index(root: Path) -> None:
    """Lead with exercises and reveal optional topic depth alongside each one."""
    sections = []
    for key, exercise in EXERCISES.items():
        if not key.isdigit():
            continue
        links = f'<a href="notebooks/{exercise.slug}.ipynb" download>Notebook</a> · <a href="notebooks/{exercise.slug}.html">Preview</a>'
        core, zoom = exercise.minutes
        deeper = [
            f'<li><a href="notebooks/{item.slug}.ipynb" download>{html.escape(item.title)}</a> · <a href="notebooks/{item.slug}.html">Preview</a></li>'
            for item in EXERCISES.values()
            if item.after == key and "/" in item.slug
        ]
        extra = (
            "<details><summary>Explore this topic further</summary><ul>"
            + "".join(deeper)
            + "</ul></details>"
            if deeper
            else ""
        )
        timing = f"Core: about {core} minutes."
        if zoom:
            timing += f" Optional zoom-in: about {zoom} more minutes, in the same notebook."
        sections.append(
            f'<section id="exercise-{key}"><h2>{key}. {html.escape(exercise.title)}</h2><p>{links}</p><p>{timing}</p>{extra}</section>'
        )
    body = '<h1>Working with PySpark</h1><p>Create a SparkSession, then build one sales pipeline from Parquet inputs to a restarted stream.</p><p><strong>Start with Exercise 0.</strong> Then work through Exercises 1–7, with optional zoom-ins inside each notebook. Choose more depth topic by topic; your saved work stays in one workspace.</p><p><strong>About 60 minutes:</strong> Exercises 0–7, with time for discussion and catch-up. <strong>About 90 minutes:</strong> add the optional zoom-ins. <strong>At your own pace:</strong> follow the deeper investigation links beside each exercise. These budgets still need a classroom rehearsal; installation is pre-work.</p><p><a href="README.md">Setup</a> · <a href="RECOVERY.md">Catch-up help</a> · <a href="API-REFERENCE.md">Small API reference</a></p>'
    body += "".join(sections)
    body += "<p>Completed answers are separate under <code>solutions/</code>. Each notebook links to its matching solution for comparison after your attempt.</p>"
    page = f'<!doctype html><html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1"><title>PySpark exercises</title><link rel="stylesheet" href="notebook.css"></head><body><main>{body}</main></body></html>'
    (root / "index.html").write_text(page, encoding="utf-8")


def build_exercise(root: Path, exercise: str, *, execute: bool, core_only: bool = False) -> None:
    """Write the learner and solution editions of a single exercise."""
    for solved in (False, True):
        notebook = build_notebook(root, exercise, solved=solved)
        path = notebook_path(root, exercise, solved=solved)
        path.parent.mkdir(parents=True, exist_ok=True)
        if solved and execute:
            print(
                f"Executing {path.relative_to(root)} in a fresh kernel ({'core only' if core_only else 'all sections'})",
                flush=True,
            )
            execute_notebook(notebook, path.parent, core_only=core_only)
        save_notebook(notebook, path)
    print(f"Built exercise {exercise}", flush=True)


def main() -> None:
    """Generate one tree; execute its baseline separately from optional investigations."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--execute", action="store_true")
    parser.add_argument(
        "--core-only",
        action="store_true",
        help="Validate exercises 0–7 while skipping optional zoom-ins",
    )
    args = parser.parse_args()
    root = Path(__file__).resolve().parents[1]
    for exercise in exercise_ids(core_only=args.core_only):
        build_exercise(root, exercise, execute=args.execute, core_only=args.core_only)
    save_index(root)


if __name__ == "__main__":
    main()
