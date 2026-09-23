"""Local workshop setup; keep environment choices out of pipeline.py."""

from __future__ import annotations

import atexit
import os
import re
import shutil
import subprocess
import sys
from pathlib import Path
from typing import TYPE_CHECKING
from uuid import uuid4

if TYPE_CHECKING:
    from pyspark.sql import SparkSession
    from pyspark.sql.streaming import StreamingQuery

PROJECT_ROOT = Path(__file__).resolve().parents[1]
DATA_ROOT = PROJECT_ROOT / "data"


def spark_path(path: str | Path) -> str:
    """Return an absolute Hadoop path with forward slashes, including C:/ on Windows.

    Do not URL-encode these: Spark treats encoded spaces in Path strings literally.
    """
    return Path(path).resolve().as_posix()


def new_run(prefix: str = "run") -> Path:
    """Create a unique run directory without overwriting previous results or checkpoints."""
    root = PROJECT_ROOT / "runs" / f"{prefix}-{uuid4().hex[:10]}"
    root.mkdir(parents=True, exist_ok=False)
    return root


def java_version() -> int:
    """Read Java's major version and report actionable errors for an unsupported runtime."""
    java_home = os.environ.get("JAVA_HOME")
    java = (
        str(Path(java_home) / "bin" / ("java.exe" if os.name == "nt" else "java"))
        if java_home
        else shutil.which("java")
    )
    if not java:
        raise RuntimeError(
            "Install JDK 21, then reopen VS Code. See docs/TROUBLESHOOTING.md: Java."
        )
    try:
        result = subprocess.run(
            [java, "-version"], capture_output=True, text=True, timeout=15, check=True
        )
    except (OSError, subprocess.SubprocessError) as exc:
        raise RuntimeError(
            "Java could not start. Check JAVA_HOME and PATH; see docs/TROUBLESHOOTING.md."
        ) from exc
    version = re.search(r'version "(\d+)', result.stderr + result.stdout)
    if not version or int(version[1]) not in {17, 21, 25}:
        raise RuntimeError(
            "This Spark 4.2 project needs Java 17, 21 or 25. Use JDK 21 for the workshop."
        )
    return int(version[1])


def check_windows_hadoop(spark: SparkSession) -> None:
    """Check Windows native loading and the same file-access API used by Parquet reads."""
    if sys.platform != "win32":
        return
    from py4j.protocol import Py4JJavaError

    jvm = spark.sparkContext._jvm
    hadoop = jvm.org.apache.hadoop
    version = hadoop.util.VersionInfo.getVersion()
    guidance = (
        f"This Spark session uses Hadoop {version}. It needs a matching Windows build "
        "containing hadoop.dll, winutils.exe and their runtime dependencies. "
        "Set HADOOP_HOME to that build and include its bin directory on PATH before "
        "starting VS Code. Restart the notebook kernel after correcting the environment. "
        "See docs/TROUBLESHOOTING.md#windows-native-hadoop."
    )
    if not hadoop.util.NativeCodeLoader.isNativeCodeLoaded():
        raise RuntimeError("Hadoop's Windows native library could not be loaded. " + guidance)
    try:
        hadoop.util.Shell.getWinUtilsPath()
        readable = hadoop.fs.FileUtil.canRead(jvm.java.io.File(spark_path(DATA_ROOT)))
    except Py4JJavaError as exc:
        raise RuntimeError("Hadoop's Windows file-access check failed. " + guidance) from exc
    if not readable:
        raise RuntimeError(
            f"Hadoop cannot read the lab data directory: {DATA_ROOT}. "
            "Check that the full lab was extracted and that this user can read it."
        )


def create_spark(run_root: Path) -> SparkSession:
    """Start a local session owned by this exercise, using this Python on workers."""
    if sys.version_info[:2] != (3, 12):
        raise RuntimeError(
            "Use the project's Python 3.12: run with uv, or select .venv as the kernel."
        )
    java_version()
    # Keep this import lazy so Python and Java preflight failures stay readable.
    from pyspark.sql import SparkSession

    if SparkSession.getActiveSession() is not None:
        raise RuntimeError(
            "A SparkSession is already active. Stop it before starting a fresh lab run."
        )
    os.environ["PYSPARK_PYTHON"] = sys.executable
    os.environ["SPARK_LOCAL_IP"] = "127.0.0.1"
    spark = (
        SparkSession.builder.master("local[2]")
        .appName("DCC PySpark workshop")
        .config("spark.pyspark.python", sys.executable)
        .config("spark.driver.host", "127.0.0.1")
        .config("spark.driver.bindAddress", "127.0.0.1")
        .config("spark.sql.session.timeZone", "UTC")
        .config("spark.sql.shuffle.partitions", "2")  # Tiny exercise, not production advice.
        .config("spark.sql.warehouse.dir", spark_path(Path(run_root) / "warehouse"))
        .config("spark.ui.enabled", "false")
        .config("spark.ui.showConsoleProgress", "false")
        .getOrCreate()
    )
    if spark.version != "4.2.0":
        spark.stop()
        raise RuntimeError("Expected Spark 4.2.0. Check for an old SPARK_HOME override.")
    spark.sparkContext.setLogLevel("ERROR")
    try:
        check_windows_hadoop(spark)
    except Exception:
        spark.stop()
        raise
    atexit.register(spark.stop)
    return spark


def finish_query(query: StreamingQuery, timeout: int = 120) -> None:
    """Wait for a bounded AvailableNow run and stop it if it fails or times out."""
    try:
        if not query.awaitTermination(timeout):
            raise TimeoutError(f"The setup check did not finish within {timeout} seconds.")
    finally:
        if query.isActive:
            query.stop()
