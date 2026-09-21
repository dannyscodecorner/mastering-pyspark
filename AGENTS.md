# Working on this course

- Author slide content in `slides/src/*.incn`. This is the chosen source of truth.
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
- `labs/chapter08/hands_on.py` is the canonical lesson source. Regenerate the
  optional notebook and HTML with its authoring helper. Keep exercise numbers
  aligned with `slides/src/chapter_08.incn`.
- The lab uses its own locked uv project. Do not change its Spark/Python/Java
  baseline as a side effect of presentation work. Validate runtime changes and
  distinguish observed results from untested platform assumptions.
- Do not include local environments, compiler output, checkpoint/run directories,
  credentials, the original PowerPoint archive or private planning material in
  commits or publication.
