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
from labs.author import lesson_source as lesson
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

    def test_marked_source_preserves_cell_boundaries(self) -> None:
        """Read inert starters without executing the worked reference."""
        script = '# %% [markdown] id=goal\n# café\n#\n# Goal\n# %% id=task role=task\nprint(1)\n# %% [starter] id=start replaces=task\n# todo("Try")\n'
        cells = lesson.lesson_cells(script)
        self.assertEqual(
            [(cell["kind"], cell["source"]) for cell in cells],
            [("markdown", "café\n\nGoal"), ("code", 'todo("Try")')],
        )
        self.assertEqual(lesson.lesson_cells(script, solved=True)[-1]["source"], "print(1)")

    def test_missing_starter_cannot_expose_a_solution(self) -> None:
        """A missing learner variant must fail closed, not publish the completed task."""
        with self.assertRaisesRegex(ValueError, "no starter"):
            lesson.lesson_cells('# %% id=answer role=task\nprint("answer")')

    def test_ambiguous_starters_are_rejected(self) -> None:
        """Two matching variants must not silently choose an arbitrary answer."""
        script = '# %% id=task role=task\nprint(1)\n# %% [starter] id=a replaces=task\n# todo("a")\n# %% [starter] id=b replaces=task\n# todo("b")'
        with self.assertRaisesRegex(ValueError, "ambiguous"):
            lesson.lesson_cells(script)

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
                nbformat.v4.new_code_cell("print(1)", id="first"),
                nbformat.v4.new_code_cell("print(2)", id="second"),
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
                nbformat.v4.new_code_cell("print(99)", id="first"),
                nbformat.v4.new_code_cell("print(2)", id="second"),
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

    def test_build_and_save_matches_verifier(self) -> None:
        """Generate a real learner notebook and HTML, with no saved answers or output."""
        source_root = ROOT / "labs"
        notebook = notebooks.build_notebook(source_root, "2")
        path = self.root / "notebooks/02-clean-keys.ipynb"
        notebooks.save_notebook(notebook, path, root=self.root)
        expected = lesson.exercise_cells((source_root / "author/hands_on.py").read_text(), "2")
        course.verify_exercise(path, expected, solved=False)
        preview = self.root / "previews/notebooks/02-clean-keys.html"
        self.assertIn("Clean the keys", preview.read_text())
        self.assertFalse(path.with_suffix(".html").exists())
        self.assertIn('href="../notebook.css"', preview.read_text())
        self.assertIn('href="../../README.md"', preview.read_text())
        self.assertIn('href="../solutions/02-clean-keys.html"', preview.read_text())
        ids = course.Markup(preview).ids
        self.assertEqual(len(ids), len(set(ids)))
        self.assertTrue(any("todo(" in cell.source for cell in notebook.cells))
        self.assertTrue(
            all(
                not cell.outputs and cell.execution_count is None
                for cell in notebook.cells
                if cell.cell_type == "code"
            )
        )

    def test_preview_navigation_handles_core_and_deeper_locations(self) -> None:
        """Moving HTML must preserve setup, next-exercise and worked-solution navigation."""
        cases = {
            "notebooks/02-clean-keys.ipynb": {
                "../README.md": "../../README.md",
                "../docs/RECOVERY.md#exercise-2": "../../docs/RECOVERY.md#exercise-2",
                "deeper/product-tags.ipynb": "deeper/product-tags.html",
                "../solutions/02-clean-keys.ipynb": "../solutions/02-clean-keys.html",
                "03-validate.ipynb?download=1#finish": "03-validate.html?download=1#finish",
                "#finish": "#finish",
                "https://example.com/other.ipynb": "https://example.com/other.ipynb",
            },
            "solutions/deeper/product-tags.ipynb": {
                "../../index.html": "../../../index.html",
                "../02-clean-keys.ipynb": "../02-clean-keys.html",
                "../../notebooks/deeper/product-tags.ipynb": "../../notebooks/deeper/product-tags.html",
                "../../lab_support/runtime.py": "../../../lab_support/runtime.py",
                "../../data/example%20file.png": "../../../data/example%20file.png",
            },
        }
        for filename, links in cases.items():
            for original, expected in links.items():
                with self.subTest(notebook=filename, link=original):
                    self.assertEqual(
                        notebooks.preview_url(original, self.root / filename, self.root),
                        expected,
                    )

    def test_preview_rewrites_urls_without_changing_code_or_link_labels(self) -> None:
        """Notebook extensions in visible prose or code must not become HTML filenames."""
        body = (
            '<a href="03-validate.ipynb?a=1&amp;b=2">03-validate.ipynb</a>'
            '<pre>print("03-validate.ipynb")</pre>'
            '<img src="../data/sample.png" alt="Input">'
        )
        actual = notebooks.preview_links(body, self.root / "notebooks/02.ipynb", self.root)
        self.assertEqual(
            actual,
            '<a href="03-validate.html?a=1&amp;b=2">03-validate.ipynb</a>'
            '<pre>print("03-validate.ipynb")</pre>'
            '<img src="../../data/sample.png" alt="Input">',
        )

    def test_support_changes_invalidate_results_but_learner_work_does_not(self) -> None:
        """Nested support code affects saved evidence; local participant work must not."""
        helper = self.root / "lab_support/nested/helper.py"
        helper.parent.mkdir(parents=True)
        helper.write_text("value = 1\n")
        original = notebooks.source_digest(self.root)
        learner = self.root / "learner_work/answers.py"
        learner.parent.mkdir()
        learner.write_text("participant_answer = 42\n")
        self.assertEqual(notebooks.source_digest(self.root), original)
        helper.write_text("value = 2\n")
        self.assertNotEqual(notebooks.source_digest(self.root), original)

    def test_verifier_rejects_saved_answers_and_outputs(self) -> None:
        """Participant answers and execution outputs must never enter a published starter."""
        source_root = ROOT / "labs"
        notebook = notebooks.build_notebook(source_root, "2")
        expected = lesson.exercise_cells((source_root / "author/hands_on.py").read_text(), "2")
        path = self.root / "test.ipynb"
        code = next(cell for cell in notebook.cells if cell.cell_type == "code")
        code.outputs = [nbformat.v4.new_output("stream", name="stdout", text="answer")]
        nbformat.write(notebook, path)
        with self.assertRaisesRegex(ValueError, "saved execution output"):
            course.verify_exercise(path, expected, solved=False)
        code.outputs = []
        code.source = "print('changed')"
        nbformat.write(notebook, path)
        with self.assertRaisesRegex(ValueError, "cells differ"):
            course.verify_exercise(path, expected, solved=False)
        with self.assertRaisesRegex(ValueError, "Lab needs"):
            course.verify_lab(self.root)

    def test_every_exercise_has_one_standalone_notebook(self) -> None:
        """Exercises lead the structure; optional depth does not duplicate a notebook."""
        script = (ROOT / "labs/author/hands_on.py").read_text()
        self.assertEqual(lesson.exercise_ids(core_only=True), [str(i) for i in range(8)])
        slugs = [spec.slug for spec in lesson.EXERCISES.values()]
        self.assertEqual(len(slugs), len(set(slugs)))
        for exercise in lesson.exercise_ids():
            cells = lesson.exercise_cells(script, exercise)
            identifiers = [cell["id"] for cell in cells]
            introduction = cells[0]["source"]
            self.assertEqual(cells[0]["kind"], "markdown")
            self.assertIn("## What you’ll learn\n\n- ", introduction)
            solved_intro = lesson.exercise_cells(script, exercise, solved=True)[0]["source"]
            outcomes = [line for line in introduction.splitlines() if line.startswith("- ")]
            self.assertTrue(all(line in solved_intro for line in outcomes))
            self.assertIn("notebook-setup", identifiers)
            self.assertIn("save-and-finish", identifiers)
            self.assertEqual(
                sum(identifier.startswith("exercise-") for identifier in identifiers),
                int(exercise.isdigit()),
            )
            self.assertNotIn("What we reused", "\n".join(cell["source"] for cell in cells))
            self.assertNotIn("route", "\n".join(cell["source"] for cell in cells).lower())

    def test_session_exercise_leaves_startup_to_the_learner(self) -> None:
        """Exercise zero must teach startup before later notebooks use the helper."""
        script = (ROOT / "labs/author/hands_on.py").read_text()
        cells = lesson.exercise_cells(script, "0")
        by_id = {cell["id"]: cell for cell in cells}
        setup = by_id["notebook-setup"]["source"]
        self.assertNotIn("create_spark", setup)
        self.assertNotIn("getOrCreate", setup)
        self.assertEqual(by_id["session-builder"]["role"], "starter")
        self.assertIn("spark = None", by_id["session-builder"]["source"])
        self.assertNotIn("setup-code", by_id)
        self.assertNotIn("zoom-heading", by_id)
        self.assertNotIn("#zoom", by_id["notebook-intro"]["source"])
        self.assertIn("spark.stop()", by_id["save-and-finish"]["source"])
        self.assertIn("01-inspect.ipynb", by_id["next-exercise"]["source"])
        solved = lesson.exercise_cells(script, "0", solved=True)
        builder = next(cell["source"] for cell in solved if cell["id"] == "session-builder")
        self.assertIn("SparkSession.builder", builder)
        self.assertIn("getOrCreate()", builder)

    def test_saved_session_output_labels_the_validation_interpreter(self) -> None:
        """Published diagnostics must not include the author's private interpreter path."""
        raw = f"Python: {sys.executable}\nInput: {self.root}/data"
        self.assertEqual(
            notebooks.portable_output_text(raw, self.root),
            "Python: <validation-python>\nInput: <lab-root>/data",
        )

    def test_notebook_bootstrap_finds_lab_from_project_or_notebook_folder(self) -> None:
        """Opening the repository rather than labs must not break a nested notebook."""
        lab = self.root / "labs"
        notebook_dir = lab / "notebooks/deeper"
        notebook_dir.mkdir(parents=True)
        (lab / "lab_support").mkdir()
        (lab / "lab_support/runtime.py").touch()
        bootstrap = lesson.setup_source("1", solved=False).split("from uuid import uuid4")[0]
        for directory in (self.root, lab, notebook_dir):
            with (
                patch("os.getcwd", return_value=str(directory)),
                patch.object(sys, "path", sys.path.copy()),
            ):
                namespace = {}
                exec(bootstrap, namespace)
                self.assertEqual(namespace["LAB_ROOT"], lab)

    def test_optional_tasks_share_the_core_without_changing_saved_answers(self) -> None:
        """A participant can skip or explore the zoom-in without switching workspaces."""
        script = (ROOT / "labs/author/hands_on.py").read_text()
        cells = lesson.exercise_cells(script, "3")
        by_id = {cell["id"]: cell for cell in cells}
        self.assertEqual(by_id["clean-sales"]["role"], "supplied")
        self.assertEqual(by_id["parsing-preview"]["role"], "starter")
        self.assertEqual(by_id["parsing-preview"]["depth"], "zoom")
        self.assertIn("todo(", by_id["parsing-preview"]["source"])
        self.assertNotIn("parsed_preview", by_id["save-and-finish"]["source"])
        self.assertIn("Workspace(solutions=False)", by_id["notebook-setup"]["source"])
        ids = [cell["id"] for cell in cells]
        self.assertLess(ids.index("check-validation"), ids.index("core-complete"))
        self.assertLess(ids.index("core-complete"), ids.index("parsing-preview"))
        solved = lesson.exercise_cells(script, "3", solved=True)
        self.assertIn(
            "Workspace(solutions=True)",
            next(cell["source"] for cell in solved if cell["id"] == "notebook-setup"),
        )

    def test_deeper_notebooks_need_only_their_topic_prerequisites(self) -> None:
        """Early investigations must not secretly require completion of the whole pipeline."""
        schemas = lesson.setup_source("schemas", solved=False)
        tags = lesson.setup_source("tags", solved=False)
        self.assertIn("clean_sales", schemas)
        self.assertNotIn("category_totals", schemas)
        self.assertNotIn("workspace.load", tags)
        self.assertEqual(
            lesson.relative_link("schemas", "README.md", solved=False), "../../README.md"
        )
        self.assertEqual(
            lesson.relative_link("3", "solutions/03-validate.ipynb", solved=False),
            "../solutions/03-validate.ipynb",
        )

    def test_taught_transformations_match_pipeline_module(self) -> None:
        """Keep the reference module and the functions learners see behaviourally aligned."""
        reference = ast.parse((ROOT / "labs/lab_support/pipeline.py").read_text())
        lesson = ast.parse((ROOT / "labs/author/hands_on.py").read_text())
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
            "author/hands_on.py",
            "lab_support/runtime.py",
            "docs/TROUBLESHOOTING.md",
            "notebooks/01-inspect.ipynb",
            "previews/notebooks/01-inspect.html",
            "previews/notebook.css",
            "data/part.parquet",
            ".vscode/settings.json",
            ".venv/bin/python",
            ".ruff_cache/local-entry",
            "runs/checkpoint/state",
            "learner_work/answers.py",
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
                    "labs/author/hands_on.py",
                    "labs/lab_support/runtime.py",
                    "labs/docs/TROUBLESHOOTING.md",
                    "labs/notebooks/01-inspect.ipynb",
                    "labs/previews/notebooks/01-inspect.html",
                    "labs/previews/notebook.css",
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
        source.parent.mkdir(exist_ok=True)
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
