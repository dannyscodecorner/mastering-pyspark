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

**Native Windows currently has a confirmed filesystem blocker on the instructor’s test machine.** The notebook kernel and Spark start, but Exercise 1 fails at its first Parquet read with `NativeIO$Windows.access0`. The full lab is not yet validated on native Windows. Starting Spark or running `spark.range(...).show()` does not establish that file access works.

## Windows native Hadoop

The locked Spark 4.2.0 distribution includes Hadoop 3.5.0 Java libraries. Native Windows also needs a matching `hadoop.dll`, `winutils.exe` and the runtime libraries required by that build. uv and the JDK installer do not install these. Hadoop’s [Windows build instructions](https://github.com/apache/hadoop/blob/rel/release-3.5.0/BUILDING.txt#L615-L618) describe the native components as required.

### `UnsatisfiedLinkError: NativeIO$Windows.access0`

The Java runtime cannot resolve a native Windows file-access function. The Hadoop DLL may be absent, incompatible with the loaded Hadoop/Java architecture, or unable to load because a dependency is missing. `winutils.exe` alone cannot supply this DLL function. Hadoop’s [file-access implementation](https://github.com/apache/hadoop/blob/rel/release-3.5.0/hadoop-common-project/hadoop-common/src/main/java/org/apache/hadoop/fs/FileUtil.java) calls it while checking local paths, before Parquet rows are read.

1. In the VS Code PowerShell terminal, inspect the current environment:

   ```powershell
   $env:HADOOP_HOME
   where.exe winutils
   where.exe hadoop.dll
   ```

   Blank `HADOOP_HOME` or a “could not find files” result is a useful clue. Finding the files does not prove that Java can load them or that their versions match.

2. Use an instructor-approved Hadoop **3.5.0** Windows build matching the Java architecture, including both native files and its runtime dependencies. **This repository does not yet supply a validated build or download link.** The instructor must provide and test one before native Windows can be the workshop default. Do not mix files from unrelated Hadoop releases.

3. With that build installed, set `HADOOP_HOME` to its root directory and add its `bin` directory to your user PATH. For example, a build at `C:\tools\hadoop-3.5.0` would have these files:

   ```text
   C:\tools\hadoop-3.5.0\bin\hadoop.dll
   C:\tools\hadoop-3.5.0\bin\winutils.exe
   ```

   Use your actual installation location. Do not copy the DLL into the JDK directory. Fully exit VS Code and reopen it after changing user environment variables; the running Java process will not pick up a new PATH. Restarting only the failed cell is insufficient.

4. From **labs**, run `uv run --locked check_setup.py`. Require **Setup check passed**, which includes Parquet reads/writes and streaming checkpoint recovery, before resuming the notebook. The shared session helper now detects missing native support during Setup and keeps the underlying Java error when a file-access call fails.

If the files are present but loading still fails, keep the full setup-check output and check the build’s architecture and dependent DLLs. Running VS Code as administrator does not supply a missing native function. Keep your exercise answers and existing checkpoints; changing the read expression or deleting data will not repair this dependency.

The same uv project could be evaluated in WSL without Docker if native setup proves impractical. WSL has not been tested here and remains a separate environment choice, not a required or automatic fallback.

## Common problems

- **Java missing or wrong version:** install JDK 21, correct `JAVA_HOME`/PATH and reopen VS Code. Run `java -version` again.
- **Wrong Python or kernel:** use `uv run`, or select the project's `.venv` in VS Code. System Python and a previously selected notebook kernel may differ.
- **Unexpected Spark version:** check for an old `SPARK_HOME` override. This project uses the Spark bundled with its locked PySpark dependency.
- **`winutils`, `NativeIO$Windows` or `hadoop.dll` errors:** follow [Windows native Hadoop](#windows-native-hadoop). Keep the complete setup-check output for the instructor; a passing `spark.range(...).show()` is not sufficient.
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

- **The notebook opens as text or has no play buttons:** install or enable Microsoft's Python and Jupyter extensions. Follow [Install the VS Code extensions](README.md#3-install-the-vs-code-extensions), reload VS Code if prompted, and open `notebooks/00-spark-session.ipynb`. The `.py` authoring file is not the participant entry point.
- **No .venv to select:** finish `uv sync --locked --group notebook` in **labs**, then run **Developer: Reload Window**. In the notebook's kernel picker, use **Select Another Kernel → Python Environments**. Choose `labs/.venv/Scripts/python.exe` on Windows or `labs/.venv/bin/python` on macOS/Linux.
- **Imports fail after setup passed in the terminal:** check the notebook's kernel, not just the editor's Python interpreter. Select this lab's `.venv`, restart the kernel and run the notebook's Setup cell.
- **`todo(...)` raises NotImplementedError:** this is an unfinished exercise, not an installation error. Replace the marked call with your own code; use the task's hint if needed.
- **A saved function is missing:** run **Save and finish** in the preceding core exercise. If you need to catch up, use the explicit [recovery instructions](RECOVERY.md).
- **NameError after restarting a kernel:** cells in that notebook share state. Run its Setup and earlier completed cells before continuing. Each exercise notebook loads its prerequisites from saved files; another notebook's variables are not shared automatically.
- **Spark is already active:** stop this notebook's queries and session using [safe cleanup](RECOVERY.md#stop-safely), then rerun Setup.
- **An arrival was already published, or the checkpoint boundary is wrong:** follow [stream recovery](RECOVERY.md#exercise-6). Do not delete the checkpoint or overwrite already-consumed files.

### Windows: the notebook selected uv's base Python

A path under `AppData/Roaming/uv/python/` in an `ipykernel` error means the notebook selected the base interpreter. The lab kernel should use `labs/.venv/Scripts/python.exe`.

If `.venv` is still missing from **Python Environments**, register it with a recognisable name. In PowerShell, from **labs**, run:

```powershell
uv sync --locked --group notebook
.\.venv\Scripts\python.exe -m ipykernel install --user --name mastering-pyspark-lab --display-name "Mastering PySpark (labs .venv)"
```

Run **Developer: Reload Window**, then **Select Kernel → Select Another Kernel → Jupyter Kernels → Mastering PySpark (labs .venv)**. Exercise 0 prints `sys.executable`; check that it points into this lab's `.venv`. This registers a kernel for the current lab location; rerun the command if you move the folder. See [IPython's kernel installation instructions](https://ipython.readthedocs.io/en/stable/install/kernel_install.html).

If VS Code is in Restricted Mode, review [Workspace Trust](https://code.visualstudio.com/docs/editing/workspaces/workspace-trust) and enable execution only for a course copy you trust.
