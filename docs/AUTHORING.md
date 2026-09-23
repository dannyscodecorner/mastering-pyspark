# Authoring the course

For the course slides and learner starting points, see the [course README](../README.md). This guide covers local builds, content changes and verification; [publishing](PUBLISHING.md) covers GitHub Pages and lab releases.

## Build and preview

Use Python 3.10 or newer for the repository tools and an installed Incan compiler. The baseline is **Incan 0.5.1**; `INCAN_BINARY` can select a different compiler explicitly.

From the repository root:

```text
python3 tools/course.py build
python3 tools/course.py serve
```

Open the address printed by the server, normally <http://127.0.0.1:8766/>. The server binds only to this machine. Stop it with Ctrl+C. On systems where Python is named `python`, use that command instead of `python3`.

The build checks and compiles the Incan program, then runs its native executable to generate the main presentation and both reference decks. Python packages the browser assets and portable lab files into `dist/`; it does not render the slides. The built directory can be served on its own. The lab download is a GitHub Release attachment; building does not publish anything to GitHub.

The historical core-reference deck retains its original material; it is not an additional modernised chapter.

## Repository layout

```text
slides/src/          Incan slide content, components and HTML renderer
slides/web/          Styles, interaction controllers, fonts and artwork
labs/                Locked uv project, notebooks and prepared data
docs/                Authoring, publishing and course design guidance
tools/course.py      Build, verify and serve commands
dist/                Generated website (ignored by Git)
.build/              Local compiler state and build evidence (ignored by Git)
```

`slides/src/` is the presentation’s source of truth. Edit its chapter modules, then rebuild. Do not edit `dist/` or continue editing the old archive’s HTML.

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

## Verify changes

After building, run this from the repository root:

```text
python3 tools/course.py verify
```

Verification checks that the build matches the current source files, native outputs reproduce the three documents, local HTML/SVG/CSS resources and fragments resolve inside the site, and every exercise notebook matches its authored exercise. It also checks that learner notebooks contain no saved outputs. It does not execute Spark or replace a visual review of changed slides.

For a lesson-code change, run its setup check and exercises using the lab’s locked environment, regenerate the exercise notebooks and HTML previews, then rebuild the course. Previous notebook outputs are not evidence for changed code. The commands are in the next section.

## Exercises and notebooks

The [lab design](LAB-DESIGN.md) defines Exercise 0 on SparkSession creation followed by seven pipeline exercises with optional depth. Each exercise has its own notebook. Participant setup and exercise links are in [labs/README.md](../labs/README.md); provenance and validation records remain in the [instructor notes](../labs/author/README.md).

Edit `labs/author/hands_on.py`, the runnable worked source with annotated `# %%` teaching cells. Every task has one comment-only `[starter]`. Optional cells use `depth=zoom`; a larger investigation has its own exercise boundary. `labs/author/lesson_source.py` selects cells and supplies independent setup/finish steps. Learner functions are saved between notebooks, not assumed to survive in a shared kernel.

From **labs**, generate notebooks and previews:

```text
uv run --locked --group notebook --group author -m author.build_notebook
```

This refreshes `notebooks/`, `solutions/`, their `deeper/` subfolders, and the exercise index. Learner outputs are always empty. Changes to lesson/supporting Python invalidate saved solution output. For executable changes:

```text
uv run --locked check_setup.py
uv run --locked --group notebook --group author -m author.build_notebook --execute
```

Each solution notebook executes in a new kernel. First run with `--execute --core-only` to prove that all eight exercises work while skipping every optional section; then run `--execute` to validate all zoom-ins and separate investigations. Inspect the resulting notebook/HTML, including setup, task/hint separation and the stream restart across notebooks. Blank learner tasks are intentionally not executable end-to-end. Keep the reference transformations in `lab_support/pipeline.py` aligned with their taught definitions.

Runnable notebooks live under `labs/notebooks/` and `labs/solutions/`; their generated HTML mirrors live under `labs/previews/`. `labs/index.html` links to both formats. Shared Python helpers are in `labs/lab_support/`, participant reference guides in `labs/docs/`, and authoring tools and sources in `labs/author/`.

The course copies portable lab files into `dist/labs/`. `learner_work/`, run directories, environments and caches are excluded from publication and release ZIPs. Never regenerate a participant's edited notebooks. The slide download points to a GitHub Release attachment; [release preparation](PUBLISHING.md#publishing-the-lab) is separate from building Pages.

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
from `author/hands_on.py`, so format the Python lesson and regenerate its outputs rather
than formatting the notebook independently.

The focused tests cover notebook output invalidation, temporary kernel settings,
lab packaging, local links and publication guards. Publication tests mock Git;
they do not push to GitHub. For changes to the build or runtime helpers, also run
the course build/verifier and the relevant native or Spark checks.

## Compiler and publication boundaries

The baseline compiler is Incan 0.5.1. All local compiler/cache output goes under this checkout’s ignored build directories. Do not share a Cargo target directory with another checkout or copy a previous experiment’s native executable into it.

`dist/` is the deployable static site; `slides/src/` is the authored presentation. Building or serving does not push commits, configure GitHub Pages or publish a release. The original archive and earlier experiments remain external fallbacks.

## Presenting

- Arrow keys, Space and Page Up/Down move between slides.
- **O** opens the slide overview; **F** enters full screen; **B** blanks the screen.
- **N** shows notes on the presentation screen, visible to the audience.
- Diagram controls advance their own teaching steps. The bottom arrows leave the slide.
- Reduced-motion and static views retain a complete illustration.

Fonts and presentation assets are local. Attribution and bundled licence notices are listed in [THIRD_PARTY_NOTICES.md](../THIRD_PARTY_NOTICES.md).
