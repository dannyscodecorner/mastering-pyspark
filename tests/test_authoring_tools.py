"""Regression checks for notebook state, site links and portable lab downloads."""

import ast
import json
import os
import runpy
import shutil
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch
from zipfile import ZipFile

import nbformat

from labs.author import build_notebook as notebooks
from labs.author import package_lab as packaging
from tools import course

ROOT = Path(__file__).resolve().parents[1]


class NotebookTests(unittest.TestCase):
    """Protect lesson boundaries and prevent stale outputs from surviving code changes."""

    def setUp(self) -> None:
        """Give each check an isolated lab directory."""
        temporary = tempfile.TemporaryDirectory()
        self.addCleanup(temporary.cleanup)
        self.root = Path(temporary.name)

    def test_author_and_verifier_agree_on_cell_boundaries(self) -> None:
        """Preserve blank cells, Markdown comments, Unicode and the final unclosed cell."""
        script = "\n".join(
            [
                '"""Module preamble."""',
                "",
                "# %% [markdown]",
                "# Heading",
                "#",
                "# café",
                "# %%",
                "",
                "# %%",
                'print("# %%")',
                "# %% [markdown]",
                "# Done",
            ]
        )
        expected = [
            ("markdown", "Heading\n\ncafé"),
            ("code", ""),
            ("code", 'print("# %%")'),
            ("markdown", "Done"),
        ]
        cells = list(notebooks.lesson_cells(script))
        self.assertEqual([(cell.cell_type, cell.source) for cell in cells], expected)
        self.assertEqual(list(course.script_cells(script)), expected)

    def previous_notebook(self) -> nbformat.NotebookNode:
        """Construct saved state with an observable output and stable cell identity."""
        return nbformat.v4.new_notebook(
            cells=[
                nbformat.v4.new_markdown_cell("Old prose"),
                nbformat.v4.new_code_cell(
                    "print(1)",
                    id="first",
                    execution_count=1,
                    outputs=[
                        nbformat.v4.new_output("stream", name="stdout", text="1\n"),
                    ],
                ),
                nbformat.v4.new_code_cell(
                    "print(2)",
                    id="second",
                    execution_count=2,
                    outputs=[
                        nbformat.v4.new_output("stream", name="stdout", text="2\n"),
                    ],
                ),
            ]
        )

    def test_markdown_edit_preserves_valid_outputs(self) -> None:
        """A prose-only edit must not discard results from unchanged executable cells."""
        previous = self.previous_notebook()
        current = nbformat.v4.new_notebook(
            cells=[
                nbformat.v4.new_markdown_cell("New prose"),
                nbformat.v4.new_code_cell("print(1)"),
                nbformat.v4.new_code_cell("print(2)"),
            ]
        )
        notebooks.preserve_cell_state(previous, current)
        self.assertEqual(current.cells[1].id, "first")
        self.assertEqual(current.cells[2].id, "second")
        self.assertEqual(current.cells[2].outputs, previous.cells[2].outputs)
        self.assertEqual(current.cells[2].execution_count, 2)

    def test_code_edit_invalidates_downstream_outputs(self) -> None:
        """Even unchanged later cells lose saved results when an earlier computation changes."""
        current = nbformat.v4.new_notebook(
            cells=[
                nbformat.v4.new_markdown_cell("Old prose"),
                nbformat.v4.new_code_cell("print(99)"),
                nbformat.v4.new_code_cell("print(2)"),
            ]
        )
        notebooks.preserve_cell_state(self.previous_notebook(), current)
        self.assertEqual(current.cells[2].id, "second")
        self.assertTrue(all(not cell.outputs for cell in current.cells[1:]))
        self.assertTrue(all(cell.execution_count is None for cell in current.cells[1:]))

    def test_kernel_restores_settings_after_failure(self) -> None:
        """A failed execution must remove its temporary kernel and restore the calling process."""
        with patch.dict(os.environ, {"JUPYTER_PATH": "original"}):
            os.environ.pop("JUPYTER_RUNTIME_DIR", None)
            with (
                self.assertRaisesRegex(RuntimeError, "execution failed"),
                notebooks.notebook_kernel() as name,
            ):
                kernel_root = Path(os.environ["JUPYTER_PATH"])
                specification = json.loads(
                    (kernel_root / "kernels" / name / "kernel.json").read_text()
                )
                self.assertEqual(specification["argv"][0], sys.executable)
                raise RuntimeError("execution failed")
            self.assertEqual(os.environ["JUPYTER_PATH"], "original")
            self.assertNotIn("JUPYTER_RUNTIME_DIR", os.environ)
            self.assertFalse(kernel_root.exists())

    def test_build_and_save_matches_independent_verifier(self) -> None:
        """Generate real notebook and HTML files from a small marked script."""
        (self.root / "hands_on.py").write_text("# %% [markdown]\n# Goal\n# %%\nprint(1)\n")
        notebook = notebooks.build_notebook(self.root)
        notebooks.save_notebook(notebook, self.root)
        course.verify_lab(self.root)
        self.assertIn("Goal", (self.root / "hands-on.html").read_text())

    def test_verifier_rejects_missing_or_outdated_notebook(self) -> None:
        """Fail explicitly when notebook generation has been omitted or fallen out of sync."""
        with self.assertRaisesRegex(ValueError, "Lab needs"):
            course.verify_lab(self.root)
        (self.root / "hands_on.py").write_text("# %%\nprint(1)\n")
        notebook = nbformat.v4.new_notebook(cells=[nbformat.v4.new_code_cell("print(2)")])
        nbformat.write(notebook, self.root / "hands-on.ipynb")
        with self.assertRaisesRegex(ValueError, "cells differ"):
            course.verify_lab(self.root)

    def test_taught_transformations_match_pipeline_module(self) -> None:
        """Keep the reference module and the functions learners see behaviourally aligned."""
        reference = ast.parse((ROOT / "labs/pipeline.py").read_text())
        lesson = ast.parse((ROOT / "labs/hands_on.py").read_text())
        taught = {node.name: node for node in lesson.body if isinstance(node, ast.FunctionDef)}
        for node in reference.body:
            if isinstance(node, ast.FunctionDef):
                self.assertEqual(ast.dump(node), ast.dump(taught[node.name]), node.name)


class PackagingTests(unittest.TestCase):
    """Exercise actual archive contents, exclusions and repeatable packaging."""

    def setUp(self) -> None:
        """Prepare a small lab with both distributable and machine-local files."""
        temporary = tempfile.TemporaryDirectory()
        self.addCleanup(temporary.cleanup)
        self.root = Path(temporary.name) / "labs"
        for name in (
            "hands_on.py",
            "data/part.parquet",
            ".vscode/settings.json",
            ".venv/bin/python",
            ".ruff_cache/local-entry",
            "runs/checkpoint/state",
            ".git/config",
            "__pycache__/module.pyc",
            ".env",
            ".env.private",
            "Thumbs.db",
            "data/.part.crc",
            "old.zip",
        ):
            path = self.root / name
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text(name)

    def test_release_archive_matches_site_sources_and_excludes_local_files(self) -> None:
        """The release and site must include the same portable lab files."""
        standalone = self.root.parent / "pyspark-labs.zip"
        packaging.package_lab(self.root, standalone)
        with ZipFile(standalone) as archive:
            self.assertEqual(
                set(archive.namelist()),
                {
                    "labs/hands_on.py",
                    "labs/data/part.parquet",
                    "labs/.vscode/settings.json",
                },
            )
            self.assertEqual(archive.read("labs/data/part.parquet"), b"data/part.parquet")
            site_sources = {
                path.relative_to(self.root.parent).as_posix(): path.read_bytes()
                for path in course.lab_files(self.root)
            }
            self.assertEqual(
                {name: archive.read(name) for name in archive.namelist()}, site_sources
            )
        first = standalone.read_bytes()
        packaging.package_lab(self.root, standalone)
        self.assertEqual(standalone.read_bytes(), first)

    def test_symlinks_cannot_pull_in_external_files(self) -> None:
        """Release packaging and site copying must reject included symlinks."""
        outside = self.root.parent / "outside.txt"
        outside.write_text("private")
        (self.root / "leak.txt").symlink_to(outside)
        with self.assertRaisesRegex(ValueError, "symlink"):
            packaging.package_lab(self.root, self.root.parent / "test.zip")
        with self.assertRaisesRegex(ValueError, "symlink"):
            list(course.lab_files(self.root))

    def test_only_explicit_command_creates_release_attachment(self) -> None:
        """Importing is inert; running the command writes outside the lab source tree."""
        source = self.root / "author/package_lab.py"
        source.parent.mkdir()
        shutil.copy2(Path(packaging.__file__), source)
        output = self.root.parent / ".build/releases/pyspark-labs.zip"
        runpy.run_path(str(source), run_name="imported_packager")
        self.assertFalse(output.exists())
        with patch("builtins.print"):
            runpy.run_path(str(source), run_name="__main__")
        self.assertTrue(output.is_file())
        self.assertFalse((self.root / "pyspark-labs.zip").exists())

    def test_site_build_copies_lab_without_zip(self) -> None:
        """Pages keeps the walkthrough and data while downloads are hosted on Releases."""
        web = self.root.parent / "slides/web"
        web.mkdir(parents=True)
        site = self.root.parent / "site"
        with (
            patch.object(course, "ROOT", self.root.parent),
            patch.object(course, "native_document", return_value=b"<html></html>"),
        ):
            course.populate_site(site)
        self.assertEqual((site / "labs/data/part.parquet").read_bytes(), b"data/part.parquet")
        self.assertFalse(list(site.rglob("*.zip")))
        self.assertFalse((site / "labs/.env").exists())


class SiteLinkTests(unittest.TestCase):
    """Check local link semantics without invoking browsers or external services."""

    def setUp(self) -> None:
        """Create a self-contained site with an encoded fragment and a CSS resource."""
        temporary = tempfile.TemporaryDirectory()
        self.addCleanup(temporary.cleanup)
        self.site = Path(temporary.name)
        (self.site / "index.html").write_text(
            '<a href="other.html#some%20id">Target</a>'
            '<a href="https://example.com">External</a><link href="style.css">'
        )
        (self.site / "other.html").write_text('<div id="some id">Target</div>')
        (self.site / "style.css").write_text(
            "a { background: url(image.png); marker-end: url(#arrow); }"
        )
        (self.site / "image.png").write_bytes(b"image fixture")

    def test_encoded_fragments_and_local_css_resources(self) -> None:
        """Accept encoded IDs and document-scoped CSS markers while checking image paths."""
        self.assertEqual(len(course.verify_links(self.site)), 2)

    def test_broken_resources_and_escapes_are_rejected(self) -> None:
        """Reject missing files, bad fragments and references outside the site root."""
        cases = {
            "missing.html": "missing resource",
            "other.html#absent": "missing fragment",
            "../outside.html": "resource escapes site",
            "%2e%2e/outside.html": "resource escapes site",
            "/other.html": "resource escapes site",
        }
        for url, message in cases.items():
            (self.site / "index.html").write_text(f'<a href="{url}">Broken</a>')
            with self.subTest(url=url), self.assertRaisesRegex(ValueError, message):
                course.verify_links(self.site)

    def test_duplicate_ids_are_rejected(self) -> None:
        """Prevent ambiguous fragments in a generated document."""
        (self.site / "other.html").write_text('<p id="same">One</p><p id="same">Two</p>')
        with self.assertRaisesRegex(ValueError, "duplicate IDs"):
            course.verify_links(self.site)


if __name__ == "__main__":
    unittest.main()
