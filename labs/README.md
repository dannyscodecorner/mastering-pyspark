# Working with PySpark — hands-on lab

Build a sales report from Parquet data, then run the same pipeline as files arrive. **Each exercise is a separate notebook.**

## Start with Exercise 0

Everyone uses the same notebooks and the same saved work. Choose how deeply to explore each topic as you go:

- **About 60 minutes:** complete the **Core** in Exercises 0–7, with time for discussion and catch-up.
- **About 90 minutes:** also do the **Optional zoom-in** sections inside those notebooks.
- **At your own pace:** follow the linked **Deeper investigations** on topics that interest you. Larger investigations have their own notebooks.

You can mix these choices. There is no route to switch and no work to copy. Times are workshop budgets awaiting rehearsal; installation is pre-work.

<!-- TODO: put links / references in a central location, making crosslinking easier -->

## Dependencies

1. **Java 21 (JDK)**
    - [macOS installation instructions](TROUBLESHOOTING.md#java-21-macos).
    - [Windows installation instructions](TROUBLESHOOTING.md#).
2. **[VS Code](https://code.visualstudio.com/download)** with Microsoft's **[Python](https://marketplace.visualstudio.com/items?itemName=ms-python.python)** and **[Jupyter](https://marketplace.visualstudio.com/items?itemName=ms-toolsai.jupyter)** extensions installed.
3. **[Git](https://git-scm.com/install/)** — to clone the repository.
4. **Python 3.12 and [uv](https://docs.astral.sh/uv/getting-started/installation/)**; uv downloads Python 3.12 if needed.
    - [Windows uv instructions](TROUBLESHOOTING.md#uv-on-windows).
    - [macOS uv instructions](TROUBLESHOOTING.md#)

**Native Windows:** also [install the Hadoop components](TROUBLESHOOTING.md#install-the-windows-components).

### Explore Parquet files — optional

The lab ships with various `.parquet` files. If you install [Parquet Explorer](https://marketplace.visualstudio.com/items?itemName=AdamViola.parquet-explorer), it allows you to open a `part-*.parquet` file inside the `data` folder and run SQL queries on the data. For instance `data/sales.parquet` or `data/products.parquet`.

<!-- TODO: consider linking the image from the https://marketplace.visualstudio.com/items?itemName=AdamViola.parquet-explorer page showing how this feature works -->

[Small API reference](API-REFERENCE.md) · [Troubleshooting](TROUBLESHOOTING.md) · [Instructor notes](author/README.md)

## 1. Open the lab

Clone the repository if you do not already have it:

```text
git clone https://github.com/dannyscodecorner/mastering-pyspark.git
```

<!-- TODO: consider checking out only the labs folder at this stage; makes it just a bit easier to digest for the reader (sparse checkout) -->

In VS Code, choose **File → Open Folder** and select **mastering-pyspark/labs**. You should see `pyproject.toml`, `notebooks` and `data` in the Explorer sidebar.

Alternatively, [download the lab from a GitHub Release](https://github.com/dannyscodecorner/mastering-pyspark/releases/latest/download/pyspark-labs.zip), extract it and open the **labs** folder inside.

## 2. Create the virtual environment

After installing the dependencies, reopen VS Code. Choose **Terminal → New Terminal** and run these commands from the **labs** folder, waiting for each to finish:

```text
uv sync --locked --group notebook
```

This first command creates **labs/.venv**, installs Python 3.12 if needed, and installs the locked packages, including PySpark 4.2.0 and the notebook kernel. 

```text
uv run --locked check_setup.py
```

`uv run` uses that environment automatically; terminal activation is not needed.

Wait for **Setup check passed**. If it fails, use [troubleshooting](TROUBLESHOOTING.md) before starting the exercises.

## 3. Install the VS Code extensions

Open **Extensions** with **Ctrl+Shift+X** (Windows/Linux) or **Cmd+Shift+X** (macOS). Install or enable **Python** (`ms-python.python`) and **Jupyter** (`ms-toolsai.jupyter`), both by Microsoft. Follow any reload prompt. These editor extensions are separate from the packages installed by uv.

<!-- TODO: link the VS Code extensions here also -->

## 4. Open Exercise 0 and select the kernel

In the Explorer, open **notebooks → 00-spark-session.ipynb**. Start here regardless of how much time you have.

<!-- TODO: explain the different time paths and levels of detail. Rephrase the "regardless of how much time you have" sentence. -->

Click **Select Kernel** at the notebook's top right, then **Python Environments → .venv**. If a kernel is already selected, click its name and choose **Select Another Kernel** first. Select this lab's Python 3.12:

| System        | Python executable inside `labs` |
| ------------- | ------------------------------- |
| Windows       | `.venv\Scripts\python.exe`      |
| macOS / Linux | `.venv/bin/python`              |

Missing notebook controls or kernel? See [VS Code help](TROUBLESHOOTING.md#vs-code-cells-and-kernels).

## 5. Work through one notebook at a time

**Exercise 0** explains the Python kernel, lets you build a `SparkSession`, and ends by stopping it. Complete that introduction first. From **Exercise 1** onward:

1. Run its supplied **Setup** code cell with the play button beside the cell. Wait for **notebook ready**.
2. Read the task and replace `todo(...)` in the **Your code** cells. Run a cell with its play button or **Shift+Enter**. Use the separate **Check** cells and collapsed hints as you go.
3. At **Core complete**, either follow the link to **Save and finish** or do the **Optional zoom-in** first. Skipping it does not affect later core exercises.
4. Run **Save and finish** to save your functions and stop Spark. Follow the next-exercise link, or a related deeper investigation, and run that notebook's Setup. The previous notebook can be closed.

Do not use **Run All** on an unfinished exercise. Your saved functions live in **learner_work/**; later notebooks use your code, not an answer filled in behind the scenes. The checkpoint exercise also reuses the stream state saved by Exercise 6. Keep your edited notebooks and this folder if you take a break.

Stuck during class? Use a hint first, then an explicit [catch-up step](RECOVERY.md) if needed. Completed answers are separate in **solutions/**. An AI assistant may only help with setup and nudges; [you write the exercise answers](AGENTS.md).

## Exercises

| Exercise                                                         | Optional zoom-in in the same notebook               |
| ---------------------------------------------------------------- | --------------------------------------------------- |
| [0. Create a SparkSession](notebooks/00-spark-session.ipynb)     | Core introduction: create, use and stop the session |
| [1. Inspect the inputs](notebooks/01-inspect.ipynb)              | Row grain, schemas and data quality                 |
| [2. Clean the keys](notebooks/02-clean-keys.ipynb)               | Expressions, renaming, dropping and immutability    |
| [3. Validate the sales](notebooks/03-validate.ipynb)             | Write tolerant parsing expressions                  |
| [4. Join and aggregate](notebooks/04-join-aggregate.ipynb)       | Compare inner and left joins                        |
| [5. Inspect and save the report](notebooks/05-save-report.ipynb) | Read the physical plan                              |
| [6. Process arriving files](notebooks/06-streaming.ipynb)        | Inspect the running query and progress              |
| [7. Resume from a checkpoint](notebooks/07-checkpoint.ipynb)     | Inspect checkpoint contents and explain recovery    |

Each notebook links to related investigations under **notebooks/deeper/**, with prerequisites stated. These cover CSV schemas and parsing, product tags, duplicate lookup keys, daily aggregates, caching, persisted streaming output and fresh checkpoints. The [browser index](index.html) groups them by exercise and offers read-only previews.
