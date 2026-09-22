# Working with PySpark — guided lab

Read and clean Parquet data, build a sales report, then run the same pipeline as files arrive.

## Dependencies

1. **Java 21 (JDK)** — follow the [Java installation steps](TROUBLESHOOTING.md#java) for your operating system.
2. **[VS Code](https://code.visualstudio.com/download)** — enable the **[Python](https://marketplace.visualstudio.com/items?itemName=ms-python.python)** and **[Jupyter](https://marketplace.visualstudio.com/items?itemName=ms-toolsai.jupyter)** extensions.
3. **[Git](https://git-scm.com/install/)** — needed to clone the repository; optional if you download the ZIP instead.
4. **Python 3.12 and [uv](https://docs.astral.sh/uv/getting-started/installation/)** — install uv; it downloads Python 3.12 during setup if needed.

The setup below installs PySpark 4.2.0 and the notebook kernel into the lab's environment.

## 1. Open the lab

Clone the repository and open **mastering-pyspark/labs** in VS Code. Skip cloning if you already have it.

```text
git clone https://github.com/dannyscodecorner/mastering-pyspark.git
```

Alternatively, [download the lab from the latest GitHub Release](https://github.com/dannyscodecorner/mastering-pyspark/releases/latest/download/pyspark-labs.zip), extract it and open the **labs** folder inside.

## 2. Run setup

After installing the dependencies, reopen VS Code normally. In its terminal, make sure you are in the **labs** folder and run:

```text
uv sync --locked --group notebook
uv run --locked check_setup.py
```

Look for **Setup check passed**. Do this before class so the downloads are ready.

**Windows:** native Windows setup is not yet validated. Read the [Windows notes](TROUBLESHOOTING.md#windows-status) before class.

## 3. Start the exercises

Open [hands_on.py](hands_on.py) and use **Run Cell**. Select the project's **.venv** as the kernel, run the **Setup** cell, then work through the exercises in order.

Prefer a notebook? Open [hands-on.ipynb](hands-on.ipynb) with the same kernel. The [executed walkthrough](hands-on.html) shows the expected results.

Using an AI assistant? Start it in this **labs** folder. The [agent guidance](AGENTS.md) allows setup help and hints; you write the exercise answers.

## Explore Parquet files — optional

Install [Parquet Explorer](https://marketplace.visualstudio.com/items?itemName=AdamViola.parquet-explorer) and open a `part-*.parquet` file inside `data/sales.parquet` or `data/products.parquet`.

Need help? See [troubleshooting](TROUBLESHOOTING.md). Teaching, data and maintenance details are in the [instructor notes](author/README.md).
