# Working on this course

- For participant lab setup or exercise help, read [labs/AGENTS.md](labs/AGENTS.md) first. Help with installation; coach exercises with hints. Explicit course-authoring requests remain authoring work.
- Author slide content in `slides/src/chapters/`. Each chapter's `mod.incn` lists
  its slide modules in teaching order. This is the chosen source of truth.
  `dist/` is generated. Do not import the old HTML back over authored Incan edits.
- Keep the Incan renderer native. No new authored Rust is needed for this course.
  Python repository tools may package files and run checks; slide construction
  and rendering belong in Incan.
- Keep existing slide IDs and teaching sequences unless the user requests a
  narrative change. Settle the story before changing visuals or animation.
- Read `docs/STYLE-GUIDE.md` before visual changes. Preserve keyboard controls,
  presenter notes, code readability and complete static/reduced-motion states.
- Use `python3 tools/course.py build` and `python3 tools/course.py verify` after
  slide changes. Review affected slides in the browser, including relevant
  animation steps and reference links.
- `labs/author/hands_on.py` is the canonical lesson source. Regenerate the
  per-exercise learner and solution notebooks/HTML with `uv run --locked --group notebook --group author -m author.build_notebook` from labs. Participant work belongs in `learner_work/` and must never be published. Keep exercise numbers
  aligned with `slides/src/chapters/chapter_08/`.
- The lab uses its own locked uv project. Do not change its Spark/Python/Java
  baseline as a side effect of presentation work. Validate runtime changes and
  distinguish observed results from untested platform assumptions.
- Do not include local environments, compiler output, checkpoint/run directories,
  credentials, the original PowerPoint archive or private planning material in
  commits or publication.
