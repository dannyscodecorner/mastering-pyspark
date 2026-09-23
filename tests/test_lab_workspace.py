"""Protect participant-owned function handoffs, catch-up backups and checkpoint boundaries."""

import importlib.util
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from labs.lab_support import workspace as lab_workspace

ROOT = Path(__file__).resolve().parents[1]


class WorkspaceTests(unittest.TestCase):
    """Verify persistence independently of a notebook's surviving Python namespace."""

    def setUp(self) -> None:
        """Create an isolated lab root and two distinct learner-authored functions."""
        temporary = tempfile.TemporaryDirectory()
        self.addCleanup(temporary.cleanup)
        self.root = Path(temporary.name).resolve()
        patcher = patch.object(lab_workspace, "LAB_ROOT", self.root)
        patcher.start()
        self.addCleanup(patcher.stop)
        (self.root / "lab_support").mkdir()
        (self.root / "lab_support/pipeline.py").write_text(
            (ROOT / "labs/lab_support/pipeline.py").read_text()
        )
        path = self.root / "student.py"
        path.write_text(
            'def product_key(value):\n    """An observable student implementation."""\n    return value + "/student"\n\n'
            'def clean_products(value):\n    """Call the student helper, not the supplied reference."""\n    return product_key(value)\n'
        )
        specification = importlib.util.spec_from_file_location("student", path)
        self.student = importlib.util.module_from_spec(specification)
        specification.loader.exec_module(self.student)

    def test_next_notebook_uses_actual_saved_functions(self) -> None:
        """Reload in a new Workspace and keep the learner's helper dependency intact."""
        first = lab_workspace.Workspace()
        first.save(self.student.product_key, self.student.clean_products)
        second = lab_workspace.Workspace()
        (clean_products,) = second.load("clean_products")
        self.assertEqual(clean_products("b1"), "b1/student")
        self.assertIn('"/student"', second.answers.read_text())

    def test_reference_recovery_backs_up_instead_of_erasing_work(self) -> None:
        """An explicit catch-up choice preserves the prior saved source verbatim."""
        workspace = lab_workspace.Workspace()
        workspace.save(self.student.product_key, self.student.clean_products)
        original = workspace.answers.read_bytes()
        workspace.use_reference("keys")
        self.assertEqual(next(workspace.root.glob("answers-*.py")).read_bytes(), original)
        self.assertNotEqual(workspace.answers.read_bytes(), original)
        self.assertEqual((self.root / "student.py").read_text().count("/student"), 1)

    def test_solutions_cannot_replace_shared_participant_answers(self) -> None:
        """Only the solution edition has a separate answer module."""
        student = lab_workspace.Workspace()
        student.save(self.student.product_key)
        original = student.answers.read_bytes()
        lab_workspace.Workspace(solutions=True).use_reference("reporting")
        self.assertEqual(student.answers.read_bytes(), original)

    def test_missing_prerequisite_has_a_recovery_message(self) -> None:
        """A new notebook tells a learner which earlier handoff is missing."""
        with self.assertRaisesRegex(FileNotFoundError, "Exercise 2"):
            lab_workspace.Workspace().load("product_key")

    def test_resume_requires_same_functions_and_arrival_boundary(self) -> None:
        """Changing transformations cannot silently reuse an incompatible checkpoint."""
        workspace = lab_workspace.Workspace()
        workspace.save(self.student.product_key)
        run = self.root / "runs/example"
        (run / "incoming").mkdir(parents=True)
        workspace.remember_stream(run, "sales_example", 2)
        self.assertEqual(workspace.resume_stream(after=2), (run, "sales_example"))
        with self.assertRaisesRegex(ValueError, "not 3"):
            workspace.resume_stream(after=3)
        workspace.save(self.student.clean_products)
        with self.assertRaisesRegex(ValueError, "functions changed"):
            workspace.resume_stream(after=2)


if __name__ == "__main__":
    unittest.main()
