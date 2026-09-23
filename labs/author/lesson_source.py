"""Select exercise-first learner and solution cells from one annotated lesson source.

This module uses only the standard library so the course verifier can use the
same selection rules without installing Spark or Jupyter.
"""

import posixpath
import re
from collections.abc import Iterator
from typing import NamedTuple

MARKER = re.compile(r"^# %%(?: \[(markdown|starter)\])?(.*)$")


class Unit(NamedTuple):
    """One authored teaching unit with a role and optional zoom-in depth."""

    kind: str
    source: str
    options: dict[str, str]


class Exercise(NamedTuple):
    """One notebook, its saved-code prerequisites and links to deeper investigations."""

    slug: str
    title: str
    functions: int
    after: str
    minutes: tuple[int, int] = (0, 0)


EXERCISES = {
    "0": Exercise("00-spark-session", "Create a SparkSession", 0, "", (5, 0)),
    "1": Exercise("01-inspect", "Inspect the inputs", 0, "", (5, 3)),
    "2": Exercise("02-clean-keys", "Clean the keys", 0, "1", (5, 5)),
    "3": Exercise("03-validate", "Validate the sales", 2, "2", (5, 6)),
    "4": Exercise("04-join-aggregate", "Join and aggregate", 5, "3", (10, 5)),
    "5": Exercise("05-save-report", "Inspect and save the report", 7, "4", (5, 4)),
    "6": Exercise("06-streaming", "Process arriving files", 7, "4", (10, 4)),
    "7": Exercise("07-checkpoint", "Resume from a checkpoint", 7, "6", (5, 3)),
    "schemas": Exercise("deeper/schemas-and-parsing", "Schemas and parsing", 5, "3"),
    "tags": Exercise("deeper/product-tags", "Reshaping product tags", 0, "2"),
    "joins": Exercise("deeper/join-investigations", "Investigating joins", 5, "4"),
    "daily": Exercise("deeper/daily-report", "A daily report", 7, "4"),
    "plans": Exercise("deeper/plans-and-cache", "Plans and repeated work", 7, "5"),
    "output": Exercise("deeper/streaming-output", "Persist streaming output", 7, "7"),
    "checkpoint": Exercise("deeper/fresh-checkpoint", "Compare with a fresh checkpoint", 7, "7"),
}
FUNCTION_NAMES = (
    "product_key",
    "clean_products",
    "clean_sales",
    "accepted_sales",
    "rejected_sales",
    "enrich_sales",
    "category_totals",
)


def decode_cell(kind: str, lines: list[str]) -> str:
    """Remove the comment prefix from Markdown and inert starter-code blocks."""
    body = "\n".join(lines).strip()
    if kind == "code":
        return body
    if any(line and not line.startswith("#") for line in body.splitlines()):
        raise ValueError(f"{kind} cells must contain only Python comments")
    return "\n".join(line[2:] if line.startswith("# ") else line[1:] for line in body.splitlines())


def lesson_units(script: str) -> Iterator[Unit]:
    """Read cell markers without executing any of the lesson's Python code."""
    current = None
    lines: list[str] = []
    for line in script.splitlines() + ["# %%"]:
        match = MARKER.fullmatch(line)
        if match is None:
            if current is not None:
                lines.append(line)
            continue
        if current is not None:
            kind, options = current
            yield Unit(kind, decode_cell(kind, lines), options)
        options = {}
        for token in match[2].split():
            key, separator, value = token.partition("=")
            if not separator or key in options:
                raise ValueError(f"Invalid cell metadata: {token}")
            options[key] = value
        current = (match[1] or "code", options)
        lines = []


def selected_starters(units: list[Unit]) -> dict[str, str]:
    """Require a single starter per task; missing or duplicate starters fail closed."""
    tasks = {unit.options.get("id") for unit in units if unit.options.get("role") == "task"}
    starters = {}
    for unit in units:
        if unit.kind != "starter":
            continue
        target = unit.options.get("replaces")
        if target not in tasks or target in starters:
            raise ValueError(f"Missing or ambiguous task for starter: {target}")
        starters[target] = unit.source
    if missing := tasks - starters.keys():
        raise ValueError(f"Tasks have no starter: {', '.join(sorted(missing))}")
    return starters


def lesson_cells(script: str, *, solved: bool = False) -> list[dict[str, str]]:
    """Choose starters or completed answers once, independently of a learner's time budget."""
    units = list(lesson_units(script))
    identifiers = [unit.options.get("id", f"cell-{i}") for i, unit in enumerate(units)]
    if len(set(identifiers)) != len(identifiers):
        raise ValueError("Duplicate lesson cell IDs")
    starters = selected_starters(units)
    cells = []
    for index, unit in enumerate(units):
        if unit.kind == "starter":
            continue
        identifier = unit.options.get("id", f"cell-{index}")
        role = unit.options.get("role", "reading" if unit.kind == "markdown" else "supplied")
        depth = unit.options.get("depth", "core")
        if depth not in {"core", "zoom"}:
            raise ValueError(f"Unknown depth for {identifier}: {depth}")
        if "routes" in unit.options or "supplied" in unit.options:
            raise ValueError("Exercises have one baseline and optional depth, not route variants")
        source = unit.source
        if role == "task" and not solved:
            source, role = starters[identifier], "starter"
        cells.append(notebook_cell(identifier, unit.kind, source, role, depth))
    return cells


def exercise_ids(*, core_only: bool = False) -> list[str]:
    """List the shared exercises, interleaving their optional investigations."""
    core = [key for key in EXERCISES if key.isdigit()]
    if core_only:
        return core
    return [
        key
        for exercise in core
        for key in [
            exercise,
            *[
                name
                for name, spec in EXERCISES.items()
                if not name.isdigit() and spec.after == exercise
            ],
        ]
    ]


def teaching_groups(cells: list[dict[str, str]]) -> dict[str, list[dict[str, str]]]:
    """Separate exercises and investigations using their authored boundaries."""
    result = {}
    current = None
    for cell in cells:
        identifier = cell["id"]
        if identifier.startswith("exercise-"):
            current = identifier.removeprefix("exercise-")
        elif identifier.startswith("extension-"):
            current = identifier.removeprefix("extension-")
        elif identifier in {"setup", "extensions", "cleanup"}:
            current = None
        if current is not None:
            result.setdefault(current, []).append(cell)
    return result


def notebook_cell(
    identifier: str, kind: str, source: str, role: str = "supplied", depth: str = "core"
) -> dict[str, str]:
    """Create a cell with stable identity, teaching role and execution depth."""
    return {"id": identifier, "kind": kind, "source": source, "role": role, "depth": depth}


def setup_source(exercise: str, *, solved: bool) -> str:
    """Start a session and load only the learner functions this exercise needs."""
    if exercise == "0":
        return "\n".join(
            [
                "import os",
                "import sys",
                "",
                "from pyspark.sql import SparkSession",
                "",
                'print("Notebook Python:", sys.executable)',
            ]
        )
    lines = [
        "import sys",
        "from pathlib import Path",
        "",
        "# Support opening the complete repository or its labs folder in VS Code.",
        "LAB_ROOT = next(",
        "    (candidate for parent in (Path.cwd(), *Path.cwd().parents)",
        "     for candidate in (parent, parent / 'labs')",
        "     if (candidate / 'lab_support/runtime.py').is_file()),",
        "    None,",
        ")",
        "if LAB_ROOT is None:",
        "    raise FileNotFoundError('Open the complete labs project in VS Code; a notebook alone is not enough.')",
        "if str(LAB_ROOT) not in sys.path:",
        "    sys.path.insert(0, str(LAB_ROOT))",
        "",
        "from uuid import uuid4",
        "",
        "from pyspark.sql import Column, DataFrame",
        "from pyspark.sql import functions as F",
        "",
        "from lab_support import checks as check",
        "from lab_support.arrival_files import publish_arrival",
        "from lab_support.checks import todo",
        "from lab_support.runtime import DATA_ROOT, create_spark, finish_query, new_run, spark_path",
        "from lab_support.workspace import Workspace",
        "",
        f"workspace = Workspace(solutions={solved})",
    ]
    count = EXERCISES[exercise].functions
    if count:
        names = FUNCTION_NAMES[:count]
        lines.append(
            f"{', '.join(names)} = workspace.load({', '.join(repr(name) for name in names)})"
        )
    stream_resume = exercise in {"7", "output", "checkpoint"}
    if stream_resume:
        after = 2 if exercise == "7" else 3
        lines.extend(
            [
                f"RUN_ROOT, TABLE_NAME = workspace.resume_stream(after={after})",
                'spark = create_spark(new_run("session"))',
                'INCOMING = RUN_ROOT / "incoming"',
            ]
        )
    else:
        lines.extend(["RUN_ROOT = new_run()", "spark = create_spark(RUN_ROOT)"])
    if exercise == "6":
        lines.extend(['INCOMING = RUN_ROOT / "incoming"', "INCOMING.mkdir()"])
    if exercise != "1":
        lines.extend(
            [
                'raw = spark.read.parquet(spark_path(DATA_ROOT / "sales.parquet"))',
                'raw_products = spark.read.parquet(spark_path(DATA_ROOT / "products.parquet"))',
            ]
        )
    if count >= 5:
        lines.extend(
            [
                "products = clean_products(raw_products)",
                "cleaned = clean_sales(raw)",
                "accepted = accepted_sales(cleaned)",
                "rejected = rejected_sales(cleaned)",
            ]
        )
    if count >= 7:
        lines.extend(
            ["enriched = enrich_sales(accepted, products)", "report = category_totals(enriched)"]
        )
    if stream_resume:
        lines.extend(
            [
                "stream_raw = spark.readStream.schema(raw.schema).parquet(spark_path(INCOMING))",
                "stream_enriched = enrich_sales(accepted_sales(clean_sales(stream_raw)), products)",
                "stream_report = category_totals(stream_enriched)",
                'CHECKPOINT_PATH = spark_path(RUN_ROOT / "report-checkpoint")',
            ]
        )
    if exercise == "7":
        lines.extend(
            [
                "writer = (",
                '    stream_report.writeStream.format("memory")',
                "    .queryName(TABLE_NAME)",
                '    .outputMode("complete")',
                '    .option("checkpointLocation", CHECKPOINT_PATH)',
                '    .trigger(processingTime="2 seconds")',
                ")",
            ]
        )
    lines.append('print(f"Spark {spark.version}; inputs: {DATA_ROOT.name}; notebook ready")')
    return "\n".join(lines)


def finish_source(exercise: str) -> str:
    """Save core outputs and stop this session without depending on optional work."""
    if exercise == "0":
        return 'spark.stop()\nprint("Spark stopped; the notebook Python kernel is still running.")'
    save = {
        "2": "workspace.save(product_key, clean_products)\n",
        "3": "workspace.save(clean_sales, accepted_sales, rejected_sales)\n",
        "4": "workspace.save(enrich_sales, category_totals)\n",
        "6": "check.arrival(spark.table(TABLE_NAME), 2)\nquery.stop()\nworkspace.remember_stream(RUN_ROOT, TABLE_NAME, 2)\n",
        "7": "workspace.remember_stream(RUN_ROOT, TABLE_NAME, 3)\n",
    }.get(exercise, "")
    return save + "\n".join(
        [
            "for active_query in spark.streams.active:",
            "    active_query.stop()",
            "spark.stop()",
            'print("Session stopped; exercise files are under", RUN_ROOT.relative_to(LAB_ROOT))',
        ]
    )


def relative_link(exercise: str, destination: str, *, solved: bool) -> str:
    """Resolve a lab-relative destination from this notebook's location."""
    folder = "solutions" if solved else "notebooks"
    parent = posixpath.dirname(f"{folder}/{EXERCISES[exercise].slug}.ipynb")
    return posixpath.relpath(destination, parent)


def rewrite_links(source: str, exercise: str, *, solved: bool) -> str:
    """Point local help, solutions and topic links at one exercise-based tree."""
    folder = "solutions" if solved else "notebooks"
    for filename in (
        "README.md",
        "docs/RECOVERY.md",
        "docs/API-REFERENCE.md",
        "lab_support/runtime.py",
    ):
        source = source.replace(
            f"({filename}", f"({relative_link(exercise, filename, solved=solved)}"
        )
    source = source.replace("(#cleanup)", "(#finish)")
    for key, target in EXERCISES.items():
        if key == exercise:
            continue
        anchor = f"exercise-{key}" if key.isdigit() else f"extension-{key}"
        destination = relative_link(exercise, f"{folder}/{target.slug}.ipynb", solved=solved)
        source = source.replace(f"(#{anchor})", f"({destination})")
    solution = relative_link(exercise, f"solutions/{EXERCISES[exercise].slug}.ipynb", solved=solved)
    return re.sub(r"\(\{\{solution\}\}\.ipynb(?:#[^)]+)?\)", f"({solution})", source)


def introduction(exercise: str, learning: str, *, solved: bool) -> dict[str, str]:
    """Make the goal and optional depth visible before the setup code."""
    spec = EXERCISES[exercise]
    edition = "Worked solution" if solved else "Learner exercise"
    title = (
        f"Exercise {exercise} — {spec.title}"
        if exercise.isdigit()
        else f"Deeper investigation — {spec.title}"
    )
    source = f"# {title}\n\n**{edition}** · [All exercises]({relative_link(exercise, 'index.html', solved=solved)}) · [Setup](README.md)\n\n"
    source += learning + "\n\n"
    if exercise.isdigit():
        source += f"**Core: about {spec.minutes[0]} minutes.** The same baseline for everyone."
        if spec.minutes[1]:
            source += f" [Optional zoom-in](#zoom): about {spec.minutes[1]} extra minutes; choose it here if the topic interests you."
        source += "\n\n"
    else:
        prerequisite = EXERCISES[spec.after]
        link = relative_link(
            exercise,
            f"{('solutions' if solved else 'notebooks')}/{prerequisite.slug}.ipynb",
            solved=solved,
        )
        source += f"Optional. Complete [Exercise {spec.after}]({link}) and its **Save and finish** cell first. This investigation uses the same saved work; it does not replace your core pipeline.\n\n"
    if exercise == "0":
        if solved:
            source += "Saved output labels the author's interpreter path as `<validation-python>`; running the cell yourself prints your actual path. "
        else:
            source += "Replace `None` in **Your code** with your builder expression. "
        source += "Run cells in order and end with **Finish — stop Spark**. This exercise does not save pipeline functions."
    else:
        if solved:
            source += "Completed answers use a separate solution workspace and do not replace participant work.\n\n"
        else:
            source += "Complete **Your code**, run the **Check** cells, and open hints when needed. Replace `todo(...)` with your answer. Do not use **Run All** while tasks remain unfinished.\n\n"
        source += "Run the supplied setup first. End with **Save and finish**; the next notebook loads your saved functions, so this kernel can be closed."
    return notebook_cell("notebook-intro", "markdown", source, "reading")


def zoom_cells(exercise: str, cells: list[dict[str, str]]) -> list[dict[str, str]]:
    """Put optional investigations after a clear, working core completion boundary."""
    minutes = EXERCISES[exercise].minutes[1]
    boundary = notebook_cell(
        "core-complete",
        "markdown",
        "## Core complete\n\nFor the 60-minute lab, [skip to Save and finish](#finish). To explore this topic further, continue with the optional section below. Later core exercises do not need any of its variables.",
        "reading",
    )
    heading = notebook_cell(
        "zoom-heading",
        "markdown",
        f'<a id="zoom"></a>\n## Optional zoom-in · about {minutes} minutes\n\nThese investigations make up the extra depth in a 90-minute session. Choose them independently; keep your working pipeline unchanged.',
        "reading",
        "zoom",
    )
    return [boundary, heading, *cells]


def next_steps(exercise: str, *, solved: bool) -> dict[str, str]:
    """Offer relevant deeper notebooks at each exercise without requiring a route switch."""
    folder = "solutions" if solved else "notebooks"
    parts = []
    if exercise.isdigit() and int(exercise) < 7:
        key = str(int(exercise) + 1)
        link = relative_link(exercise, f"{folder}/{EXERCISES[key].slug}.ipynb", solved=solved)
        parts.append(f"Next: [Exercise {key} — {EXERCISES[key].title}]({link}).")
    else:
        parts.append(
            f"Return to [all exercises]({relative_link(exercise, 'index.html', solved=solved)})."
        )
    deeper = [
        f"[{spec.title}]({relative_link(exercise, f'{folder}/{spec.slug}.ipynb', solved=solved)})"
        for spec in EXERCISES.values()
        if spec.after == exercise and "/" in spec.slug
    ]
    if deeper:
        parts.append(
            "Want more on this topic? You can open these now, using the same saved work: "
            + " · ".join(deeper)
            + "."
        )
    if not solved:
        parts.append(
            "After your attempt, compare the separate [worked solution]({{solution}}.ipynb)."
        )
    return notebook_cell("next-exercise", "markdown", "\n\n".join(parts), "reading")


def exercise_cells(script: str, exercise: str, *, solved: bool = False) -> list[dict[str, str]]:
    """Build a single exercise with baseline tasks and independent optional depth."""
    if exercise not in EXERCISES:
        raise ValueError(f"Unknown exercise: {exercise}")
    body = teaching_groups(lesson_cells(script, solved=solved))[exercise]
    learning = [cell for cell in body if cell["role"] == "learning"]
    if len(learning) != 1 or learning[0]["kind"] != "markdown":
        raise ValueError(f"Exercise {exercise} needs one Markdown learning summary")
    body = [cell for cell in body if cell["role"] != "learning"]
    # The notebook introduction already supplies the exercise title.
    body[0] = dict(
        body[0],
        source=re.sub(r"^## .+$", "## Your task", body[0]["source"], count=1, flags=re.MULTILINE),
    )
    if exercise == "7":
        body = [
            dict(cell, source="query = writer.start()") if cell["id"] == "restart-query" else cell
            for cell in body
        ]
    core = [cell for cell in body if cell["depth"] == "core"]
    optional = [cell for cell in body if cell["depth"] == "zoom"]
    if exercise.isdigit() and optional:
        core.extend(zoom_cells(exercise, optional))
    elif optional:
        raise ValueError("A separate investigation should not contain a second depth selector")
    setup_heading = "## Setup — supplied\n\nSelect the lab's `.venv` kernel. Stop Spark in the previous notebook before closing it. This uses the `create_spark` helper explained in [Exercise 0](#exercise-0). Missing earlier work? Use an explicit [catch-up step](docs/RECOVERY.md)."
    finish_heading = '<a id="finish"></a>\n## Save and finish\n\nRun once the core checks pass, whether or not you did the optional section. This saves your functions or stream handoff, then stops this notebook’s queries and Spark. Your work remains in `learner_work/`.'
    if exercise == "0":
        setup_heading = "## Setup — check the Python kernel\n\nComplete the [installation and setup check](README.md#2-create-the-virtual-environment) first. Select the lab's `.venv` kernel, then run this cell. On Windows the printed path should end in `labs\\.venv\\Scripts\\python.exe`; on macOS/Linux, `labs/.venv/bin/python`. If it points at uv's base Python instead, use [kernel selection help](README.md#4-open-exercise-0-and-select-the-kernel). Importing `SparkSession` makes the class available; this cell does not start Spark."
        finish_heading = '<a id="finish"></a>\n## Finish — stop Spark\n\nRun the cell below after the checks. In this local lab, `spark.stop()` stops the underlying SparkContext and releases its resources. The Python kernel keeps running, but the stopped session and its DataFrames cannot run more work. To repeat this exercise, run the builder and following cells again. [SparkSession.stop documentation](https://spark.apache.org/docs/4.2.0/api/python/reference/pyspark.sql/api/pyspark.sql.SparkSession.stop.html).'
    cells = [
        introduction(exercise, learning[0]["source"], solved=solved),
        notebook_cell(
            "setup-heading",
            "markdown",
            setup_heading,
        ),
        notebook_cell("notebook-setup", "code", setup_source(exercise, solved=solved)),
        *core,
        notebook_cell(
            "finish-heading",
            "markdown",
            finish_heading,
        ),
        notebook_cell("save-and-finish", "code", finish_source(exercise)),
        next_steps(exercise, solved=solved),
    ]
    return [
        dict(cell, source=rewrite_links(cell["source"], exercise, solved=solved)) for cell in cells
    ]
