"""Check actionable Windows setup failures without requiring native binaries on the host."""

import os
import unittest
from pathlib import Path
from unittest.mock import MagicMock, patch

from py4j.protocol import Py4JJavaError

from labs import workshop_runtime as runtime


class WindowsHadoopTests(unittest.TestCase):
    """Distinguish missing JNI support, file permissions and successful startup probes."""

    def setUp(self) -> None:
        """Model the Hadoop APIs of a running Spark session on Windows."""
        self.spark = MagicMock()
        self.hadoop = self.spark.sparkContext._jvm.org.apache.hadoop
        self.hadoop.util.VersionInfo.getVersion.return_value = "3.5.0"
        self.hadoop.util.NativeCodeLoader.isNativeCodeLoaded.return_value = True
        self.hadoop.fs.FileUtil.canRead.return_value = True
        platform = patch.object(runtime.sys, "platform", "win32")
        platform.start()
        self.addCleanup(platform.stop)

    def test_non_windows_does_not_require_windows_native_libraries(self) -> None:
        """Keep macOS and Linux on their existing non-native local filesystem paths."""
        with patch.object(runtime.sys, "platform", "darwin"):
            runtime.check_windows_hadoop(self.spark)
        self.hadoop.util.NativeCodeLoader.isNativeCodeLoaded.assert_not_called()

    def test_missing_native_library_explains_the_required_environment(self) -> None:
        """A missing DLL fails before the exercise's first Parquet read."""
        self.hadoop.util.NativeCodeLoader.isNativeCodeLoaded.return_value = False
        with self.assertRaises(RuntimeError) as failure:
            runtime.check_windows_hadoop(self.spark)
        for detail in ("3.5.0", "hadoop.dll", "winutils.exe", "HADOOP_HOME", "PATH", "Restart"):
            self.assertIn(detail, str(failure.exception))
        self.hadoop.fs.FileUtil.canRead.assert_not_called()

    def test_java_failures_keep_the_underlying_cause(self) -> None:
        """Missing winutils and an unresolved access0 symbol both retain their Java cause."""
        calls = (self.hadoop.util.Shell.getWinUtilsPath, self.hadoop.fs.FileUtil.canRead)
        for call in calls:
            with self.subTest(call=call):
                cause = Py4JJavaError("Native setup failed", MagicMock(_target_id="error"))
                call.side_effect = cause
                with self.assertRaisesRegex(
                    RuntimeError, "Windows file-access check failed"
                ) as failure:
                    runtime.check_windows_hadoop(self.spark)
                self.assertIs(failure.exception.__cause__, cause)
                call.side_effect = None

    def test_unreadable_data_is_not_labelled_as_a_missing_dll(self) -> None:
        """A false access result leads to file/permission help rather than binary replacement."""
        self.hadoop.fs.FileUtil.canRead.return_value = False
        with self.assertRaisesRegex(RuntimeError, "cannot read the lab data directory"):
            runtime.check_windows_hadoop(self.spark)

    def test_loaded_support_still_probes_actual_file_access(self) -> None:
        """A loaded-library flag alone does not prove that access0 can be called."""
        runtime.check_windows_hadoop(self.spark)
        self.hadoop.fs.FileUtil.canRead.assert_called_once()

    def test_failed_probe_stops_the_new_session(self) -> None:
        """A failed Setup cell must not leave an active Spark session blocking a retry."""
        with (
            patch.dict(os.environ),
            patch.object(runtime, "java_version", return_value=21),
            patch.object(
                runtime, "check_windows_hadoop", side_effect=RuntimeError("native failure")
            ),
            patch("pyspark.sql.SparkSession") as sessions,
        ):
            sessions.getActiveSession.return_value = None
            builder = sessions.builder
            for method in ("master", "appName", "config"):
                getattr(builder, method).return_value = builder
            builder.getOrCreate.return_value = self.spark
            self.spark.version = "4.2.0"
            with self.assertRaisesRegex(RuntimeError, "native failure"):
                runtime.create_spark(Path("unused-run"))
            self.spark.stop.assert_called_once()


if __name__ == "__main__":
    unittest.main()
