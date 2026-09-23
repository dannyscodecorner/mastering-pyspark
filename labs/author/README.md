# Lab instructor notes

[Participant setup](../README.md) · [Setup troubleshooting](../docs/TROUBLESHOOTING.md)

Run the commands below from the **labs** folder.

## Exercise sequence

### Instructor fallback laptop

Danny will bring an additional MacBook for an attendee who encounters setup problems. Prepare that Mac with this same project and JDK 21 before the session: run `uv sync --locked --group notebook`, `uv run --locked check_setup.py`, and validate the eight core solution notebooks as described below. Select the project kernel in VS Code beforehand. Leave the project ready at the first exercise; each run creates its own output directory.

Ask attendees to run the setup check before class. The spare Mac is the classroom contingency, not evidence that native Windows has been validated.

### Lesson sequence

The chapter opens with an agenda and setup walkthrough. Everyone starts at `notebooks/00-spark-session.ipynb`. The core is the 60-minute baseline; optional sections add the 90-minute depth. Larger investigations are linked by topic under `notebooks/deeper/`. Every exercise is a separate notebook, with task cells, collapsed hints, checks and a final save/cleanup cell. Completed answers live under `solutions/`, never in the learner task cells.

0. **Create a SparkSession:** distinguish the kernel from the session, configure local execution, run a tiny DataFrame, observe session reuse and stop Spark. Explain the later setup helper.
1. **Inspect the inputs:** read Parquet and investigate schemas and values.
2. **Clean the keys:** build a reusable Column-expression helper and normalise the lookup.
3. **Validate the sales:** parse types, retain rejects and reconcile all eight inputs.
4. **Join and aggregate:** preserve the sale population and build the category report.
5. **Inspect and save:** inspect the plan (optional zoom-in), write and verify the report and rejects.
6. **Process arriving files:** reuse the participant's functions and introduce files 01/02.
7. **Resume from a checkpoint:** open a new notebook/kernel, restore the same stream configuration, and introduce file 03.

Core exercises supply wrappers, parsing and some operational steps; participants write key expressions, filtering, joins/grouping and the streaming reader/start. Optional sections investigate expressions, parsing, join behaviour, plans, query progress and checkpoints. Participants may choose any zoom-in independently. Separate investigations have explicit prerequisites and never become dependencies of later core exercises. See the [design and timing budgets](../../docs/LAB-DESIGN.md); classroom rehearsal is still needed.

### Cross-notebook handoffs

Each notebook owns its SparkSession. Exercise 2 saves the participant's key/lookup functions, Exercise 3 saves validation/filter functions, and Exercise 4 saves reporting functions. `Workspace.save` captures their actual source into `learner_work/answers.py`; later notebooks reload that module and rebuild the small batch context. Functions use `F`, arguments and earlier saved helpers, not unrelated globals from a previous notebook. The normal learner flow never imports reference transformations.

Exercise 6 stops its query and saves its input directory, checkpoint, table name and a hash of the saved functions. Exercise 7 starts in another kernel and resumes that state; changing saved transformations requires replaying Exercise 6 with fresh state. Solution runs use the separate `learner_work/solutions/` folder. Learner work, checkpoints and local runs are excluded from Git, Pages and ZIPs.

[Recovery](../docs/RECOVERY.md) offers explicit supplied-code boundaries with backups; it never silently replaces an unfinished answer. Participant agents should not choose a reference recovery on the learner's behalf.

## Local runtime

Exercise 0 uses `SparkSession.builder` directly. From Exercise 1 onward, the setup helper creates `spark` in local mode with two worker threads, UTC timestamps and two shuffle partitions for this tiny fixture. It selects the same Python executable for Spark workers as for the driver. It does not connect to a cluster. The final lesson cell stops the session; script exit also cleans up.

Every pipeline run creates a fresh directory under `runs/`; prepared inputs and earlier runs are never overwritten. The arrival helper stages completed files, then publishes each through a hard link. Use a local filesystem supporting hard links. Spark paths use absolute paths with forward slashes, preserving spaces and Windows drive letters without URL-encoding them.

`lab_support/pipeline.py` contains only transformations. Chapter 09 will reuse it in AWS Glue with separately configured storage, identity, runtime and monitoring. The local file publisher and session helper are workshop scaffolding, not deployment code.

## Data and checkpoints

The synthetic fixture extends the five sales used earlier in the course.

| Input | Meaning |
|---|---|
| `data/sales.parquet` | Eight raw sales, with strings for amount and timestamp |
| `data/products.parquet` | Three lookup rows with inconsistent category casing |
| `data/arrivals/01` | s1 and s2 |
| `data/arrivals/02` | s3, s4 and rejected s6 |
| `data/arrivals/03` | s5 and rejected s7/s8 |

Expected reconciliation: **8 input = 5 accepted + 3 rejected**. Category totals: books 50.00, games 40.00, unmapped 10.00. Streaming totals progress through 65.00, 90.00 and 100.00 after each file has been consumed. These are file arrivals, not a guarantee of one file per micro-batch.

The lesson uses a fresh run directory and refuses to overwrite existing input or batch output. To resume the restart exercise, retain the same input, query, static lookup and checkpoint. To replay the whole lab, stop active queries and run setup again to create a new directory. Do not edit files already consumed.

The category report uses a Complete-mode memory sink for classroom inspection. The checkpoint restart was verified, but the memory sink is not durable external output. The separate Append-mode Parquet query writes accepted sales rows before aggregation. Rejected rows are stored by the batch exercise; routing streaming rejects to a second audit destination is a possible extension.

If an experimental edit raises an error while a query is running, stop it with `query.stop()` before restarting setup. Every exercise ends with its own cleanup. Optional query notebooks clean up only queries they created; a skipped extension is never a core dependency.

## Original material reused

Reviewed the original PowerPoints and the corresponding public notebooks at revision `8cbb218a87052cd1a37cbe4a7862e772c15e5e44`:

- [3.2: fixing data](https://github.com/PacktPublishing/Mastering-Big-Data-Analytics-with-PySpark/blob/8cbb218a87052cd1a37cbe4a7862e772c15e5e44/Section%203%20-%20Preparing%20Data%20using%20SparkSQL/3.2/hands-on-3.2.ipynb): built-in functions, timestamp conversion and column transformations.
- [3.3: further preparation](https://github.com/PacktPublishing/Mastering-Big-Data-Analytics-with-PySpark/blob/8cbb218a87052cd1a37cbe4a7862e772c15e5e44/Section%203%20-%20Preparing%20Data%20using%20SparkSQL/3.3/hands-on-3.3.ipynb): exploration and inspecting transformed data. Its split/explode progression is used in the optional product-tags notebook.
- [8.3: managing and converting streams](https://github.com/PacktPublishing/Mastering-Big-Data-Analytics-with-PySpark/blob/8cbb218a87052cd1a37cbe4a7862e772c15e5e44/Section%208%20-%20Machine%20Learning%20in%20Real-Time/8.3/structured_streaming.ipynb): static versus streaming readers, shared transformations, writer/query distinction, query activity, progress, memory-table inspection and stopping.

The original files were preserved. Twitter acquisition, credentials and sentiment analysis are excluded. Prepared Parquet inputs replace the Twitter JSON. The exercise adds explicit rejected-record handling, repeatable arrivals, expected results and checkpoint/output checks. It removes the unconditional single-file coalesce, legacy one-time trigger and notebook display polling loop.

`lab_support/pipeline.py` contains only transformations and is the handoff to chapter 09. `author/prepare_inputs.py` is an author-only fixture generator; students do not need its DataFrame-construction syntax. `lab_support/arrival_files.py` is exercise scaffolding.

## Validation performed

After reorganising the lab on **23 September 2026**, all **15 worked notebooks** completed with every optional section on macOS. A freshly packaged and extracted lab, in a directory containing spaces, passed `check_setup.py` and all **eight core notebooks** with optional sections skipped. All 43 regression tests and Python lint/format checks passed. Preview navigation, styling and saved outputs were checked in the browser; all local preview links resolve. Prepared inputs and existing participant work were unchanged. This does not establish native Windows support.

After adding **Exercise 0** on **22 September 2026**, all eight core notebooks completed in separate kernels with optional sections skipped, followed by all 15 solution notebooks with full depth. The new session exercise created Spark 4.2.0 directly through the builder, displayed IDs 0/1/2, observed session reuse and stopped successfully. All 34 authoring/workspace tests and Python lint/format checks passed. The learner preview and chapter 08 introduction were visually reviewed. This is local macOS validation, not evidence of a successful Windows run or a measured five-minute classroom duration.

Before adding Exercise 0 on **22 September 2026**, the exercise-based layout passed on macOS with Python 3.12, PySpark 4.2.0 and Temurin 21.0.11. First, all **seven core notebooks** completed in fresh kernels with every optional section skipped. Then all **14 solution notebooks** completed, including every inline zoom-in and the seven deeper investigations visited at their associated exercise boundaries. The baseline and full-depth runs both preserved the saved-function and checkpoint handoffs and reached the expected 100.00 report. All 32 authoring/workspace tests and Python lint checks passed. Learner notebooks have unfinished tasks and no saved outputs.

The instructor reports that the previous notebook worked on Windows; the redesigned sequence still needs end-to-end Windows validation and a timing rehearsal. The records below describe earlier versions.

On 21 September 2026, the locked uv project was installed into a fresh environment and checked on macOS arm64 with Python **3.12.13**, PySpark **4.2.0** and Temurin **21.0.11**. Both the Python script and all notebook cells completed. The original notebook had also passed with Python 3.12.14 before this setup change.

- Setup preflight passed: matching Python worker, Parquet reads/writes, atomic arrivals, stateful checkpoint restart and streaming Parquet output.
- Complete `uv run --locked hands_on.py` execution passed.
- Notebook format validated and all 36 cells executed in order.
- Eight input rows, five accepted rows and exactly s6/s7/s8 rejected.
- Normalized lookup keys checked; all expected category totals verified.
- Batch Parquet output read back and compared with the expected report.
- Three arrivals verified, including an orderly restart with the same checkpoint.
- AvailableNow file sink completed, yielding five distinct accepted sale IDs.
- Daily-report exercise yielded four rows and preserved the total of 100.00.
- Executed notebook and HTML preview include the observed outputs.

On **22 September 2026**, the instructor reported that `winget install --id EclipseAdoptium.Temurin.21.JDK --exact` successfully installed Java on Windows when run in PowerShell as Administrator. This records the installation step; the Windows setup check and lesson run are still pending.

On **22 September 2026**, the macOS setup instructions were checked against [SDKMAN's Homebrew tap](https://github.com/sdkman/homebrew-tap). SDKMAN's validation API accepted `21.0.12-tem`, and its download URLs resolved successfully for both Apple Silicon and Intel Macs. A fresh Homebrew/SDKMAN installation and a lab run with this patch have not been performed; the executed macOS validation above used 21.0.11.

Full lab validation on native Windows, Linux, WSL, distributed clusters, Spark Connect and AWS Glue remains pending, as does crash-injection testing. Local checks cannot establish support for those environments.

## Agent support

[AGENTS.md](../AGENTS.md) is the shared setup and coaching policy. [CLAUDE.md](../CLAUDE.md) imports it so the two entry points stay aligned. Have participants start their agent from the `labs` folder; both files also ship in the GitHub Release download.

Agents may install and troubleshoot the environment, then give one nudge at a time. Participants write the answers. Explicit maintainer requests to change the course are treated as authoring work. These files guide agent behaviour; they are not an access-control mechanism, and the current worked references remain readable.

When reviewing an agent-assisted setup, check that it uses `check_setup.py`, reports actual failures, stops before completing exercises, and responds to a request for a solution with a hint. These behaviours have not been validated by running separate agent sessions.

Instruction-file conventions: [Codex AGENTS.md](https://learn.chatgpt.com/docs/agent-configuration/agents-md) and [Claude Code imports](https://code.claude.com/docs/en/memory#import-additional-files).

## Maintaining the lab

| Folder | Contents |
|---|---|
| `notebooks/` | Learner notebooks, with larger investigations in `deeper/` |
| `solutions/` | Worked notebooks |
| `data/` | Prepared inputs |
| `docs/` | Setup troubleshooting, catch-up help and API reference |
| `lab_support/` | Session setup, exercise checks, saved-work helpers and reference transformations |
| `author/` | Lesson source, fixture preparation and build/package tools |
| `previews/` | Generated HTML mirroring `notebooks/` and `solutions/`, plus their stylesheet |

`index.html` remains the browser entry point. The setup command remains `uv run --locked check_setup.py`. Participant-owned `learner_work/` and `runs/` stay in the lab root and are excluded from distribution.

Edit `author/hands_on.py` as the teaching source; `lab_support/pipeline.py` is the matching reusable transformation module for chapter 09. The source remains a complete runnable reference (`uv run --locked -m author.hands_on` from labs). Annotated `# %%` cells have stable IDs and roles; comment-only `[starter]` cells replace a named task; `depth=zoom` marks optional cells. Missing/ambiguous starters fail generation. Operational setup, saved-code handoffs and notebook boundaries are defined in `author/lesson_source.py`.

Generate learner and solution notebooks and lightweight HTML previews under `previews/` from the **labs** folder:

```text
uv run --locked --group notebook --group author -m author.build_notebook
```

To execute every reference-completed exercise, each in a separate kernel:

```text
uv run --locked check_setup.py
uv run --locked --group notebook --group author -m author.build_notebook --execute
```

Use `--execute --core-only` first to skip every zoom-in and validate the complete baseline. Then use `--execute` to run all sections plus the deeper notebooks. These are validation modes over the same notebook files, not alternative learner routes. This intentionally executes solutions, not blank learner exercises. Learner notebooks always have empty outputs. Saved output uses the labelled placeholders `<lab-root>` for this machine’s lab directory and `<validation-python>` for the interpreter path. Results are otherwise retained as executed. Saved solution output is preserved only when the lesson and supporting Python sources are unchanged; generation alone is not execution evidence. Do not regenerate over a participant's edited notebooks.

Keep the seven transformation definitions aligned with `lab_support/pipeline.py`; the AST parity test checks this. Tests also cover missing starters, solution isolation and optional prerequisites, saving learner functions, recovery backups and checkpoint boundaries. Rebuild and verify the course after changing published lab assets.

Include `uv.lock` with the project. Dependency changes require a new preflight and core and full-depth execution. The lab ZIP is generated only for a release; see [Publishing the lab](https://github.com/dannyscodecorner/mastering-pyspark/blob/main/docs/PUBLISHING.md#publishing-the-lab).
