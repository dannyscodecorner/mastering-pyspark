# Working with PySpark — guided lab

Build a checked sales report, then run the same transformations as files arrive.
Use a normal Python project in VS Code, managed by **uv**. No Docker or separate
Spark download is used. The prepared Parquet inputs are included.

Course repository: [dannyscodecorner/mastering-pyspark](https://github.com/dannyscodecorner/mastering-pyspark).

## Before class

1. Extract the complete ZIP and open its **chapter08** folder in VS Code (the
   folder containing `pyproject.toml`). Use a writable local folder. On Windows,
   choose a short path such as `C:/work/chapter08` on an NTFS drive.
2. Install **JDK 21** and reopen VS Code; see Java below.
3. In the VS Code terminal, run these same commands on PowerShell, macOS or Linux:

   ```text
   uv sync --locked
   uv run --locked check_setup.py
   ```

The project selects Python **3.12** and locks PySpark to **4.2.0**. uv creates the
`.venv` and can download Python 3.12 if needed. The first setup needs network
access and downloads Spark's JVM libraries as part of PySpark; do this before
class. No shell activation is needed for `uv run`.

The setup check must finish with **Setup check passed**. It tests a Python worker,
Parquet input/output, atomic arrival publication, stateful streaming, checkpoint
restart and a streaming Parquet sink. The small fixture is the actual workshop
data, not a test that only starts Spark.

### Java

Use a 64-bit JDK matching your computer, such as
[Eclipse Temurin 21](https://adoptium.net/temurin/releases/?version=21).
The [Windows installer](https://adoptium.net/installation/windows/) offers PATH
and `JAVA_HOME` settings; enable them. `JAVA_HOME` should name the JDK directory,
not its `bin` directory. Reopen VS Code after installation and run:

```text
java -version
```

It should report version 21 for this workshop. Spark 4.2 also supports Java 17 and
25, but this lab's observed validation uses 21. uv manages Python, not Java.

### Windows status

**Native Windows is not yet validated for this lab.** Jupyter in VS Code supports
Windows; the remaining risk is Spark's Hadoop filesystem support. The bundled
Spark 4.2 distribution uses Hadoop 3.5.0. Hadoop's
[Windows build documentation](https://github.com/apache/hadoop/blob/rel/release-3.5.0/BUILDING.txt#L615-L618)
states that its native Windows components are required. Python, uv and Java alone
may therefore be insufficient for Parquet/checkpoint writes on a clean machine.

Before distributing a native Windows setup as class-ready, the instructor must
supply or approve a matching Hadoop 3.5.0 Windows build (`winutils.exe` and
`hadoop.dll`, with its required runtime libraries), configure `HADOOP_HOME` and
its `bin` directory on PATH, and run the setup check on a representative attendee
machine. This project does not download unverified native binaries. Do not mix
binaries from older Hadoop releases.

If native setup proves impractical, the same uv project can be evaluated in WSL
without Docker. WSL has not been tested here and is not a prerequisite currently
assumed for attendees. Keep this deployment choice out of the teaching slides.

## Work in VS Code

### Python script — the baseline

Open [hands_on.py](hands_on.py). It follows the lesson in order, with prompts,
code, checks and a final exercise. To run the full worked reference:

```text
uv run --locked hands_on.py
```

The `# %%` markers also let VS Code run sections in its Python Interactive window.
For that interface, install the Python and Jupyter extensions, add the optional
kernel dependencies below, and select the project's `.venv` Python environment.
Run cells from the top; later cells use earlier variables.

### Notebook — optional

```text
uv sync --locked --group notebook
```

Open [hands-on.ipynb](hands-on.ipynb), choose **Select Kernel → Python Environments**
and select this project's `.venv`. No separately hosted Jupyter server is needed
for VS Code. Use this environment for both the notebook and Python Interactive
window. The [HTML walkthrough](hands-on.html) is a read-only executed reference.

`hands_on.py` is the editable lesson source. The notebook contains the same cells;
its authoring helper regenerates it when the lesson changes. Participants can
experiment in either copy. Stop the local session with `spark.stop()` before
rerunning setup or switching between interactive copies.

## Local runtime

The setup helper creates `spark` in local mode with two worker threads, UTC
timestamps and two shuffle partitions for this tiny fixture. It selects the same
Python executable for Spark workers as for the driver. It does not connect to a
cluster. The final lesson cell stops the session; script exit also cleans up.

Every run creates a fresh directory under `runs/`; prepared inputs and earlier
runs are never overwritten. The arrival helper stages completed files, then
publishes each through a hard link. Use a local filesystem supporting hard links.
Spark paths use absolute paths with forward slashes, preserving spaces and
Windows drive letters without URL-encoding them.

`pipeline.py` contains only transformations. Chapter 09 will reuse it in AWS Glue
with separately configured storage, identity, runtime and monitoring. The local
file publisher and session helper are workshop scaffolding, not deployment code.

## Troubleshooting

- **Java missing or wrong version:** install JDK 21, correct `JAVA_HOME`/PATH and
  reopen VS Code. Run `java -version` again.
- **Wrong Python or kernel:** use `uv run`, or select the project's `.venv` in
  VS Code. System Python and a previously selected notebook kernel may differ.
- **Unexpected Spark version:** check for an old `SPARK_HOME` override. This
  project uses the Spark bundled with its locked PySpark dependency.
- **`winutils`, `NativeIO$Windows` or `hadoop.dll` errors:** this is the native
  Windows dependency issue above. Keep the complete setup-check output for the
  instructor; a passing `spark.range(...).show()` is not sufficient.
- **Hard-link or file permission error:** extract the project to a writable
  local NTFS/APFS/ext4 folder. The arrival publisher requires hard-link support.
- **Interrupted interactive run:** stop the query or call `spark.stop()` before
  running setup again. The setup cell creates a new run rather than deleting
  old checkpoint files.

Setup references: [uv projects](https://docs.astral.sh/uv/guides/projects/),
[uv with Jupyter](https://docs.astral.sh/uv/guides/integration/jupyter/),
[VS Code Python cells](https://code.visualstudio.com/docs/python/jupyter-support-py),
[Spark 4.2 requirements](https://spark.apache.org/docs/4.2.0/index.html).

## Exercise route

### Instructor fallback laptop

Danny will bring an additional MacBook for an attendee who encounters setup
problems. Prepare that Mac with this same project and JDK 21 before the session:
run `uv sync --locked`, `uv run --locked check_setup.py`, and the full
`uv run --locked hands_on.py`. If using notebooks, also install the optional
notebook group and select its kernel in VS Code beforehand. Leave the project
ready at the first exercise; each run creates its own output directory.

Ask attendees to run the setup check before class. The spare Mac is the
classroom contingency, not evidence that native Windows has been validated.

### Lesson sequence

The chapter opens with an agenda and setup walkthrough. These numbered exercises
then match the slides, `hands_on.py` headings and the optional notebook:

1. **Inspect the inputs:** read the prepared Parquet files and examine schemas and values.
2. **Clean the keys:** use `functions as F` and a reusable Column-expression helper.
3. **Validate the sales:** parse types, retain rejects and reconcile all eight inputs.
4. **Join and aggregate:** check lookup keys and build the category report.
5. **Save and check the report:** validate totals, write Parquet and read it back.
6. **Process arriving files:** switch the reader, start the query and introduce files 01/02.
7. **Resume from a checkpoint:** restart and introduce file 03 without double-counting.
8. **Write the streaming output:** use a separate Append-mode Parquet query and checkpoint.
9. **Build a daily report:** extend the batch result and preserve the total of 100.00.

The lesson is a guided, executable reference with prediction prompts and a
final exercise. It is not a blank assessment notebook. The tiny dataset teaches
behaviour and reconciliation, not performance or scaling.

## Data and checkpoints

The synthetic fixture extends the five sales used earlier in the course.

| Input | Meaning |
|---|---|
| `data/sales.parquet` | Eight raw sales, with strings for amount and timestamp |
| `data/products.parquet` | Three lookup rows with inconsistent category casing |
| `data/arrivals/01` | s1 and s2 |
| `data/arrivals/02` | s3, s4 and rejected s6 |
| `data/arrivals/03` | s5 and rejected s7/s8 |

Expected reconciliation: **8 input = 5 accepted + 3 rejected**. Category totals:
books 50.00, games 40.00, unmapped 10.00. Streaming totals progress through 65.00,
90.00 and 100.00 after each file has been consumed. These are file arrivals, not a
guarantee of one file per micro-batch.

The lesson uses a fresh run directory and refuses to overwrite existing input
or batch output. To resume the restart exercise, retain the same input, query,
static lookup and checkpoint. To replay the whole lab, stop active queries and
run setup again to create a new directory. Do not edit files already consumed.

The category report uses a Complete-mode memory sink for classroom inspection.
The checkpoint restart was verified, but the memory sink is not durable external
output. The separate Append-mode Parquet query writes accepted sales rows before
aggregation. Rejected rows are stored by the batch exercise; routing streaming
rejects to a second audit destination is a possible extension.

If an experimental edit raises an error while a query is running, stop it with
`query.stop()` before restarting setup. The provided successful route stops both
queries and the local SparkSession.

## Original material reused

Reviewed the original PowerPoints and the corresponding public notebooks at
revision `8cbb218a87052cd1a37cbe4a7862e772c15e5e44`:

- [3.2: fixing data](https://github.com/PacktPublishing/Mastering-Big-Data-Analytics-with-PySpark/blob/8cbb218a87052cd1a37cbe4a7862e772c15e5e44/Section%203%20-%20Preparing%20Data%20using%20SparkSQL/3.2/hands-on-3.2.ipynb): built-in functions, timestamp conversion and column transformations.
- [3.3: further preparation](https://github.com/PacktPublishing/Mastering-Big-Data-Analytics-with-PySpark/blob/8cbb218a87052cd1a37cbe4a7862e772c15e5e44/Section%203%20-%20Preparing%20Data%20using%20SparkSQL/3.3/hands-on-3.3.ipynb): exploration and inspecting transformed data. Its split/explode example remains a possible follow-up.
- [8.3: managing and converting streams](https://github.com/PacktPublishing/Mastering-Big-Data-Analytics-with-PySpark/blob/8cbb218a87052cd1a37cbe4a7862e772c15e5e44/Section%208%20-%20Machine%20Learning%20in%20Real-Time/8.3/structured_streaming.ipynb): static versus streaming readers, shared transformations, writer/query distinction, query activity, progress, memory-table inspection and stopping.

The original files were preserved. Twitter acquisition, credentials and sentiment
analysis are excluded. Prepared Parquet inputs replace the Twitter JSON. The
exercise adds explicit rejected-record handling, repeatable arrivals, expected
results and checkpoint/output checks. It removes the unconditional single-file
coalesce, legacy one-time trigger and notebook display polling loop.

`pipeline.py` contains only transformations and is the handoff to chapter 09.
`prepare_inputs.py` is an author-only fixture generator; students do not need its
DataFrame-construction syntax. `arrival_files.py` is exercise scaffolding.

## Validation performed

On 21 September 2026, the locked uv project was installed into a fresh environment
and checked on macOS arm64 with Python **3.12.13**, PySpark **4.2.0** and Temurin
**21.0.11**. Both the Python script and all notebook cells completed. The original
notebook had also passed with Python 3.12.14 before this setup change.

- Setup preflight passed: matching Python worker, Parquet reads/writes, atomic
  arrivals, stateful checkpoint restart and streaming Parquet output.
- Complete `uv run --locked hands_on.py` execution passed.
- Notebook format validated and all 36 cells executed in order.
- Eight input rows, five accepted rows and exactly s6/s7/s8 rejected.
- Normalized lookup keys checked; all expected category totals verified.
- Batch Parquet output read back and compared with the expected report.
- Three arrivals verified, including an orderly restart with the same checkpoint.
- AvailableNow file sink completed, yielding five distinct accepted sale IDs.
- Daily-report exercise yielded four rows and preserved the total of 100.00.
- Executed notebook and HTML preview include the observed outputs.

Native Windows, Linux, WSL, crash-injection, distributed-cluster, Spark Connect
and AWS Glue validation have not been performed. Local checks cannot establish
support for those environments.

## Maintaining the lab

Edit `hands_on.py` as the teaching source; `pipeline.py` is the matching reusable
transformation module for chapter 09. Regenerate and execute the notebook, then
rebuild the download:

```text
uv run --locked --group notebook --group author author/build_notebook.py --execute
uv run --locked author/package_lab.py
```

The archive excludes `.venv`, caches and `runs/`. Include `uv.lock` with the
project; dependency updates should be deliberate and followed by both the setup
check and the full lesson.
