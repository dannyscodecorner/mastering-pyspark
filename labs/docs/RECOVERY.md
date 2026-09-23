# If you get stuck

Try the collapsed hints in your exercise first. You can move on during class and return to an unfinished task later. These are explicit catch-up choices, not part of the normal exercise flow.

## How the notebooks connect

Exercise 0 teaches you to create and stop a SparkSession. It saves no pipeline functions. Later notebooks start their own sessions through the helper explained there and stop them at the end. **Save and finish** writes your function definitions into `learner_work/answers.py`. Later notebooks load them and reconstruct the small batch inputs. Keep helper functions self-contained: use `F`, function arguments and the previously saved helpers, rather than unrelated notebook globals.

Core tasks, optional zoom-ins and deeper investigations share this one answer folder. You can choose extra depth without copying or restarting your work. Solution notebooks use `learner_work/solutions/` and do not replace your answers. Your notebook edits remain your primary working copy.

## Stop safely

If an exercise fails after starting a query, run this in a new code cell in that notebook:

```python
for active_query in spark.streams.active:
    active_query.stop()
spark.stop()
```

This leaves files and checkpoints intact. After a kernel restart, run the notebook's Setup again. Replaying Exercise 6 creates a fresh stream; Exercise 7 intentionally reuses the existing one.

## Explicit catch-up boundaries

For Exercises 3–6, missing saved functions can make Setup stop before Spark starts. The `workspace` object has already been created. Run the appropriate catch-up call below in a new cell, then rerun Setup. If Spark was already started, stop it first with the cleanup cell above.

The helper backs up existing saved functions before replacing them with reference implementations. It never changes your exercise notebook. It replaces the whole boundary through the chosen stage so the functions remain consistent. You can later redo the earlier exercise and save your own code again.

<a id="exercise-0"></a>
### Exercise 0 — the session

A missing `ipykernel` or `pyspark` package points to setup or kernel selection; follow [VS Code troubleshooting](TROUBLESHOOTING.md#vs-code-cells-and-kernels). If `spark` is still `None`, complete the builder task. If you already ran **Finish — stop Spark**, rerun the builder and subsequent cells to start again. After a kernel restart, run the notebook from its Setup cell. Exercise 1 creates its own session; it does not depend on this notebook remaining open.

<a id="exercise-1"></a>
### Exercise 1

There is no saved code prerequisite. Review the read examples in the [API reference](API-REFERENCE.md), or compare the matching separate solution. Exercise 2 supplies its own reads.

<a id="exercise-2"></a>
### Exercise 2 — keys

To continue into Exercise 3 with supplied key and lookup functions:

```python
workspace.use_reference("keys")
```

<a id="exercise-3"></a>
### Exercise 3 — validation

To continue into Exercise 4 with supplied cleaning and filter functions:

```python
workspace.use_reference("validation")
```

<a id="exercise-4"></a>
### Exercise 4 — report

To continue into Exercise 5 or 6 with a supplied complete transformation pipeline:

```python
workspace.use_reference("reporting")
```

<a id="exercise-5"></a>
### Exercise 5 — saved report

Exercise 6 rebuilds its batch comparison using your saved functions. It does not require the report files from Exercise 5. You may move on and return to the write/read-back task later.

A successful write is intentionally not overwritten. Rerun only the read/check cells, or stop Spark and start this notebook again for new output paths.

<a id="exercise-6"></a>
### Exercise 6 — streaming

To replay an interrupted stream, stop its queries and Spark, then rerun Exercise 6 from Setup. It creates a **new** run directory, input and checkpoint; publish arrivals 01 and 02 there and run **Save and finish**. Previous runs are retained.

Do not re-publish a file in the same input directory or delete a checkpoint to silence an error. Do not change saved transformation functions while resuming the same query. If you changed them, replay Exercise 6 first.

<a id="exercise-7"></a>
### Exercise 7 — checkpoint restart

This exercise requires the completed handoff from Exercise 6. Its Setup reads that saved input directory and checkpoint. If you already completed arrival 03, replay Exercise 6 before trying the restart again.

Streaming investigations require the saved handoff after Exercise 7. Other deeper notebooks state their own prerequisites: parsing follows Exercise 3; join/report investigations follow Exercise 4. None is required by a later core task.
