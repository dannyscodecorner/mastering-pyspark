# Mastering PySpark

Danny’s Code Corner course on Spark and PySpark, with an interactive presentation and a guided batch-to-streaming lab.

Course repository: [dannyscodecorner/mastering-pyspark](https://github.com/dannyscodecorner/mastering-pyspark).

## Start the hands-on lab

Open [labs](labs) in VS Code and follow its [setup guide](labs/README.md). The project uses Python 3.12, PySpark 4.2.0, Java 21 and uv. Run these commands from that folder:

```text
uv sync --locked --group notebook
uv run --locked check_setup.py
```

Open [Exercise 0](labs/notebooks/00-spark-session.ipynb) and select the lab’s `.venv` kernel. Each exercise has one notebook: complete the core for an approximately 60-minute lab, add optional zoom-ins for about 90 minutes, or explore the linked deeper investigations at your own pace. [The lab guide](labs/README.md) explains the flow. Completed solutions are separate; participants do not need Incan or Docker.

For optional Parquet inspection in VS Code, install [Parquet Explorer](https://marketplace.visualstudio.com/items?itemName=AdamViola.parquet-explorer). The [lab setup guide](labs/README.md#explore-parquet-files--optional) explains which files to open.

The [troubleshooting guide](labs/TROUBLESHOOTING.md) covers platform setup; the [instructor notes](labs/author/README.md#validation-performed) record validation. Native Windows still needs a representative-machine check with the matching Hadoop components.

## Build and view the presentation

The slides are authored in **Incan**. Use Python 3.10 or newer for the repository tools and an installed Incan compiler. The consolidation baseline uses **Incan 0.5.1**; `INCAN_BINARY` can select a different compiler explicitly.

From the repository root:

```text
python3 tools/course.py build
python3 tools/course.py serve
```

Open the address printed by the server, normally <http://127.0.0.1:8766/>.
The server binds only to this machine. Stop it with Ctrl+C. On systems where Python is named `python`, use that command instead of `python3`.

The build checks and compiles the Incan program, then runs its native executable to generate the main presentation and both reference decks. Python packages their existing browser assets and labs into `dist/`; it does not render the slides. The built directory can be served on its own, including the chapter 08 walkthrough. The lab download is a GitHub Release attachment. Building does not publish anything to GitHub.

The initial corpus contains 123 main slides, 56 core-reference slides and five join-reference slides. The historical core references retain their original material; they are not an additional modernised chapter.

## Repository layout

```text
slides/src/          Incan slide content, components and HTML renderer
slides/web/          Styles, interaction controllers, fonts and artwork
labs/               Locked uv project, lesson, notebook and prepared data
docs/                Authoring guidance, visual language and consolidation notes
tools/course.py      Build, verify and serve commands
dist/                Generated website (ignored by Git)
.build/              Local compiler state and build evidence (ignored by Git)
```

`slides/src/` is the presentation’s source of truth. Edit its chapter modules, then rebuild. Do not edit `dist/` or continue editing the old archive’s HTML.
See [authoring guidance](docs/AUTHORING.md) for the source map and lab workflow.

## Verify changes

```text
python3 tools/course.py verify
```

Verification checks that the build matches the current source files, native outputs reproduce the three documents, local HTML/SVG/CSS resources and fragments resolve inside the site, and every exercise notebook matches its authored exercise and learner copies contain no saved outputs. It does not execute Spark or replace a visual review of changed slides.

For a lesson-code change, run its setup check and exercises using the lab’s locked environment, regenerate the exercise notebooks and HTML previews, then rebuild the course. Previous notebook outputs are not evidence for changed code.

## Presenting

- Arrow keys, Space and Page Up/Down move between slides.
- **O** opens the slide overview; **F** enters full screen; **B** blanks the screen.
- **N** shows notes on the presentation screen, visible to the audience.
- Diagram controls advance their own teaching steps. The bottom arrows leave the slide.
- Reduced-motion and static views retain a complete illustration.

Fonts and presentation assets are local. Attribution and bundled license notices are listed in [THIRD_PARTY_NOTICES.md](THIRD_PARTY_NOTICES.md).
