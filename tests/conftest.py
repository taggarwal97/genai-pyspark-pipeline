import ctypes
import os
import sys
from pathlib import Path

if os.name == "nt" and sys.version_info[:2] not in ((3, 10), (3, 11)):
    raise RuntimeError(
        "Unsupported Python version for PySpark on Windows. "
        "This project requires Python 3.10 or 3.11 for running tests on Windows. "
        "Please install a supported Python runtime and recreate the virtual environment."
    )

ROOT_DIR = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT_DIR))

import pytest
from pyspark.sql import SparkSession


def _get_windows_short_path(path: str) -> str:
    """Return the short (8.3) Windows path for the given path, if available."""
    if os.name != "nt":
        return path

    buffer = ctypes.create_unicode_buffer(260)
    result = ctypes.windll.kernel32.GetShortPathNameW(path, buffer, len(buffer))
    if result == 0:
        return path
    return buffer.value


def _validate_windows_hadoop_home() -> None:
    if os.name != "nt":
        return

    hadoop_home = os.environ.get("HADOOP_HOME")
    if not hadoop_home:
        raise RuntimeError(
            "Windows PySpark requires HADOOP_HOME and winutils.exe. "
            "Set HADOOP_HOME to a local Hadoop root containing 'bin\\winutils.exe', "
            "then rerun tests."
        )

    hadoop_home_path = Path(hadoop_home)
    winutils_candidates = [
        hadoop_home_path / "bin" / "winutils.exe",
        hadoop_home_path / "winutils.exe",
    ]
    if not any(path.exists() for path in winutils_candidates):
        raise RuntimeError(
            f"Unable to locate winutils.exe under HADOOP_HOME={hadoop_home}. "
            "Put a matching winutils.exe in 'bin\\winutils.exe' and rerun tests."
        )


@pytest.fixture(scope="session")
def spark():
    _validate_windows_hadoop_home()
    """Create a shared SparkSession for the test session."""
    python_path = sys.executable
    short_python_path = _get_windows_short_path(python_path)

    local_dir = Path.cwd() / "tmp_spark"
    local_dir.mkdir(parents=True, exist_ok=True)
    short_local_dir = _get_windows_short_path(str(local_dir))

    os.environ["PYSPARK_PYTHON"] = short_python_path
    os.environ["PYSPARK_DRIVER_PYTHON"] = short_python_path
    os.environ["SPARK_LOCAL_DIRS"] = short_local_dir

    builder = (
        SparkSession.builder
        .master("local[1]")
        .appName("pytest-spark")
        .config("spark.ui.enabled", "false")
        .config("spark.sql.shuffle.partitions", "2")
        .config("spark.local.dir", short_local_dir)
        .config("spark.driver.bindAddress", "127.0.0.1")
        .config("spark.pyspark.python", short_python_path)
        .config("spark.pyspark.driver.python", short_python_path)
        .config("spark.executorEnv.PYSPARK_PYTHON", short_python_path)
        .config("spark.executorEnv.PYSPARK_DRIVER_PYTHON", short_python_path)
        .config("spark.executorEnv.SPARK_LOCAL_DIRS", short_local_dir)
    )
    spark_session = builder.getOrCreate()
    yield spark_session
    spark_session.stop()
