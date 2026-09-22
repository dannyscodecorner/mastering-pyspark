# Lab setup and troubleshooting

[Back to the lab](README.md)

## Java

Use a 64-bit JDK matching your computer, such as [Eclipse Temurin 21](https://adoptium.net/temurin/releases/?version=21).

### Windows

Open PowerShell with **Run as administrator**:

```powershell
winget install --id EclipseAdoptium.Temurin.21.JDK --exact
```

If WinGet is unavailable, use the [Windows installer](https://adoptium.net/installation/windows/) and enable its PATH and `JAVA_HOME` options. If `JAVA_HOME` is set, it should name the JDK directory, not its `bin` directory. After installation, close the Administrator terminal and fully reopen VS Code normally. Run:

```text
java -version
```

It should report version 21 for this workshop. Spark 4.2 also supports Java 17 and 25, but this lab's observed validation uses 21. uv manages Python, not Java.

### macOS

Install [Homebrew](https://brew.sh/) first if `brew` is unavailable. Then install [SDKMAN! through its Homebrew tap](https://github.com/sdkman/homebrew-tap):

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

The initialization lines use Homebrew's SDKMAN directory; the usual `~/.sdkman` path is for a different installation method.

The instructions assume Zsh, the default macOS shell. If you use Bash, put the initialization lines in `~/.bash_profile` and source that file instead. If `sdk` is missing in a new terminal, check that the initialization lines are in your shell's startup file.

In the VS Code terminal, check the selected JDK:

```sh
sdk current java
java -version
```

If another version is selected, run `sdk use java 21.0.12-tem` for the current terminal or `sdk default java 21.0.12-tem` for future terminals too. SDKMAN sets `JAVA_HOME`; an older hard-coded setting later in your shell startup file can override it.

The command pins Temurin 21. If that patch becomes unavailable, use `sdk list java` and choose an available Temurin **21** identifier. A bare `sdk install java` selects SDKMAN's current default major version, which may differ from the workshop's. See [SDKMAN usage](https://sdkman.io/usage/).

### Linux

Install a 64-bit [JDK 21](https://adoptium.net/temurin/releases/?version=21) matching your computer. Reopen VS Code and check `java -version` in its terminal; it should report version 21.

## uv on Windows

Open **PowerShell** and install uv using [WinGet](https://docs.astral.sh/uv/getting-started/installation/#winget):

```powershell
winget install --id astral-sh.uv --exact
```

Close PowerShell and fully exit VS Code. Reopen VS Code, choose **Terminal → New Terminal**, and check that uv is available:

```powershell
uv --version
```

This should print the installed uv version. If WinGet is unavailable, use the [official Windows installer](https://docs.astral.sh/uv/getting-started/installation/#standalone-installer).

Then continue with [creating the lab's virtual environment](README.md#2-create-the-virtual-environment).

## Windows status

**The full lab has not yet been validated on native Windows.** The instructor has confirmed the Java installation command above; the setup check is still pending. Jupyter in VS Code supports Windows; the remaining risk is Spark's Hadoop filesystem support. The bundled Spark 4.2 distribution uses Hadoop 3.5.0. Hadoop's [Windows build documentation](https://github.com/apache/hadoop/blob/rel/release-3.5.0/BUILDING.txt#L615-L618) states that its native Windows components are required. Python, uv and Java alone may therefore be insufficient for Parquet/checkpoint writes on a clean machine.

Before distributing a native Windows setup as class-ready, the instructor must supply or approve a matching Hadoop 3.5.0 Windows build (`winutils.exe` and `hadoop.dll`, with its required runtime libraries), configure `HADOOP_HOME` and its `bin` directory on PATH, and run the setup check on a representative attendee machine. This project does not download unverified native binaries. Do not mix binaries from older Hadoop releases.

If native setup proves impractical, the same uv project can be evaluated in WSL without Docker. WSL has not been tested here and is not a prerequisite currently assumed for attendees. Keep this deployment choice out of the teaching slides.

## Common problems

- **Java missing or wrong version:** install JDK 21, correct `JAVA_HOME`/PATH and reopen VS Code. Run `java -version` again.
- **Wrong Python or kernel:** use `uv run`, or select the project's `.venv` in VS Code. System Python and a previously selected notebook kernel may differ.
- **Unexpected Spark version:** check for an old `SPARK_HOME` override. This project uses the Spark bundled with its locked PySpark dependency.
- **`winutils`, `NativeIO$Windows` or `hadoop.dll` errors:** this is the native Windows dependency issue above. Keep the complete setup-check output for the instructor; a passing `spark.range(...).show()` is not sufficient.
- **Hard-link or file permission error:** keep the project in a writable local NTFS/APFS/ext4 folder. The arrival publisher requires hard-link support.
- **Interrupted interactive run:** stop the query or call `spark.stop()` before running setup again. The setup cell creates a new run rather than deleting old checkpoint files.

Setup references: [uv projects](https://docs.astral.sh/uv/guides/projects/), [uv with Jupyter](https://docs.astral.sh/uv/guides/integration/jupyter/), [VS Code Python cells](https://code.visualstudio.com/docs/python/jupyter-support-py), [Spark 4.2 requirements](https://spark.apache.org/docs/4.2.0/index.html).

## Project folder and downloads

Use a writable local folder. On Windows, choose a short path such as `C:/work/mastering-pyspark` on an NTFS drive. Open the **labs** folder containing `pyproject.toml` in VS Code so its terminal, environment and extension recommendations use the lab project.

The chapter 08 slides link to the `pyspark-labs.zip` attachment on the latest GitHub Release. Extract the entire archive, including the data and project files, and open its **labs** folder. This is an alternative to cloning the repository.

## Environment and setup check

The project selects Python **3.12** and locks PySpark to **4.2.0**. uv creates the `.venv` and can download Python 3.12 if needed. The first setup needs network access and downloads Spark's JVM libraries as part of PySpark; do this before class. No shell activation is needed for `uv run`.

The setup check must finish with **Setup check passed**. It tests a Python worker, Parquet input/output, atomic arrival publication, stateful streaming, checkpoint restart and a streaming Parquet sink. The small fixture is the actual workshop data, not a test that only starts Spark.

## VS Code cells and kernels

- **The menu says "Install the Jupyter extension":** click that item or **Install** in the Jupyter recommendation notification. This installs the VS Code extension; `uv sync` installs the Python kernel packages separately. Follow [Install the VS Code extensions](README.md#3-install-the-vs-code-extensions), then reopen `hands_on.py`.
- **No Run Cell links:** open `hands_on.py` in the editor and check the language mode at the bottom right says **Python**. In the Extensions view, check that **Python** and **Jupyter** are installed and enabled for this workspace. If the folder is in Restricted Mode, review [Workspace Trust](https://code.visualstudio.com/docs/editing/workspaces/workspace-trust); enable execution only for a course copy you trust. Run **Developer: Reload Window** from the Command Palette after enabling extensions. Also check that `editor.codeLens` and `jupyter.interactiveWindow.codeLens.enable` are enabled in Settings.
- **No .venv to select:** finish `uv sync --locked --group notebook` in **labs**, then run **Developer: Reload Window**. Open `hands_on.py` and use **Python: Select Interpreter** again. In the Interactive window or notebook, use **Select Another Kernel → Python Environments** to see environments outside the recently used list.
- **Setup passed, but a cell cannot import pyspark or ipykernel:** the Interactive window may be using a different Python from the terminal. Choose the lab's `.venv` in its kernel picker and run the Setup cell again. Selecting the editor's interpreter alone does not change an already running kernel.
- **NameError for spark or an earlier variable:** run the Setup cell and preceding exercise cells in the same kernel. A new or restarted kernel has no variables from the previous session.

See the official [Python Interactive window guide](https://code.visualstudio.com/docs/python/jupyter-support-py) and [kernel selection guide](https://code.visualstudio.com/docs/datascience/jupyter-kernel-management).

## Other ways to run the lesson

The README's setup command includes the kernel dependencies for VS Code's Python Interactive window and notebooks. Use the project's `.venv` in both, and run cells from the top.

To run the entire worked reference as a script instead:

```text
uv run --locked hands_on.py
```

If you interrupt a run, call `spark.stop()` before rerunning setup or switching between interactive copies. Each run creates its own output and checkpoint directories under `runs/`; prepared inputs and previous runs stay unchanged.
