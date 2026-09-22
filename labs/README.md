# Working with PySpark — guided lab

Read and clean Parquet data, build a sales report, then run the same pipeline as files arrive.

## Dependencies

1. **Java 21 (JDK)** — follow the [Java installation steps](TROUBLESHOOTING.md#java) for your operating system.
2. **[VS Code](https://code.visualstudio.com/download)** — install and enable the **[Python](https://marketplace.visualstudio.com/items?itemName=ms-python.python)** and **[Jupyter](https://marketplace.visualstudio.com/items?itemName=ms-toolsai.jupyter)** extensions.
3. **[Git](https://git-scm.com/install/)** — needed to clone the repository; optional if you download the ZIP instead.
4. **Python 3.12 and [uv](https://docs.astral.sh/uv/getting-started/installation/)** — install uv ([Windows steps](TROUBLESHOOTING.md#uv-on-windows)); it downloads Python 3.12 during setup if needed.

The setup below installs PySpark 4.2.0 and the notebook kernel into the lab's environment.

## 1. Open the lab

In a terminal, clone the repository. Skip this if you already have it:

```text
git clone https://github.com/dannyscodecorner/mastering-pyspark.git
```

In VS Code, choose **File → Open Folder** and select **mastering-pyspark/labs**. You should see `pyproject.toml`, `hands_on.py` and the `data` folder in the Explorer sidebar.

Alternatively, [download the lab from the latest GitHub Release](https://github.com/dannyscodecorner/mastering-pyspark/releases/latest/download/pyspark-labs.zip), extract it and open the **labs** folder inside.

## 2. Create the virtual environment

After installing the dependencies, reopen VS Code normally. Choose **Terminal → New Terminal** and make sure the terminal is in the **labs** folder. Run:

```text
uv sync --locked --group notebook
```

This creates **.venv** inside **labs**: the lab's own Python environment and packages. It downloads Python 3.12 if needed and installs the locked dependencies, including PySpark and the notebook kernel. Wait for the command to finish.

Then check the environment:

```text
uv run --locked check_setup.py
```

`uv run` uses this `.venv` automatically; you do not need to activate it in the terminal. Wait for **Setup check passed** before continuing. Do this before class so the downloads are ready.

**Windows:** native Windows setup is not yet validated. Read the [Windows notes](TROUBLESHOOTING.md#windows-status) before class.

## 3. Install the VS Code extensions

`uv sync` installs the Python packages in `.venv`. The editor also needs its own **Python** and **Jupyter** extensions installed.

1. Open the **Extensions** view: **Ctrl+Shift+X** on Windows/Linux or **Cmd+Shift+X** on macOS.
2. Search for `@id:ms-python.python`. Open **Python** by **Microsoft** and click **Install** if it is missing.
3. Search for `@id:ms-toolsai.jupyter`. Open **Jupyter** by **Microsoft** and click **Install**. If either extension is already installed but disabled, choose **Enable**.
4. Wait for installation to finish and follow any **Restart Extensions** or reload prompt.

If VS Code shows a notification recommending **Jupyter**, its **Install** button does the same thing. A menu entry saying **Install the Jupyter extension** means this editor setup is still missing.

Reopen [hands_on.py](hands_on.py). You should now see **Run Cell** links above the `# %%` code-cell markers. If they are still missing, see [VS Code setup help](TROUBLESHOOTING.md#vs-code-cells-and-kernels).

## 4. Select the lab's Python in VS Code

Open [hands_on.py](hands_on.py) from the Explorer sidebar. Open the **Command Palette** with **Ctrl+Shift+P** on Windows/Linux or **Cmd+Shift+P** on macOS. Run **Python: Select Interpreter** and choose the **Python 3.12** environment in the lab's **.venv** folder.

Check the interpreter's path belongs to this lab:

| Operating system | Python executable inside `labs` |
| ---------------- | ------------------------------- |
| Windows          | `.venv\Scripts\python.exe`      |
| macOS / Linux    | `.venv/bin/python`              |

If `.venv` is missing from the list, see [VS Code setup help](TROUBLESHOOTING.md#vs-code-cells-and-kernels).

## 5. Run the first cell, then the exercises

The `# %%` lines in `hands_on.py` divide the file into cells. Each code cell has a **Run Cell** link above it. Cells share a Python session, so later cells can use variables created earlier.

1. Find **Setup** near the top of the file. Click **Run Cell** above the following code cell, which starts with `from decimal import Decimal`.
2. VS Code opens the **Python Interactive** window. If prompted for a kernel, choose **Python Environments → .venv**. Check the kernel shown in the window's upper-right corner belongs to the same environment selected above. To change it, click its name, then **Select Another Kernel → Python Environments → .venv**.
3. Wait for the setup cell to finish. Its output should include `Spark 4.2.0; inputs: data; fresh run prepared`.
4. Go to **Exercise 1 — Inspect the inputs** and click **Run Cell** above its code. The schemas and tables appear in the Interactive window. Read each exercise and run its cells in order, waiting for each cell to finish.
5. At the end, run the **Finish the exercise** cell to stop Spark.

If you restart or change the kernel, run **Setup** and the earlier exercise cells again before continuing. Missing **Run Cell**, or an import error? See [VS Code setup help](TROUBLESHOOTING.md#vs-code-cells-and-kernels).

**Prefer a notebook?** Open [hands-on.ipynb](hands-on.ipynb), click **Select Kernel** (or the current kernel name) at the top right, and choose the same `.venv` under **Python Environments**; use **Select Another Kernel** if needed. Run the first code cell under **Setup** with the play button beside that cell, then continue one cell at a time. The [executed walkthrough](hands-on.html) shows the expected results.

Using an AI assistant? Start it in this **labs** folder. The [agent guidance](AGENTS.md) allows setup help and hints; you write the exercise answers.

## Explore Parquet files — optional

Install [Parquet Explorer](https://marketplace.visualstudio.com/items?itemName=AdamViola.parquet-explorer) and open a `part-*.parquet` file inside `data/sales.parquet` or `data/products.parquet`.

Need help? See [troubleshooting](TROUBLESHOOTING.md). Teaching, data and maintenance details are in the [instructor notes](author/README.md).
