# Working with PySpark — guided lab

Read and clean Parquet data, build a sales report, then run the same pipeline as files arrive.

## 1. Open the lab

Clone the repository and open **mastering-pyspark/labs** in VS Code. Skip cloning if you already have it.

```text
git clone https://github.com/dannyscodecorner/mastering-pyspark.git
```

Alternatively, [download the lab from the latest GitHub Release](https://github.com/dannyscodecorner/mastering-pyspark/releases/latest/download/pyspark-labs.zip), extract it and open the **labs** folder inside.

## 2. Run setup

**Windows:** open PowerShell with **Run as administrator** and install JDK 21:

```powershell
winget install --id EclipseAdoptium.Temurin.21.JDK --exact
```

**macOS:** install [SDKMAN! through Homebrew](https://github.com/sdkman/homebrew-tap):

```sh
brew tap sdkman/tap
brew install sdkman-cli
```

Add these two lines once at the end of `~/.zshrc`:

```sh
export SDKMAN_DIR="$(brew --prefix sdkman-cli)/libexec"
[[ -s "$SDKMAN_DIR/bin/sdkman-init.sh" ]] && source "$SDKMAN_DIR/bin/sdkman-init.sh"
```

Then load SDKMAN, install Temurin 21 and make it your default Java:

```sh
source ~/.zshrc
sdk install java 21.0.12-tem
sdk default java 21.0.12-tem
```

**Linux:** install [JDK 21](https://adoptium.net/temurin/releases/?version=21).

Reopen VS Code normally and enable its **Python** and **Jupyter** extensions. In the VS Code terminal:

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
