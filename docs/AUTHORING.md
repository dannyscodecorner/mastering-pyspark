# Authoring the course

## Presentation sources

| Content | File in `slides/src/` |
| --- | --- |
| Welcome, biography and agenda | `opening.incn` |
| Chapters 01–09 | `chapter_01.incn` through `chapter_09.incn` |
| Closing | `closing.incn` |
| Core-abstraction references | `core_reference_*.incn` |
| Join references | `joins_reference_00.incn` |
| Document and chapter order | `documents.incn` |
| Slide, surface and teaching-step types | `surface.incn` |
| Shared teaching components | `components.incn` |
| HTML rendering | `html_target.incn` |

Each slide is a function returning a `Slide`. Chapters list those functions in
teaching order. `TeachingStep` values supply lesson labels and narration cues.
The existing styles and JavaScript controllers remain under `slides/web/`.
This is a course-specific surface model, not Pallay’s public API.

Make content changes in Incan, then run the build from the repository root.
Resource paths such as `assets/...` and `labs/...` refer to the generated site
root. Do not add dependencies on paths outside the repository. The build supplies
all shared resources alongside the rendered HTML.

Imported composed slides retain explicit footer numbers and chapter starting
pages. When adding or moving slides, update those values and review the resulting
overview and footer numbers. Keep stable slugs so earlier links keep working.

The normal verifier checks the current build rather than freezing the course to
its migration snapshot. For a deliberate preservation comparison, it also accepts:

```text
python3 tools/course.py verify --compare-original /path/to/preserved/html/deck
```

The supplied directory must contain the three original HTML documents. That
comparison is optional and should not be required after intentional content edits.

## Exercises and notebooks

The chapter 08 lesson is a guided worked reference with prompts and checks. It
uses the synthetic sales/products fixture and nine numbered exercises. The
last exercise adds a daily report. Chapter 09 is intended to reuse the pipeline
in AWS Glue and remains to be developed further.

Edit `labs/chapter08/hands_on.py`. Its `# %%` markers divide Markdown and code
cells for VS Code and the optional notebook. From the chapter 08 directory:

```text
uv run --locked --group notebook --group author author/build_notebook.py
```

That refreshes `hands-on.ipynb` and `hands-on.html`. It preserves outputs only
when the lesson’s code cells are unchanged. After changing code, execute the
reference as well:

```text
uv run --locked check_setup.py
uv run --locked --group notebook --group author author/build_notebook.py --execute
```

Review the resulting notebook and HTML. Keep transformations in `pipeline.py`
aligned with their teaching definitions. Do not claim runtime checks passed just
because the notebook’s saved output was preserved.

The course build copies the lab’s source, prepared data and generated references
into `dist/labs/` and creates the downloadable ZIP. Environments and run output
are excluded. A standalone lab ZIP can also be made with
`uv run --locked author/package_lab.py`; that local archive is ignored by Git.

## Compiler and publication boundaries

The baseline compiler is Incan 0.5.1. All local compiler/cache output goes under
this checkout’s ignored build directories. Do not share a Cargo target directory
with another checkout or copy a previous experiment’s native executable into it.

`dist/` is the deployable static site; `slides/src/` is the authored presentation.
Building or serving does not push commits, configure GitHub Pages or publish a
release. The original archive and earlier experiments remain external fallbacks.
