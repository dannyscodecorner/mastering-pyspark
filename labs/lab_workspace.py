"""Persist learner-written functions and stream progress between independent notebooks."""

import ast
import hashlib
import importlib.util
import inspect
import json
import textwrap
from collections.abc import Callable
from pathlib import Path
from types import ModuleType

LAB_ROOT = Path(__file__).resolve().parent
STAGES = {
    "keys": ("product_key", "clean_products"),
    "validation": ("clean_sales", "accepted_sales", "rejected_sales"),
    "reporting": ("enrich_sales", "category_totals"),
}
IMPORTS = "from pyspark.sql import Column, DataFrame\nfrom pyspark.sql import functions as F\n"


class Workspace:
    """Share learner answers across all exercises and keep worked solutions separate."""

    def __init__(self, *, solutions: bool = False) -> None:
        """Create a local answer folder; never write into the distributed notebooks."""
        self.root = LAB_ROOT / "learner_work"
        if solutions:
            self.root /= "solutions"
        self.root.mkdir(parents=True, exist_ok=True)
        self.answers = self.root / "answers.py"
        self.stream_state = self.root / "stream.json"

    def save(self, *functions: Callable) -> None:
        """Save the participant's actual function source for the next notebook.

        Exercise functions use F, Column, DataFrame and earlier saved functions.
        Extra notebook globals are not part of the handoff; pass values as arguments.
        """
        definitions = self._definitions()
        for function in functions:
            if not inspect.isfunction(function):
                raise TypeError("Save named Python functions from the exercise cells.")
            source = textwrap.dedent(inspect.getsource(function)).strip()
            node = ast.parse(source).body[0]
            if not isinstance(node, ast.FunctionDef):
                raise ValueError("The saved answer must be a function definition.")
            definitions[function.__name__] = source
        self._write_definitions(definitions)
        print("Saved your functions to", self.answers.relative_to(LAB_ROOT))

    def load(self, *names: str) -> tuple[Callable, ...]:
        """Load fresh definitions, with a useful error when an earlier exercise is missing."""
        if not self.answers.exists():
            raise FileNotFoundError(
                "No saved functions yet. Complete Exercise 2 and run its "
                "Save and finish cells, or use the explicit catch-up step in RECOVERY.md."
            )
        module = self._module()
        missing = [name for name in names if not hasattr(module, name)]
        if missing:
            raise ValueError(
                f"Missing saved functions: {', '.join(missing)}. Finish the earlier exercise "
                "and its Save cell, or choose the matching recovery step in RECOVERY.md."
            )
        return tuple(getattr(module, name) for name in names)

    def use_reference(self, through: str) -> None:
        """Explicitly replace a boundary with supplied functions, backing up prior answers."""
        if through not in STAGES:
            raise ValueError(f"Choose a catch-up boundary: {', '.join(STAGES)}")
        definitions = self._definitions()
        reference_source = (LAB_ROOT / "pipeline.py").read_text(encoding="utf-8")
        reference = {
            node.name: ast.get_source_segment(reference_source, node)
            for node in ast.parse(reference_source).body
            if isinstance(node, ast.FunctionDef)
        }
        if self.answers.exists():
            backup = self.root / (
                "answers-" + hashlib.sha256(self.answers.read_bytes()).hexdigest()[:12] + ".py"
            )
            if not backup.exists():
                backup.write_bytes(self.answers.read_bytes())
        for stage, names in STAGES.items():
            for name in names:
                definitions[name] = reference[name]
            if stage == through:
                break
        self._write_definitions(definitions)
        print(
            "Explicitly loaded reference code through",
            through,
            "— earlier saved answers are backed up.",
        )

    def remember_stream(self, run_root: Path, table_name: str, arrival: int) -> None:
        """Remember a verified arrival boundary for the next independent Spark session."""
        state = {
            "run": str(run_root.resolve().relative_to(LAB_ROOT.resolve())),
            "table": table_name,
            "arrival": arrival,
            "answers_sha256": hashlib.sha256(self.answers.read_bytes()).hexdigest(),
        }
        self.stream_state.write_text(json.dumps(state, indent=2) + "\n", encoding="utf-8")

    def resume_stream(self, *, after: int) -> tuple[Path, str]:
        """Use the existing input and checkpoint only with the same saved transformations."""
        if not self.stream_state.exists():
            raise FileNotFoundError(
                "Complete Exercise 6, including Save and finish, before opening Exercise 7."
            )
        state = json.loads(self.stream_state.read_text(encoding="utf-8"))
        if state["arrival"] != after:
            raise ValueError(
                f"The stream is saved after arrival {state['arrival']}, not {after}. "
                "To replay, rerun Exercise 6 from setup; it creates new input and checkpoints."
            )
        if hashlib.sha256(self.answers.read_bytes()).hexdigest() != state["answers_sha256"]:
            raise ValueError(
                "Your saved functions changed. Rerun Exercise 6 with fresh state before resuming."
            )
        run_root = (LAB_ROOT / state["run"]).resolve()
        if (
            not run_root.is_relative_to((LAB_ROOT / "runs").resolve())
            or not (run_root / "incoming").is_dir()
        ):
            raise ValueError("The saved stream input is unavailable. Replay Exercise 6 from setup.")
        return run_root, state["table"]

    def _definitions(self) -> dict[str, str]:
        """Read only existing function definitions from the saved answer module."""
        if not self.answers.exists():
            return {}
        source = self.answers.read_text(encoding="utf-8")
        return {
            node.name: ast.get_source_segment(source, node)
            for node in ast.parse(source).body
            if isinstance(node, ast.FunctionDef)
        }

    def _write_definitions(self, definitions: dict[str, str]) -> None:
        """Replace the current answer module after validating its syntax."""
        source = IMPORTS + "\n\n" + "\n\n\n".join(definitions.values()) + "\n"
        ast.parse(source)
        self.answers.write_text(source, encoding="utf-8")

    def _module(self) -> ModuleType:
        """Evaluate saved source without stale import or bytecode caches."""
        specification = importlib.util.spec_from_file_location("workshop_answers", self.answers)
        module = importlib.util.module_from_spec(specification)
        exec(
            compile(self.answers.read_text(encoding="utf-8"), str(self.answers), "exec"),
            module.__dict__,
        )
        return module
