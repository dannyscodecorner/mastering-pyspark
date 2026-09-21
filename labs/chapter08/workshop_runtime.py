"""Local workshop setup; keep environment choices out of pipeline.py."""

import atexit
import os
from pathlib import Path
import re
import shutil
import subprocess
import sys
from uuid import uuid4

PROJECT_ROOT = Path(__file__).resolve().parent
DATA_ROOT = PROJECT_ROOT / "data"


def spark_path(path):
    """Hadoop accepts absolute paths with forward slashes, including C:/ on Windows.

    Do not URL-encode these: Spark treats encoded spaces in Path strings literally.
    """
    return Path(path).resolve().as_posix()


def new_run(prefix="run"):
    root = PROJECT_ROOT / "runs" / f"{prefix}-{uuid4().hex[:10]}"
    root.mkdir(parents=True, exist_ok=False)
    return root


def java_version():
    java_home = os.environ.get("JAVA_HOME")
    java = (
        str(Path(java_home) / "bin" / ("java.exe" if os.name == "nt" else "java"))
        if java_home else shutil.which("java")
    )
    if not java:
        raise RuntimeError("Install JDK 21, then reopen VS Code. See README.md: Java.")
    try:
        result = subprocess.run(
            [java, "-version"], capture_output=True, text=True, timeout=15, check=True
        )
    except (OSError, subprocess.SubprocessError) as exc:
        raise RuntimeError("Java could not start. Check JAVA_HOME and PATH; see README.md.") from exc
    version = re.search(r'version "(\d+)', result.stderr + result.stdout)
    if not version or int(version[1]) not in {17, 21, 25}:
        raise RuntimeError("This Spark 4.2 project needs Java 17, 21 or 25. Use JDK 21 for the workshop.")
    return int(version[1])


def create_spark(run_root):
    """Start a local session owned by this exercise, using this Python on workers."""
    if sys.version_info[:2] != (3, 12):
        raise RuntimeError("Use the project's Python 3.12: run with uv, or select .venv as the kernel.")
    java_version()
    from pyspark.sql import SparkSession

    if SparkSession.getActiveSession() is not None:
        raise RuntimeError("A SparkSession is already active. Stop it before starting a fresh lab run.")
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
    atexit.register(spark.stop)
    return spark


def finish_query(query, timeout=120):
    """Wait for a bounded AvailableNow run and stop it if it fails or times out."""
    try:
        if not query.awaitTermination(timeout):
            raise TimeoutError(f"The setup check did not finish within {timeout} seconds.")
    finally:
        if query.isActive:
            query.stop()
