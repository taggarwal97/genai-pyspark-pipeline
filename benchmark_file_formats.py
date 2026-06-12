"""Benchmark common file formats with hardware metrics.

This script generates a synthetic DataFrame and writes it to CSV, XLSX, Parquet,
ORC, and Feather formats. For each format it measures:
- file size in MB
- write time in seconds
- read time in seconds
- peak memory usage using tracemalloc
- CPU time using time.process_time
- estimated energy consumption using a 65W TDP baseline

It also prints a comparison table with percentage savings relative to CSV.
"""

from __future__ import annotations

import importlib.util
import time
from pathlib import Path

import numpy as np
import pandas as pd
import tracemalloc


BENCHMARK_DIR = Path("data") / "benchmark_outputs"
BENCHMARK_DIR.mkdir(parents=True, exist_ok=True)

CATEGORIES = ["Electronics", "Clothing", "Home", "Sports", "Books"]
FILE_COUNT = 500_000
CSV_FILENAME = BENCHMARK_DIR / "benchmark.csv"
XLSX_FILENAME = BENCHMARK_DIR / "benchmark.xlsx"
PARQUET_FILENAME = BENCHMARK_DIR / "benchmark.parquet"
ORC_FILENAME = BENCHMARK_DIR / "benchmark.orc"
FEATHER_FILENAME = BENCHMARK_DIR / "benchmark.feather"

CPU_TDP_WATTS = 65.0


def generate_dataframe(n: int) -> pd.DataFrame:
    np.random.seed(42)
    ids = np.arange(1, n + 1, dtype=np.int64)
    names = np.array([f"User_{i:06d}" for i in ids], dtype=object)
    emails = np.char.add(names.astype(str), "@example.com")
    amounts = np.round(np.random.uniform(5.0, 500.0, size=n), 2)
    dates = pd.date_range("2024-01-01", periods=n, freq="min")
    categories = np.random.choice(CATEGORIES, size=n)

    return pd.DataFrame(
        {
            "id": ids,
            "name": names,
            "email": emails,
            "amount": amounts,
            "date": dates,
            "category": categories,
        }
    )


def measure_memory_and_time(func, *args, **kwargs) -> tuple[float, float, float]:
    tracemalloc.start()
    cpu_start = time.process_time()
    wall_start = time.perf_counter()

    result = func(*args, **kwargs)

    cpu_end = time.process_time()
    wall_end = time.perf_counter()
    current, peak = tracemalloc.get_traced_memory()
    tracemalloc.stop()

    return wall_end - wall_start, cpu_end - cpu_start, peak / 1024.0, result


def write_csv(df: pd.DataFrame, path: Path) -> None:
    df.to_csv(path, index=False)


def read_csv(path: Path) -> pd.DataFrame:
    return pd.read_csv(path)


def write_xlsx(df: pd.DataFrame, path: Path) -> None:
    engine = None
    if importlib.util.find_spec("openpyxl") is not None:
        engine = "openpyxl"
    elif importlib.util.find_spec("xlsxwriter") is not None:
        engine = "xlsxwriter"
    else:
        raise ImportError("No Excel engine installed. Install openpyxl or xlsxwriter.")
    df.to_excel(path, index=False, engine=engine)


def read_xlsx(path: Path) -> pd.DataFrame:
    return pd.read_excel(path)


def write_parquet(df: pd.DataFrame, path: Path) -> None:
    engine = None
    if importlib.util.find_spec("pyarrow") is not None:
        engine = "pyarrow"
    elif importlib.util.find_spec("fastparquet") is not None:
        engine = "fastparquet"
    else:
        raise ImportError("No Parquet engine installed. Install pyarrow or fastparquet.")
    df.to_parquet(path, engine=engine, index=False)


def read_parquet(path: Path) -> pd.DataFrame:
    return pd.read_parquet(path)


def write_orc(df: pd.DataFrame, path: Path) -> None:
    if importlib.util.find_spec("pyarrow") is None:
        raise ImportError("No ORC engine installed. Install pyarrow.")
    df.to_orc(path)


def read_orc(path: Path) -> pd.DataFrame:
    return pd.read_orc(path)


def write_feather(df: pd.DataFrame, path: Path) -> None:
    if importlib.util.find_spec("pyarrow") is None:
        raise ImportError("No Feather engine installed. Install pyarrow.")
    df.to_feather(path)


def read_feather(path: Path) -> pd.DataFrame:
    return pd.read_feather(path)


def benchmark_format(
    name: str,
    write_fn,
    read_fn,
    path: Path,
    df: pd.DataFrame,
) -> dict[str, float | str]:
    write_time, write_cpu, write_peak, _ = measure_memory_and_time(write_fn, df, path)
    file_size_mb = path.stat().st_size / 1024**2

    read_time, read_cpu, read_peak, read_df = measure_memory_and_time(read_fn, path)
    if len(read_df) != len(df):
        raise ValueError(f"Read data length mismatch for {name}")

    cpu_time = write_cpu + read_cpu
    peak_memory_kb = max(write_peak, read_peak)
    estimated_energy_wh = cpu_time * CPU_TDP_WATTS / 3600.0

    return {
        "format": name,
        "file_size_mb": round(file_size_mb, 2),
        "write_time_s": round(write_time, 3),
        "read_time_s": round(read_time, 3),
        "cpu_time_s": round(cpu_time, 3),
        "peak_memory_kb": round(peak_memory_kb, 1),
        "energy_wh": round(estimated_energy_wh, 4),
    }


def format_percentage_savings(value: float) -> str:
    return f"{value:.1f}%"


def main() -> None:
    print("Generating synthetic DataFrame with 500,000 rows...")
    df = generate_dataframe(FILE_COUNT)

    formats = [
        ("CSV", write_csv, read_csv, CSV_FILENAME),
        ("XLSX", write_xlsx, read_xlsx, XLSX_FILENAME),
        ("Parquet", write_parquet, read_parquet, PARQUET_FILENAME),
        ("ORC", write_orc, read_orc, ORC_FILENAME),
        ("Feather", write_feather, read_feather, FEATHER_FILENAME),
    ]

    results = []
    for fmt, writer, reader, path in formats:
        print(f"\nBenchmarking {fmt}...")
        if path.exists():
            path.unlink()
        try:
            metrics = benchmark_format(fmt, writer, reader, path, df)
            results.append(metrics)
            print(f"  {fmt} completed: {metrics['file_size_mb']} MB, "
                  f"write {metrics['write_time_s']}s, read {metrics['read_time_s']}s")
        except Exception as exc:
            results.append(
                {
                    "format": fmt,
                    "file_size_mb": "NA",
                    "write_time_s": "NA",
                    "read_time_s": "NA",
                    "cpu_time_s": "NA",
                    "peak_memory_kb": "NA",
                    "energy_wh": "NA",
                    "error": str(exc),
                }
            )
            print(f"  {fmt} failed: {exc}")

    result_df = pd.DataFrame(results)
    csv_row = result_df[result_df["format"] == "CSV"].iloc[0]

    savings = []
    for _, row in result_df.iterrows():
        if row["format"] == "CSV" or row.get("error") is not None:
            savings.append({
                "format": row["format"],
                "size_savings": "0.0%",
                "write_time_savings": "0.0%",
                "read_time_savings": "0.0%",
                "energy_savings": "0.0%",
            })
            continue

        size_savings = (csv_row["file_size_mb"] - row["file_size_mb"]) / csv_row["file_size_mb"] * 100
        write_savings = (csv_row["write_time_s"] - row["write_time_s"]) / csv_row["write_time_s"] * 100
        read_savings = (csv_row["read_time_s"] - row["read_time_s"]) / row["read_time_s"] * 100
        energy_savings = (csv_row["energy_wh"] - row["energy_wh"]) / csv_row["energy_wh"] * 100

        savings.append(
            {
                "format": row["format"],
                "size_savings": format_percentage_savings(size_savings),
                "write_time_savings": format_percentage_savings(write_savings),
                "read_time_savings": format_percentage_savings(read_savings),
                "energy_savings": format_percentage_savings(energy_savings),
            }
        )

    savings_df = pd.DataFrame(savings)

    print("\nBenchmark results")
    print(result_df.to_string(index=False))

    print("\nSavings vs CSV baseline")
    print(savings_df.to_string(index=False))


if __name__ == "__main__":
    main()
