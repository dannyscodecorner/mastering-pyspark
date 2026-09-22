# Authoring the course

## Presentation sources

| Content                                | Location in `slides/src/`                      |
| -------------------------------------- | --------------------------------------------- |
| Welcome, biography and agenda          | `chapters/opening/`                            |
| Chapters 01–09                         | `chapters/chapter_01/` through `chapters/chapter_09/` |
| Closing                                | `chapters/closing/`                            |
| Core-abstraction references            | `chapters/references/core/chapter_*/`          |
| Join references                        | `chapters/references/joins/`                   |
| Document and chapter order             | `documents.incn`                              |
| Slide, surface and teaching-step types | `surface.incn`                                |
| Shared teaching components             | `components.incn`                             |
| General text helpers and inline tests  | `helper.incn`                                 |
| HTML rendering                         | `html_target.incn`                            |

Each slide has its own named module containing a function returning a `Slide`. The chapter's `mod.incn` imports those functions and lists them in teaching order; file names do not determine the order. For example, edit `chapters/chapter_01/pyspark_code.incn` for the PySpark code slide, and `chapters/chapter_01/mod.incn` to change that chapter's sequence. `documents.incn` imports the chapter modules using paths such as `chapters.chapter_01`. Shared imports such as `surface`, `components` and `helper` stay at the source root.

`TeachingStep` values supply lesson labels and narration cues. The existing styles and JavaScript controllers remain under `slides/web/`. This is a course-specific surface model, not Pallay’s public API.

Make content changes in Incan, then run the build from the repository root. Resource paths such as `assets/...` and `labs/...` refer to the generated site root. Do not add dependencies on paths outside the repository. The build supplies all shared resources alongside the rendered HTML.

Imported composed slides retain explicit footer numbers and chapter starting pages. When adding or moving slides, update those values and review the resulting overview and footer numbers. Keep stable slugs so earlier links keep working.

The normal verifier checks the current build rather than freezing the course to its migration snapshot. For a deliberate preservation comparison, it also accepts:

```text
python3 tools/course.py verify --compare-original /path/to/preserved/html/deck
```

The supplied directory must contain the three original HTML documents. That comparison is optional and should not be required after intentional content edits.

## Exercises and notebooks

The agreed [lab design](LAB-DESIGN.md) defines the 60-minute, 90-minute and
detailed self-paced routes, shared milestones and the implementation sequence.
Those learner routes remain to be implemented; the files below currently contain
the worked reference.

The chapter 08 lesson is a guided worked reference with prompts and checks. It uses the synthetic sales/products fixture and nine numbered exercises. The last exercise adds a daily report. Chapter 09 is intended to reuse the pipeline in AWS Glue and remains to be developed further.

Participant setup is in [labs/README.md](../labs/README.md). The [instructor notes](../labs/author/README.md) retain the lesson sequence, fixture details, original-material references and validation record.

Edit `labs/hands_on.py`. Its `# %%` markers divide Markdown and code cells for VS Code and the optional notebook. From the `labs/` directory:

```text
uv run --locked --group notebook --group author author/build_notebook.py
```

That refreshes `hands-on.ipynb` and `hands-on.html`. It preserves outputs only when the lesson’s code cells are unchanged. After changing code, execute the reference as well:

```text
uv run --locked check_setup.py
uv run --locked --group notebook --group author author/build_notebook.py --execute
```

Review the resulting notebook and HTML. Keep transformations in `pipeline.py` aligned with their teaching definitions. Do not claim runtime checks passed just because the notebook’s saved output was preserved.

The course build copies the lab’s source, prepared data and generated references into `dist/labs/`. Environments and run output are excluded. It does not create a ZIP. The slide’s **Download the lab** link points to a GitHub Release attachment; see [Publishing the lab](PUBLISHING.md#publishing-the-lab).

## Python tooling

Use the repository's `ruff.toml` for Python formatting and checks. It enforces
grouped imports, docstrings, a maximum of three nested blocks and a cyclomatic
complexity limit of ten per function. Prefer guard clauses and functions with
clear responsibilities; document contracts and side effects rather than
restating each line of code.

Run these from the repository root:

```text
uvx --from ruff==0.16.8 ruff check .
uvx --from ruff==0.16.8 ruff format --check .
uv run --project labs --locked --group notebook --group author python -m unittest discover -s tests
```

For supported fixes, change `check .` to `check --fix .` in the first command;
to apply formatting, omit `--check` from the second command.
The nesting rule currently requires Ruff's lint preview; the commands above pin
the version used to check this repository. Notebook and HTML files are generated
from `hands_on.py`, so format the Python lesson and regenerate its outputs rather
than formatting the notebook independently.

The focused tests cover notebook output invalidation, temporary kernel settings,
lab packaging, local links and publication guards. Publication tests mock Git;
they do not push to GitHub. For changes to the build or runtime helpers, also run
the course build/verifier and the relevant native or Spark checks.

## Compiler and publication boundaries

The baseline compiler is Incan 0.5.1. All local compiler/cache output goes under this checkout’s ignored build directories. Do not share a Cargo target directory with another checkout or copy a previous experiment’s native executable into it.

`dist/` is the deployable static site; `slides/src/` is the authored presentation. Building or serving does not push commits, configure GitHub Pages or publish a release. The original archive and earlier experiments remain external fallbacks.
