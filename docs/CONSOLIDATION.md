# Local repository baseline

Consolidated on 21 September 2026 from the accepted Incan corpus trial and the
existing chapter 08 lab. The Git remote is
`https://github.com/dannyscodecorner/mastering-pyspark.git`.

## Chosen sources

- `slides/src/` is the canonical presentation source: 25 Incan modules.
- `slides/web/` contains the required browser resources and their available
  attribution, including fonts referenced indirectly by CSS.
- `labs/chapter08/` contains the existing 27-file lab project. Its lesson,
  notebooks, saved outputs, lockfile and prepared data were carried over unchanged.
- The original HTML deck, PowerPoints, earlier experiments and private planning
  files remain in the original archive, outside this repository.

Only two Incan modules needed relocation changes: document asset prefixes were
made relative to the built site root, and the renderer stopped routing resources
back into the archive. No slide content or animation logic was changed.

The build produces a complete `dist/` tree with the main deck, both references,
local presentation assets, lab references and a lab ZIP. Build output, native
compiler artifacts, environments and exercise runs are ignored by Git. The local
build records its input and output hashes under `.build/` so the normal verifier
can reject a stale build without freezing future content edits to this baseline.

## Verification performed

A fresh Incan 0.5.1 check and native build completed in this checkout using an
isolated local compiler/cache directory. The three native outputs were compared
with the preserved original HTML, allowing only formatting differences:

| Document | Slides | Matching markup events |
| --- | ---: | ---: |
| Main presentation | 123 | 18,874 |
| Core references | 56 | 7,144 |
| Join references | 5 | 1,346 |

All local HTML/SVG links and fragments, CSS resource references and notebook cells
passed the repository verifier. Resources resolve within `dist/`. Byte comparisons
also confirmed that the old source decks and copied lab files were unchanged.

Browser checks covered the new site’s chapter 08 agenda, all main-deck images,
loaded fonts, syntax highlighting, a four-step lesson through completion and
replay, and both reference decks. No browser warnings or errors were captured in
those checks. This is a representative relocation check, not a new visual audit
of every slide or a review of all Spark teaching claims.

The relocated lab’s locked setup check passed on macOS: a Python worker, prepared
Parquet reads/writes, file arrivals, aggregate state, checkpoint restart and a
streaming Parquet sink. The full lesson and notebook were not rerun as part of
consolidation; their code and previously validated outputs are unchanged.
Native Windows, WSL, Glue and distributed-cluster validation remain separate work.

## Next course work

Continue editing the notebook exercises and chapter 08 in this repository.
The current lesson is a guided worked reference; any future starter/solution
split should keep its exercise numbers and expected results aligned with the
slides. Chapter 09 remains the place to develop the AWS Glue deployment story.

The repository was prepared locally. GitHub publication and hosting configuration
are separate from this baseline.
