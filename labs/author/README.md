# Lab instructor notes

[Participant setup](../README.md) · [Setup troubleshooting](../TROUBLESHOOTING.md)

Run the commands below from the **labs** folder.

## Exercise route

### Instructor fallback laptop

Danny will bring an additional MacBook for an attendee who encounters setup problems. Prepare that Mac with this same project and JDK 21 before the session: run `uv sync --locked`, `uv run --locked check_setup.py`, and the full `uv run --locked hands_on.py`. If using notebooks, also install the optional notebook group and select its kernel in VS Code beforehand. Leave the project ready at the first exercise; each run creates its own output directory.

Ask attendees to run the setup check before class. The spare Mac is the classroom contingency, not evidence that native Windows has been validated.

### Lesson sequence

The chapter opens with an agenda and setup walkthrough. These numbered exercises then match the slides, `hands_on.py` headings and the optional notebook:

1. **Inspect the inputs:** read the prepared Parquet files and examine schemas and values.
2. **Clean the keys:** use `functions as F` and a reusable Column-expression helper.
3. **Validate the sales:** parse types, retain rejects and reconcile all eight inputs.
4. **Join and aggregate:** check lookup keys and build the category report.
5. **Save and check the report:** validate totals, write Parquet and read it back.
6. **Process arriving files:** switch the reader, start the query and introduce files 01/02.
7. **Resume from a checkpoint:** restart and introduce file 03 without double-counting.
8. **Write the streaming output:** use a separate Append-mode Parquet query and checkpoint.
9. **Build a daily report:** extend the batch result and preserve the total of 100.00.

The lesson is a guided, executable reference with prediction prompts and a final exercise. It is not a blank assessment notebook. The tiny dataset teaches behaviour and reconciliation, not performance or scaling.

## Local runtime

The setup helper creates `spark` in local mode with two worker threads, UTC timestamps and two shuffle partitions for this tiny fixture. It selects the same Python executable for Spark workers as for the driver. It does not connect to a cluster. The final lesson cell stops the session; script exit also cleans up.

Every run creates a fresh directory under `runs/`; prepared inputs and earlier runs are never overwritten. The arrival helper stages completed files, then publishes each through a hard link. Use a local filesystem supporting hard links. Spark paths use absolute paths with forward slashes, preserving spaces and Windows drive letters without URL-encoding them.

`pipeline.py` contains only transformations. Chapter 09 will reuse it in AWS Glue with separately configured storage, identity, runtime and monitoring. The local file publisher and session helper are workshop scaffolding, not deployment code.

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

If an experimental edit raises an error while a query is running, stop it with `query.stop()` before restarting setup. The provided successful route stops both queries and the local SparkSession.

## Original material reused

Reviewed the original PowerPoints and the corresponding public notebooks at revision `8cbb218a87052cd1a37cbe4a7862e772c15e5e44`:

- [3.2: fixing data](https://github.com/PacktPublishing/Mastering-Big-Data-Analytics-with-PySpark/blob/8cbb218a87052cd1a37cbe4a7862e772c15e5e44/Section%203%20-%20Preparing%20Data%20using%20SparkSQL/3.2/hands-on-3.2.ipynb): built-in functions, timestamp conversion and column transformations.
- [3.3: further preparation](https://github.com/PacktPublishing/Mastering-Big-Data-Analytics-with-PySpark/blob/8cbb218a87052cd1a37cbe4a7862e772c15e5e44/Section%203%20-%20Preparing%20Data%20using%20SparkSQL/3.3/hands-on-3.3.ipynb): exploration and inspecting transformed data. Its split/explode example remains a possible follow-up.
- [8.3: managing and converting streams](https://github.com/PacktPublishing/Mastering-Big-Data-Analytics-with-PySpark/blob/8cbb218a87052cd1a37cbe4a7862e772c15e5e44/Section%208%20-%20Machine%20Learning%20in%20Real-Time/8.3/structured_streaming.ipynb): static versus streaming readers, shared transformations, writer/query distinction, query activity, progress, memory-table inspection and stopping.

The original files were preserved. Twitter acquisition, credentials and sentiment analysis are excluded. Prepared Parquet inputs replace the Twitter JSON. The exercise adds explicit rejected-record handling, repeatable arrivals, expected results and checkpoint/output checks. It removes the unconditional single-file coalesce, legacy one-time trigger and notebook display polling loop.

`pipeline.py` contains only transformations and is the handoff to chapter 09. `prepare_inputs.py` is an author-only fixture generator; students do not need its DataFrame-construction syntax. `arrival_files.py` is exercise scaffolding.

## Validation performed

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

Native Windows, Linux, WSL, crash-injection, distributed-cluster, Spark Connect and AWS Glue validation have not been performed. Local checks cannot establish support for those environments.

## Agent support

[AGENTS.md](../AGENTS.md) is the shared setup and coaching policy. [CLAUDE.md](../CLAUDE.md) imports it so the two entry points stay aligned. Have participants start their agent from the `labs` folder; both files also ship in the GitHub Release download.

Agents may install and troubleshoot the environment, then give one nudge at a time. Participants write the answers. Explicit maintainer requests to change the course are treated as authoring work. These files guide agent behaviour; they are not an access-control mechanism, and the current worked references remain readable.

When reviewing an agent-assisted setup, check that it uses `check_setup.py`, reports actual failures, stops before completing exercises, and responds to a request for a solution with a hint. These behaviours have not been validated by running separate agent sessions.

Instruction-file conventions: [Codex AGENTS.md](https://learn.chatgpt.com/docs/agent-configuration/agents-md) and [Claude Code imports](https://code.claude.com/docs/en/memory#import-additional-files).

## Maintaining the lab

Edit `hands_on.py` as the teaching source; `pipeline.py` is the matching reusable transformation module for chapter 09. Regenerate and execute the notebook:

```text
uv run --locked --group notebook --group author author/build_notebook.py --execute
```

Include `uv.lock` with the project; dependency updates should be deliberate and followed by both the setup check and the full lesson. The lab ZIP is generated only when preparing a release; follow [Publishing the lab](https://github.com/dannyscodecorner/mastering-pyspark/blob/main/docs/PUBLISHING.md#publishing-the-lab).
