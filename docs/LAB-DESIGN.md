# Hands-on lab design

## Desired outcome

Participants build one sales pipeline: inspect prepared Parquet, clean and validate it, preserve the intended sale population through a join, aggregate and save a report, then reuse their transformations on arriving files and resume from a checkpoint.

The exercise is the stable unit. Every core exercise has one learner notebook and one separate worked solution. Time budgets do not create alternate copies of either the notebook or the participant's answers.

## Depth within an exercise

- **Core:** a complete baseline across Exercises 0–7, aiming for about 60 minutes including discussion and catch-up. Supplied wrappers and operational code leave participants to make the central decisions and write selected expressions.
- **Optional zoom-in:** a clearly separated section after that exercise's core checks, adding approximately 30 minutes across the chapter. A participant can choose it for one topic and skip it for another.
- **Deeper investigation:** a separate notebook only where a topic warrants its own context and task. Links live beside the relevant exercise, with explicit prerequisites. There is no detailed route to switch into.

Installation is pre-work. The timing figures below are facilitation budgets, not measured completion times. A learner rehearsal is still required.

| Exercise | Core | Optional zoom-in | Extra time |
|---|---:|---|---:|
| 0. Create a SparkSession | 5 min | — | — |
| 1. Inspect the inputs | 5 min | Row grain, stored schemas and meaningful values | 3 min |
| 2. Clean the keys | 5 min | Column expressions, renaming/dropping and immutability | 5 min |
| 3. Validate the sales | 5 min | Build tolerant decimal/timestamp parsing expressions | 6 min |
| 4. Join and aggregate | 10 min | Compare an inner join without changing the working report | 5 min |
| 5. Inspect and save | 5 min | Read the formatted physical plan | 4 min |
| 6. Process arriving files | 10 min | Inspect the DataFrame, writer, query and last progress | 4 min |
| 7. Resume from a checkpoint | 5 min | Inspect checkpoint contents and explain recovery | 3 min |
| Discussion, catch-up and finish | 10 min | | |
| **Total** | **60 min** | **With all zoom-ins** | **90 min overall** |

## Notebook shape

1. State the question and core success condition.
2. Run supplied setup, loading only the prerequisite learner functions.
3. Work through the core tasks, predictions, checks and progressive hints.
4. At **Core complete**, offer a direct link to **Save and finish**, alongside the optional zoom-in below.
5. Keep optional experiments in separate variables. They must not change the core functions or create state that the next core exercise requires.
6. Save the participant's functions and stop this notebook's SparkSession.
7. Link to the next exercise and related deeper investigations using the same saved work.

Exercise 0 introduces the lifecycle before this shared pattern: its setup imports `SparkSession` and reports the kernel, but the learner creates the session explicitly. It has no optional zoom-in or saved-function dependency; its Finish cell only stops Spark. Later notebooks link back to its explanation of the `create_spark` helper.

Do not put completed answers in learner task cells or save execution outputs in distributed learner notebooks. Expected results and operational scaffolding are supplied deliberately. Worked answers are separately accessible for comparison after an attempt. Participants' agents help with setup and nudges, not completed answers.

## Core contracts and handoffs

Use the prepared eight-row sales fixture and three-row product lookup. Preserve the original data. One raw sales row represents an attempted sale; one lookup row represents a product category.

- Exercise 0 creates a local SparkSession, runs a small DataFrame, observes `getOrCreate()` reuse and stops Spark. No live session or function definitions are passed to Exercise 1.
- Exercise 1 discovers malformed values, string-typed amount/time fields and inconsistent keys.
- Exercise 2 saves `product_key` and `clean_products`. The supplied lookup wrapper uses the participant's key expression.
- Exercise 3 saves `clean_sales`, `accepted_sales` and `rejected_sales`. Missing keys, invalid/missing amounts and invalid/missing timestamps are rejected. A valid key absent from the lookup is accepted. Retain raw values and a rejection reason.
- Exercise 4 saves `enrich_sales` and `category_totals`. Require one lookup row per key, preserve unmatched sales, label a missing category `unmapped`, and produce one row per category.
- Exercise 5 writes report and reject outputs to fresh paths and reads the report back. Writes return `None` in Python; files are their side effect.
- Exercise 6 reuses the participant's transformations on a streaming reader, keeps the lookup static, processes arrivals 01/02 and saves its stream handoff after stopping the query.
- Exercise 7 opens another kernel and restarts from the saved input, functions and checkpoint. It processes arrival 03 and checks equality with the batch report.

Expected reconciliation is **8 input = 5 accepted + 3 rejected**, with s6/s7/s8 rejected. The report contains books 50.00, games 40.00 and unmapped 10.00. Streaming totals progress through 65.00, 90.00 and 100.00 after available input is consumed. A file arrival is not a guarantee of one file per micro-batch.

Every notebook starts its own SparkSession. `Workspace.save` captures the participant's actual function source in `learner_work/answers.py`; subsequent core or deeper notebooks load that same module. Solution notebooks use `learner_work/solutions/` separately. No normal handoff imports a hidden reference implementation.

Exercise 6 also saves its input/checkpoint path, query name, arrival boundary and a hash of the saved functions. Exercise 7 resumes only that compatible state. Replaying Exercise 6 creates a fresh run; it does not delete an existing checkpoint. This is an orderly stop/restart demonstration, not a crash-injection test. The memory sink is a debugging aid, not durable external output.

## Deeper investigations

These are topic branches, not a second version of the core exercises. They use their stated prerequisites and can be chosen independently. Each has its own task, hints, checks and solution.

| Investigation | Open after | What to discover |
|---|---|---|
| Schemas and parsing | Exercise 3 | Read the same fixture as CSV with an explicit schema; apply validation to a separate malformed/missing-value fixture. Stored types do not establish business validity. |
| Product tags | Exercise 2 | Use `split`, `explode` and `distinct` on separate product tags. Six product/tag associations represent five distinct tags; explain the new row grain. |
| Join investigations | Exercise 4 | Use semi/anti joins and duplicate a lookup key in a separate DataFrame. The unchecked join has eight rows and totals 150.00. Keep the working lookup unchanged. |
| Daily report | Exercise 4 | Group by date/category, calculate total and largest sale, and explain the two measures. Four groups preserve 100.00. |
| Plans and repeated work | Exercise 5 | Compare projection/join/aggregate plans; cache, materialise and unpersist a report. Do not infer performance from a tiny local fixture. |
| Persist streaming output | Exercise 7 | Run an independent Append/Parquet/AvailableNow query, with its own checkpoint. Five stored sale IDs reproduce the batch report. |
| Fresh checkpoint | Exercise 7 | Start an independent aggregate with fresh state over the available files. Explain why a new query history is different from resuming the existing query or appending duplicates to an external sink. |

## Getting unstuck

A participant may deliberately choose a supplied catch-up boundary through keys, validation or reporting. The helper backs up their saved functions before replacing that boundary; it never silently completes an exercise or overwrites notebook edits. [Recovery instructions](../labs/docs/RECOVERY.md) explain safe replay and checkpoint reuse. Choosing an optional zoom-in does not require catch-up or a new workspace.

## Authoring and verification

`labs/author/hands_on.py` is the one annotated lesson source and runnable reference. Each task has exactly one comment-only `[starter]`; completed code belongs to the solution edition. `depth=zoom` marks an optional teaching unit. `author/lesson_source.py` selects exercise boundaries, places optional units after the core, and generates independent setup/finish cells.

The generated layout is:

```text
labs/
  notebooks/
    00-spark-session.ipynb
    01-inspect.ipynb
    ...
    07-checkpoint.ipynb
    deeper/
      schemas-and-parsing.ipynb
      ...
  solutions/                  # Matching completed notebooks
  previews/                   # Generated HTML and stylesheet
    notebooks/
    solutions/
  docs/                       # Participant help and reference
  lab_support/                # Shared Python helpers
  author/                     # Lesson source and authoring tools
  learner_work/               # Local participant work; never published
```

The generator creates one learner and one solution notebook per exercise, with lightweight HTML previews. There are no time-based directories. The README and browser index lead with exercise names and offer deeper links in context.

Validate the baseline with `--execute --core-only`: eight fresh kernels, skipping every optional section. Then run `--execute`: all zoom-ins and deeper notebooks, visiting investigations at their associated exercise boundaries. This proves that optional work can be skipped and that exploring it does not disrupt the remaining core. Blank learner worksheets deliberately cannot pass Run All.

Tests cover one starter per task, learner-output exclusion, one notebook per exercise, shared learner functions, solution isolation, recovery backups, minimal topic prerequisites and checkpoint boundaries. `lab_support/pipeline.py` remains the reference module and chapter 09 handoff; AST checks keep its seven transformation functions aligned with the lesson.

Build and verify the native Incan course after publishing-source changes. Check links, the ZIP contents and changed slides in a browser. Do not publish learner answers, local environments, caches, runs or checkpoints. Runtime validation and classroom pacing are separate claims; record both honestly.

## Slides

Keep the established slide IDs. Chapter 08 opens with the shared outcome and Exercises 0–7, then installation setup, then the SparkSession introduction and pipeline task briefs. Presenter notes identify optional depth. The checkpoint slide links directly to the recap; the daily report and persisted output remain clearly optional. Use one deck and one notebook sequence.

## Reuse of the original course

The comparison used the original PowerPoint recaps/notes and the published
notebooks at revision `8cbb218a87052cd1a37cbe4a7862e772c15e5e44` of the
[original course repository](https://github.com/PacktPublishing/Mastering-Big-Data-Analytics-with-PySpark/tree/8cbb218a87052cd1a37cbe4a7862e772c15e5e44).

| Original material | Place in this design |
|---|---|
| 2.5 data operations reference | A compact current reference and the plans/actions extension |
| 3.1 CSV loading and schemas | Investigate before correcting; optional schema extension |
| 3.2 functions, timestamps and column operations | Core cleaning and validation; detailed expression explanation |
| 3.3 genres, arrays, filtering and exploration | Product-tags extension using the same transformation ideas |
| 3.4–3.5 joins, grouping and aggregates | Core category report, join investigations and daily report |
| 6.2–6.3 exploration and wrangling | Inspect values, list problems, then assemble justified transformations |
| 8.3 reader conversion and query management | Core batch-to-streaming sequence and query inspection |
| 8.4 assembly of a streaming application | Reuse transformation functions in a running pipeline; the course's ML/Twitter application is outside this lab |

Retain the teaching progression while updating implementation for the locked
runtime. The old path assumptions, single-partition shortcuts and display
polling loops do not become requirements of the new lab.
