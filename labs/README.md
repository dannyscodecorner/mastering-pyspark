# Working with PySpark — hands-on lab

Build a sales report from Parquet data, then run the same pipeline as files arrive. **Each exercise is a separate notebook.**

## Dependencies

1. **Java 21 (JDK)**
    - [macOS installation instructions][java-macos].
    - [Windows installation instructions][java-windows].
2. **[VS Code][vscode]** with Microsoft's **[Python][python-extension]** and **[Jupyter][jupyter-extension]** extensions installed.
3. **[Git][git]** — to clone the repository.
4. **Python 3.12 and [uv][uv]**; uv downloads Python 3.12 if needed.
    - [Windows uv instructions][uv-windows].
    - [macOS uv instructions][uv-macos].

**Native Windows:** also [install the Hadoop components][hadoop-windows].

### Explore Parquet files — optional

The lab ships with various `.parquet` files. If you install [Parquet Explorer][parquet-explorer], it allows you to open a `part-*.parquet` file inside the `data` folder and run SQL queries on the data. For instance `data/sales.parquet` or `data/products.parquet`.

<details>
<summary>See Parquet Explorer in action</summary>

[![Parquet Explorer preview and SQL query on iris.parquet][parquet-demo]][parquet-explorer]

Demo from the extension's publisher, using `iris.parquet`.

</details>

[Small API reference][api-reference] · [Troubleshooting][troubleshooting] · [Instructor notes][instructor-notes]

## 1. Open the lab

For a new checkout, get the lab folder with Git's [sparse checkout][sparse-checkout]. Skip this if you already have the repository.

```bash
git clone --filter=blob:none --sparse https://github.com/dannyscodecorner/mastering-pyspark.git
git -C mastering-pyspark sparse-checkout set labs
```

In VS Code, choose **File → Open Folder** and select **mastering-pyspark/labs**. You should see `pyproject.toml`, `notebooks` and `data` in the Explorer sidebar.

Alternatively, [download the lab from a GitHub Release][lab-download], extract it and open the **labs** folder inside.

## 2. Create the virtual environment

After installing the dependencies, reopen VS Code. Choose **Terminal → New Terminal** and run these commands from the **labs** folder, waiting for each to finish:

```bash
uv sync --locked --group notebook
```

This creates **labs/.venv**, installs Python 3.12 if needed, and installs the locked packages, including PySpark 4.2.0 and the notebook kernel.

```bash
uv run --locked check_setup.py
```

`uv run` uses that environment automatically; terminal activation is not needed.

Wait for **Setup check passed**. If it fails, use [troubleshooting][troubleshooting] before starting the exercises.

## 3. Install the VS Code extensions

Open **Extensions** with **Ctrl+Shift+X** (Windows/Linux) or **Cmd+Shift+X** (macOS). Install or enable Microsoft's **[Python][python-extension]** and **[Jupyter][jupyter-extension]** extensions. Reload VS Code if prompted.

<a id="start-with-exercise-0"></a>

## 4. Open Exercise 0 and select the kernel

Everyone starts with Exercise 0, then works through Exercises 1–7. Choose how much detail to explore:

- **About 60 minutes:** complete each exercise's **Core** tasks.
- **About 90 minutes:** also complete the **Optional zoom-in** sections in the same notebooks.
- **Self-paced:** add the linked **Deeper investigations**, which have their own notebooks.

You can choose extra detail topic by topic. Times are approximate; complete setup before class.

In the Explorer, open **notebooks → [00-spark-session.ipynb][exercise-0]**. This introduction is part of all three options.

Click **Select Kernel** at the notebook's top right, then **Python Environments → .venv**. If a kernel is already selected, click its name and choose **Select Another Kernel** first. Select this lab's Python 3.12:

| System        | Python executable inside `labs` |
| ------------- | ------------------------------- |
| Windows       | `.venv\Scripts\python.exe`      |
| macOS / Linux | `.venv/bin/python`              |

Missing notebook controls or kernel? See [VS Code help][kernel-help].

## 5. Work through one notebook at a time

**Exercise 0** explains the Python kernel, lets you build a `SparkSession`, and ends by stopping it. Complete that introduction first. From **Exercise 1** onward:

1. Run its supplied **Setup** code cell with the play button beside the cell. Wait for **notebook ready**.
2. Read the task and replace `todo(...)` in the **Your code** cells. Run a cell with its play button or **Shift+Enter**. Use the separate **Check** cells and collapsed hints as you go.
3. At **Core complete**, either follow the link to **Save and finish** or do the **Optional zoom-in** first. Skipping it does not affect later core exercises.
4. Run **Save and finish** to save your functions and stop Spark. Follow the next-exercise link, or a related deeper investigation, and run that notebook's Setup. The previous notebook can be closed.

Do not use **Run All** on an unfinished exercise. Your saved functions live in **learner_work/**; later notebooks use your code, not an answer filled in behind the scenes. The checkpoint exercise also reuses the stream state saved by Exercise 6. Keep your edited notebooks and this folder if you take a break.

Stuck during class? Use a hint first, then an explicit [catch-up step][recovery] if needed. Completed answers are separate in **solutions/**. An AI assistant may only help with setup and nudges; [you write the exercise answers][agent-guidance].

## Exercises

| Exercise                                                         | Optional zoom-in in the same notebook               |
| ---------------------------------------------------------------- | --------------------------------------------------- |
| [0. Create a SparkSession][exercise-0]     | Core introduction: create, use and stop the session |
| [1. Inspect the inputs][exercise-1]              | Row grain, schemas and data quality                 |
| [2. Clean the keys][exercise-2]               | Expressions, renaming, dropping and immutability    |
| [3. Validate the sales][exercise-3]             | Write tolerant parsing expressions                  |
| [4. Join and aggregate][exercise-4]       | Compare inner and left joins                        |
| [5. Inspect and save the report][exercise-5] | Read the physical plan                              |
| [6. Process arriving files][exercise-6]        | Inspect the running query and progress              |
| [7. Resume from a checkpoint][exercise-7]     | Inspect checkpoint contents and explain recovery    |

Each notebook links to related investigations under **notebooks/deeper/**, with prerequisites stated. These cover CSV schemas and parsing, product tags, duplicate lookup keys, daily aggregates, caching, persisted streaming output and fresh checkpoints. The [browser index][browser-index] groups them by exercise and offers read-only previews.

<!-- Link destinations: define each once and reuse its label above. -->

[java-macos]: TROUBLESHOOTING.md#java-21-macos
[java-windows]: TROUBLESHOOTING.md#windows
[vscode]: https://code.visualstudio.com/download
[python-extension]: https://marketplace.visualstudio.com/items?itemName=ms-python.python
[jupyter-extension]: https://marketplace.visualstudio.com/items?itemName=ms-toolsai.jupyter
[git]: https://git-scm.com/install/
[uv]: https://docs.astral.sh/uv/getting-started/installation/
[uv-windows]: TROUBLESHOOTING.md#uv-on-windows
[uv-macos]: TROUBLESHOOTING.md#uv-on-macos
[hadoop-windows]: TROUBLESHOOTING.md#install-the-windows-components
[parquet-explorer]: https://marketplace.visualstudio.com/items?itemName=AdamViola.parquet-explorer
[api-reference]: API-REFERENCE.md
[troubleshooting]: TROUBLESHOOTING.md
[instructor-notes]: author/README.md
[sparse-checkout]: https://git-scm.com/docs/git-sparse-checkout
[lab-download]: https://github.com/dannyscodecorner/mastering-pyspark/releases/latest/download/pyspark-labs.zip
[exercise-0]: notebooks/00-spark-session.ipynb
[kernel-help]: TROUBLESHOOTING.md#vs-code-cells-and-kernels
[recovery]: RECOVERY.md
[agent-guidance]: AGENTS.md
[exercise-1]: notebooks/01-inspect.ipynb
[exercise-2]: notebooks/02-clean-keys.ipynb
[exercise-3]: notebooks/03-validate.ipynb
[exercise-4]: notebooks/04-join-aggregate.ipynb
[exercise-5]: notebooks/05-save-report.ipynb
[exercise-6]: notebooks/06-streaming.ipynb
[exercise-7]: notebooks/07-checkpoint.ipynb
[browser-index]: index.html
[parquet-demo]: https://github.com/adamviola/parquet-explorer/raw/HEAD/iris.gif
