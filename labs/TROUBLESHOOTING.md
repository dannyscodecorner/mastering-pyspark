# Lab setup and troubleshooting

[Back to the lab](README.md)

## Java

Use a 64-bit JDK matching your computer, such as [Eclipse Temurin 21](https://adoptium.net/temurin/releases/?version=21).

On Windows, open PowerShell with **Run as administrator**:

```powershell
winget install --id EclipseAdoptium.Temurin.21.JDK --exact
```

If WinGet is unavailable, use the [Windows installer](https://adoptium.net/installation/windows/) and enable its PATH and `JAVA_HOME` options. If `JAVA_HOME` is set, it should name the JDK directory, not its `bin` directory. After installation, close the Administrator terminal and fully reopen VS Code normally. Run:

```text
java -version
```

It should report version 21 for this workshop. Spark 4.2 also supports Java 17 and 25, but this lab's observed validation uses 21. uv manages Python, not Java.

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

## Other ways to run the lesson

The README's setup command includes the kernel dependencies for VS Code's Python Interactive window and notebooks. Use the project's `.venv` in both, and run cells from the top.

To run the entire worked reference as a script instead:

```text
uv run --locked hands_on.py
```

If you interrupt a run, call `spark.stop()` before rerunning setup or switching between interactive copies. Each run creates its own output and checkpoint directories under `runs/`; prepared inputs and previous runs stay unchanged.
