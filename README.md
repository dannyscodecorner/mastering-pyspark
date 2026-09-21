# Mastering PySpark

Danny’s Code Corner course on Spark and PySpark, with an interactive presentation
and a guided batch-to-streaming lab.

Course repository: [dannyscodecorner/mastering-pyspark](https://github.com/dannyscodecorner/mastering-pyspark).

## Start the hands-on lab

Open [labs/chapter08](labs/chapter08) in VS Code and follow its
[setup guide](labs/chapter08/README.md). The project uses Python 3.12, PySpark 4.2.0,
Java 21 and uv. Run these commands from that folder:

```text
uv sync --locked
uv run --locked check_setup.py
```

Then work through the nine numbered exercises in
[hands_on.py](labs/chapter08/hands_on.py), using the VS Code cells. The optional
[notebook](labs/chapter08/hands-on.ipynb) contains the same lesson. Both start Spark
locally; participants do not need Incan or Docker.

The lab guide records platform prerequisites and validation. Native Windows
still needs a representative-machine check with the matching Hadoop components.

## Build and view the presentation

The slides are authored in **Incan**. Use Python 3.10 or newer for the repository
tools and an installed Incan compiler. The consolidation baseline uses **Incan
0.5.1**; `INCAN_BINARY` can select a different compiler explicitly.

From the repository root:

```text
python3 tools/course.py build
python3 tools/course.py serve
```

Open the address printed by the server, normally <http://127.0.0.1:8766/>.
The server binds only to this machine. Stop it with Ctrl+C. On systems where
Python is named `python`, use that command instead of `python3`.

The build checks and compiles the Incan program, then runs its native executable
to generate the main presentation and both reference decks. Python packages
their existing browser assets and labs into `dist/`; it does not render the
slides. The built directory can be served on its own, including the downloadable
chapter 08 lab. Building does not publish anything to GitHub.

The initial corpus contains 123 main slides, 56 core-reference slides and five
join-reference slides. The historical core references retain their original
material; they are not an additional modernised chapter.

## Repository layout

```text
slides/src/          Incan slide content, components and HTML renderer
slides/web/          Styles, interaction controllers, fonts and artwork
labs/chapter08/      Locked uv project, lesson, notebook and prepared data
docs/                Authoring guidance, visual language and consolidation notes
tools/course.py      Build, verify and serve commands
dist/                Generated site and downloads (ignored by Git)
.build/              Local compiler state and build evidence (ignored by Git)
```

`slides/src/` is the presentation’s source of truth. Edit its chapter modules,
then rebuild. Do not edit `dist/` or continue editing the old archive’s HTML.
See [authoring guidance](docs/AUTHORING.md) for the source map and lab workflow.

## Verify changes

```text
python3 tools/course.py verify
```

Verification checks that the build matches the current source files, native
outputs reproduce the three documents, local HTML/SVG/CSS resources and fragments
resolve inside the site, and the notebook cells match the Python lesson. It does
not execute Spark or replace a visual review of changed slides.

For a lesson-code change, run its setup check and exercises using the lab’s
locked environment, regenerate the notebook and HTML reference, then rebuild
the course. Previous notebook outputs are not evidence for changed code.

## Presenting

- Arrow keys, Space and Page Up/Down move between slides.
- **O** opens the slide overview; **F** enters full screen; **B** blanks the screen.
- **N** shows notes on the presentation screen, visible to the audience.
- Diagram controls advance their own teaching steps. The bottom arrows leave
  the slide.
- Reduced-motion and static views retain a complete illustration.

Fonts and presentation assets are local. Attribution and bundled license notices
are listed in [THIRD_PARTY_NOTICES.md](THIRD_PARTY_NOTICES.md).
