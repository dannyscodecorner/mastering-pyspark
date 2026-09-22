# Chapter 08 lab design

Design baseline: 22 September 2026.

This document specifies the agreed 60-minute, 90-minute and detailed self-paced
routes. The current [lesson](../labs/hands_on.py) is still a complete
worked reference with nine exercises. The route generation and learner versions
described here remain to be implemented.

## Intended outcome

Every route builds the same sales pipeline. Participants inspect messy inputs,
produce a checked category report, reuse their transformations as files arrive,
and resume the query from its checkpoint. They should be able to explain why the
report includes the unmatched sale and how the stream reaches the same result.

The 90-minute route is the classroom default. The 60-minute route supplies more
implementation while retaining meaningful coding and the complete pipeline
story. The self-paced route explains each decision and offers further experiments
that participants can complete without an instructor.

Depth describes how much participants implement and investigate. It is not an
ability label. A participant may use a supplied implementation during class and
return to the fuller task afterwards.

## Delivery constraints

- The spoken course is planned for approximately four hours. The lab uses the
  sales/products context established earlier and gives participants frequent
  opportunities to run code and inspect a result.
- Attendees already have VS Code, Python and uv. Installation, dependency
  downloads and the full setup check are pre-work. The classroom setup step
  opens the selected route and starts its local SparkSession.
- Retain the locked Python 3.12, PySpark 4.2.0 and Java 21 lab baseline. The
  [instructor notes](../labs/author/README.md) record platform validation, including the outstanding native Windows check and the spare MacBook plan.
- Use prepared Parquet inputs and controlled file arrivals. The lab requires no
  Docker, external account, Twitter feed or downloaded training dataset.
- The Python script with VS Code cells remains the baseline. A notebook and
  readable HTML guide present the same route. A hosted notebook service is not
  required.
- AWS-specific storage, credentials, packaging and deployment belong in chapter
  09. The reusable transformation functions form the handoff.

## Routes and timing

These are facilitation budgets, including reading, coding and discussion, not
measured completion times. Rehearse with a learner after the exercise versions
exist. Keep ten minutes for catch-up and the closing discussion in both routes.

| Milestone | 60-minute route | 90-minute route |
|---|---:|---:|
| Launch and goal | 5 | 5 |
| 1. Inspect the inputs | 5 | 8 |
| 2. Clean the keys | 5 | 10 |
| 3. Validate the sales | 5 | 12 |
| 4. Join and aggregate | 10 | 15 |
| 5. Inspect and save the report | 5 | 10 |
| 6. Process arriving files | 10 | 12 |
| 7. Resume from a checkpoint | 5 | 8 |
| Catch-up, recap and cleanup | 10 | 10 |
| **Total minutes** | **60** | **90** |

Keep core exercise numbers 1–7 consistent across routes, slides and solutions.
The detailed route follows these same milestones with explanations and named
extensions linked at the relevant point. It has no fixed completion time.

If a two-hour classroom slot is available, use the 90-minute route and select
the reshaping and persisted-stream-output extensions, allowing about 15 minutes
each. They remain optional; every route already has a complete ending.

## Shared data and completion criteria

Use the current fixture and [transformation contracts](../labs/pipeline.py).
Do not change its baseline results to accommodate a new extension.

| Check | Expected result |
|---|---|
| Inputs | Eight sales and three product lookup rows |
| Accepted sales | Five, with IDs s1–s5 |
| Rejected sales | s6: invalid amount; s7: missing amount; s8: invalid timestamp |
| Reconciliation | Eight inputs = five accepted + three rejected |
| Lookup contract | One row per normalised product key |
| Unmatched sale | s4 / M1 / 10.00 remains accepted; its report category is `unmapped` |
| Category report | books: 3 sales / 50.00; games: 1 / 40.00; unmapped: 1 / 10.00 |
| Saved batch report | Same three category rows and total 100.00 when read back |
| Streaming result after arrival 01 | Two accepted sales, total 65.00 |
| Streaming result after arrival 02 | Four accepted sales, total 90.00 |
| After restart and arrival 03 | Five accepted sales, total 100.00; same category report as batch |
| Exit | Active exercise queries and the local SparkSession are stopped |

These streaming checks occur after processing each published arrival. They do
not assume that one input file always equals one micro-batch, or that an exact
batch number will appear in progress information.

`unmapped` is the course's reporting policy. Invalid values and a valid product
key absent from the lookup are different cases. The lab must make that
distinction explicit before learners write their filters.

## Core exercise briefs

### 1. Inspect the inputs

Question: what needs attention before these sales can become a reliable report?

- **60 minutes:** complete the two Parquet reads in a supplied scaffold, inspect
  the displayed values and schema, and identify at least two issues.
- **90 minutes:** write the reads, choose useful projections for inspection, and
  identify inconsistent keys/categories, amounts and timestamps stored as raw
  strings, malformed values and missing lookup information.
- **Detailed:** explain the stored schema, row grain and what each field means.
  Include questions about which problems are visible in a schema and which
  require inspecting values. Link to the schema extension.

Output: `raw` and `raw_products`, plus a short list of observations. Introduce
the cleaning tasks after this investigation so every transformation has a reason.

### 2. Clean the keys

Question: how can differently written product keys match reliably?

- **60 minutes:** fill in the normalisation expression and inspect the result.
  Supply the surrounding function and category-cleaning code.
- **90 minutes:** compose the key expression, put it in `product_key`, and
  implement `clean_products`. Use projections and aliases to retain clear
  column names.
- **Detailed:** explain `F`, `Column`, literals, aliases and expression
  composition. Compare the original and derived DataFrames. Practise adding,
  renaming and dropping columns in a separate exploratory result.

Checks: `" b1 "` becomes `B1`, `"g1"` becomes `G1`, and `" Books "` becomes
`books`. The original input remains available. Explain why a Python helper
returning a Column expression is different from a Python UDF.

### 3. Validate the sales

Question: which rows can enter the report, and how can rejected rows be explained?

- **60 minutes:** use the supplied `clean_sales` function. Predict the bad rows,
  complete the accepted/rejected filters, and inspect rejection reasons.
- **90 minutes:** complete amount and timestamp parsing and the rejection-rule
  scaffold, then separate and reconcile the two results. Provide the timestamp
  pattern and decimal type so API discovery does not consume the whole exercise.
- **Detailed:** explain null propagation and parsing choices, retain raw values
  for diagnosis, and try additional malformed and missing-key inputs in a
  separate fixture. Compare a parseable value with a valid business value.

Outputs: `cleaned`, `accepted` and `rejected`, backed by reusable transformation
functions. Check the exact rejected IDs and 8 = 5 + 3. M1 must remain accepted.

### 4. Join and aggregate

Question: what would cause this report to lose sales or count them twice?

- **60 minutes:** supply the lookup checks and output projection. Learners choose
  the join type and complete the grouping, count and sum expressions. Ask them
  to explain the `unmapped` row.
- **90 minutes:** implement `enrich_sales` and `category_totals` using the
  validated inputs. Inspect the lookup checks. Compare a separate inner-join
  result with the left-join report, then explain the 90.00 versus 100.00 total.
- **Detailed:** explain key-based matching and row grain, aliases, missing lookup
  values and multiple aggregates. Link to the join and reporting extensions.

Outputs: `enriched` and `report`, with the five accepted sales and the three
expected category totals. Experiments use separate variables and leave the
static lookup unchanged for streaming.

### 5. Inspect and save the report

Question: what work have we described, and what evidence says the result is right?

- **60 minutes:** run supplied verification and write/read-back cells. Identify
  the action that writes output and check the report after reading it back.
- **90 minutes:** inspect the formatted plan, identify the join strategy and any
  exchanges shown, complete the write/read-back steps, and check reconciliation.
  Save the rejected rows as well.
- **Detailed:** connect operators to the code, discuss actions and repeated work,
  inspect output files, and explain the limits of a tiny local fixture.

Provide verification helpers and fresh output paths. Do not ask participants to
write a test framework. Check values rather than row ordering or exact physical
plan text. The eight-row fixture is for reasoning about behaviour, not comparing
performance or proving scalability.

### 6. Process arriving files

Question: which parts of our working batch pipeline change when the input keeps arriving?

- **60 minutes:** change the reader in the supplied skeleton and connect the
  same transformation functions. Complete the query start, publish two arrivals
  with the helper, and inspect the changing report.
- **90 minutes:** assemble the streaming reader and writer using supplied paths
  and schema. Choose Complete mode from the result behaviour, start the query,
  inspect `isStreaming`, `isActive` and `lastProgress`, and check both arrivals.
- **Detailed:** explain the streaming DataFrame, writer and running query as
  distinct objects. Show where bounded-result inspection occurs, how the file
  publisher works, and why this supported pipeline can reuse its transformations.

Retain the Complete-mode memory sink as an inspectable classroom result. Supply
the input schema, query name, checkpoint path, arrival publisher and waiting
helper. Explain that the trigger interval is a scheduling choice and that the
memory table is not durable external output. Keep the product lookup fixed.

### 7. Resume from a checkpoint

Question: after restarting, will the first two arrivals be counted again?

- **60 minutes:** predict the outcome, run the provided stop/restart sequence,
  publish arrival 03, and verify the result.
- **90 minutes:** perform the stop/restart using the same query configuration,
  input and checkpoint; add arrival 03 and compare with the batch report.
- **Detailed:** explain retained progress and aggregate state, compare restart
  with a new independent run, and link to the checkpoint and output extensions.

This is an orderly stop/restart in the same exercise environment. It does not
establish behaviour during an arbitrary crash. Finish by checking five accepted
sales, a total of 100.00 and equality with the batch report.

## Learner experience within an exercise

Each exercise contains a short goal, a task, an observable success condition,
progressive hints, a separately accessible solution, and an explanation of the
result. Show the task before the answer. Keep essential operational instructions
in every route; longer explanations belong in the detailed view.

For example, the normalisation task asks learners to turn `" b1 "` into `B1`.
The first hint names the required operations. A later hint shows how expressions
nest. The solution supplies the expression and explains its Column result.
The detailed version adds the original-versus-derived DataFrame inspection.

Before a revealing operation, ask for a prediction: which rows are rejected,
which sale an inner join loses, what the next arrival changes, or whether a
restart repeats earlier input. These prompts remain useful in the shorter route.

Provide a small reference for the functions and operations actually used, with
examples tied to the sales data. Link to the API documentation for the locked
Spark version rather than embedding a large historical API catalogue.

## Continuing after a skipped or unfinished task

Routes share the same output names, schemas and pure transformation functions.
A skipped exercise implementation must have an explicit supplied equivalent.
No later core cell may require a variable created only in an extension.

| Boundary | Required state before continuing | Supplied recovery |
|---|---|---|
| After inspection | `raw`, `raw_products` | Prepared read cells |
| After cleaning/validation | Cleaning/filter functions; `products`, `cleaned`, `accepted`, `rejected` | Reference functions and cells that recompute these values from the raw inputs |
| After reporting | `enrich_sales`, `category_totals`, `enriched`, `report` | Reference transformations, recomputed report and the same checks |
| Before streaming | Passing batch checks; reusable functions; untouched product lookup | Use the reference pipeline and start the streaming exercise explicitly |
| During streaming | Known input publications and query/checkpoint state | A supplied stop-and-restart-exercise procedure using a new run directory |

Recovery must be deliberate and labelled. Never silently replace a learner's
function after they edit it. In particular, `clean_sales` and `clean_products`
must use the learner's `product_key` on the route where they implement it; a
hidden import of another module's helper would make that task misleading.

Separate ordinary replay from the checkpoint demonstration. Replaying the lab
uses fresh directories and query names. The checkpoint exercise intentionally
keeps the existing input and checkpoint. Do not recover by deleting checkpoints,
republishing the same arrival or overwriting prepared inputs.

Detailed experiments that modify functions or lookup data run before starting
a stream, or in a separate stopped-query context. Each has a clear return to the
baseline. Cleanup handles only the queries that the selected route actually
created; it cannot assume that the optional Parquet query exists.

## Detailed extensions

These are named branches from core exercises. They do not become prerequisites
for later core work. Each receives its own prompt, prepared inputs where needed,
hints, reference solution and checks.

| Extension | Entry point | Task and expected evidence |
|---|---|---|
| Schemas and parsing | After 1 | Read an optional CSV representation of the same raw fixture, compare loading options and an explicit schema, and reconcile it with the Parquet input. Explain why a declared string type does not validate the meaning of an amount. |
| Expressions and immutability | After 2 | Build an alternative projection, rename/drop columns, and inspect both original and derived schemas. The raw input remains eight rows with its original four columns. |
| Reshaping product tags | After 3 | Apply `split`, `explode`, `select` and `distinct` to a separate product-tag fixture. Identify the new row grain. See fixture below. |
| Join investigations | After 4 | Find the unmatched s4 sale with an anti join; compare matched sales with a semi join. Duplicate the B1 lookup row in a separate experiment: the unchecked join produces eight sales rows totalling 150.00, demonstrating why the lookup check matters. |
| Daily report and aggregates | After 4 | Reuse the existing daily-report challenge. Produce four date/category rows totalling 100.00. Add another justified aggregate and explain what it measures. |
| Plans and repeated work | After 5 | Inspect plans for a projection, join and aggregate. Explore repeated actions and optional persistence, checking results and cleaning up persistence. Avoid timing claims based on this fixture. |
| Persist streaming output | After 7 | Reuse the existing separate Append-mode Parquet query with its own checkpoint and AvailableNow trigger. Store five unique accepted sale IDs; aggregating the stored rows reproduces the category report. |
| Checkpoint comparison | After 7 | Compare the existing checkpoint with a separate fresh-checkpoint run using independent state and output. Explain why a fresh query sees the available files again; do not describe a fresh aggregate as automatically doubling the old result. |

The proposed tags fixture is separate from `products.parquet`:

| product_id | tags_raw |
|---|---|
| B1 | books\|reading |
| G1 | games\|gifts |
| X1 | accessories\|gifts |

Expected result: six product/tag rows and five distinct tags, with `gifts`
associated with two products. Learners count product/tag associations here.
They should not sum sale amounts over exploded tags without first deciding how
sales are attributed across tags. Keep the main report's one-row-per-sale grain.

The daily-report check remains:

| sale_date | category | total |
|---|---|---:|
| 2026-09-01 | books | 25.00 |
| 2026-09-01 | games | 40.00 |
| 2026-09-02 | books | 25.00 |
| 2026-09-02 | unmapped | 10.00 |

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

## Authoring and generated material

Maintain one lesson source in `labs/hands_on.py`. Each teaching unit
needs a stable ID, its exercise/extension association and a role such as prompt,
starter, supplied code, hint, solution or check. Associate units with routes
explicitly. The generator should select units by that metadata, with a shared
initialisation and cleanup sequence.

Keep the worked reference runnable. Generate the learner scripts, notebooks and
HTML guides from the same authored units. Keep generated route scripts at the
lab root so local helper imports work consistently. Use the existing
`hands-on.ipynb` and `hands-on.html` URLs as the default 90-minute learner route
once the separate worked solution is available; update links and verification
together when that transition happens.

`pipeline.py` remains the reference implementation and chapter 09 handoff. Its
transformation definitions must stay aligned with the lesson, preferably through
generation from the same reference blocks. Learner routes must actually use
learner-authored functions unless the participant explicitly chooses recovery.

A route index identifies the 60-minute, 90-minute and detailed versions. It states
what learners will achieve and which scaffolding is supplied. Hints and solutions
remain reachable from the downloaded project without an external service. The
README and slides point to this index rather than to an unlabelled worked answer.

Extend `author/build_notebook.py` and `tools/course.py` to understand all generated
routes. The current one-notebook equality check cannot establish route correctness.
Starter files intentionally contain unfinished tasks; execute the reference
completion of each route for validation rather than pretending a blank worksheet
should pass a full run.

## Slide mapping

Keep the existing slugs so earlier links continue to resolve. The chapter opens
with the outcome and route choice, then a setup walkthrough, then one task slide
per core exercise. Slides carry the task and success condition; the guide carries
long explanations, hints and solutions.

| Existing slide/module | Planned treatment |
|---|---|
| `data-work` | Shared outcome, seven core exercises, route selection and lab links |
| `pyspark-setup` | Opening the chosen route and starting Spark; installation remains pre-work |
| `pyspark-inputs` | Exercise 1, with discovery questions before the cleaning recipe |
| `pyspark-cleaning` | Exercise 2, with supplied-versus-authored code made clear in the guide |
| `pyspark-types` | Exercise 3 and the 8 = 5 + 3 check |
| `pyspark-report` | Exercise 4 and the total of 100.00 |
| `pyspark-write` | Exercise 5, including the 90-minute plan-inspection prompt |
| `pyspark-streaming-query` | Exercise 6 and the two observable arrival results |
| `pyspark-streaming-restart` | Exercise 7 and the common finish |
| `pyspark-streaming-files` | Named optional extension: persisted streaming output |
| `pyspark-daily-exercise` | Named optional extension: daily report; linked from exercise 4 |
| `working-pyspark-recap` | Shared outcomes; distinguish the optional stored stream output |

Give optional material an explicit extension label and a clear route back to the
recap. A shorter presentation path must be able to reach the recap directly from
exercise 7 without teaching either extension. Use one deck, with presenter notes
for route depth, rather than independently maintained slide copies.

## Implementation sequence and acceptance

1. Author the 90-minute learner tasks, progressive hints, checks and solutions
   around exercises 1–7. Separate them from the existing worked reference.
2. Add explicit supplied-code choices for the 60-minute route. Verify that each
   shortened step leaves the same state and uses its intended learner edits.
3. Add the detailed explanations and the extensions above, carrying over existing
   daily-report and stream-output code where appropriate.
4. Extend generation and verification, then update the route index, README,
   chapter slides and downloadable project together.
5. Run all reference-completed routes and recovery paths in the locked environment.
   Check exact accepted/rejected IDs, batch read-back, arrival results, checkpoint
   restart and cleanup. Check extensions separately from the baseline fixture.
6. Verify notebook/script correspondence, generated links, offline hints/solutions
   and archive contents. Build and visually inspect changed slides. Rehearse the
   timed routes with a learner and record observed pacing before claiming the
   budgets are validated.

Completion means three usable learner routes with corresponding explanations
and solutions. A route selector alone, or three copies of the current worked
notebook, does not fulfil this design.
