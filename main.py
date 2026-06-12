"""Main orchestration script leveraging the SyntheticDataGenerator Class to produce Parquet tables."""

import importlib.util
import time
from pathlib import Path
import pandas as pd

from src.config import (
    CUSTOMERS_RAW_FILE,
    ORDERS_RAW_FILE,
    PRODUCTS_RAW_FILE,
    RAW_DATA_DIR,
    logger,
)
from src.data_generator import SyntheticDataGenerator


def get_file_metrics(directory: Path, filename: str) -> str:
    """Calculates disk space metric sizes for tracking."""
    target_path = directory / filename
    if target_path.exists():
        bytes_size = target_path.stat().st_size
        return f"{bytes_size / (1024 * 1024):.2f} MB ({bytes_size} bytes)"
    return "File Not Found"


def main() -> None:
    """Runs the statistical generation engine and outputs to local storage."""
    logger.info("Initializing baseline high-scale orchestrator routine...")
    start_time = time.time()

    try:
        # 1. Instantiating the new Generator Class
        generator = SyntheticDataGenerator()

        # Define high-scale benchmarks matching image configurations
        CUSTOMERS_LIMIT = 100000
        PRODUCTS_LIMIT = 10000
        ORDERS_LIMIT = 1000000

        # 3. Generating DataFrames using default parameters
        customers_df = generator.generate_customers(num_customers=CUSTOMERS_LIMIT)
        products_df = generator.generate_products(num_products=PRODUCTS_LIMIT)
        orders_df = generator.generate_orders(
            num_orders=ORDERS_LIMIT,
            num_customers=CUSTOMERS_LIMIT,
            num_products=PRODUCTS_LIMIT,
        )

        # 4. Save directly as Parquet files
        logger.info("Saving generated tables as Parquet to storage paths...")
        parquet_engine = None
        if importlib.util.find_spec("pyarrow") is not None:
            parquet_engine = "pyarrow"
        elif importlib.util.find_spec("fastparquet") is not None:
            parquet_engine = "fastparquet"
        else:
            raise ImportError(
                "No Parquet engine installed. Install pyarrow or fastparquet."
            )

        customers_df.to_parquet(CUSTOMERS_RAW_FILE, engine=parquet_engine, index=False)
        products_df.to_parquet(PRODUCTS_RAW_FILE, engine=parquet_engine, index=False)
        orders_df.to_parquet(ORDERS_RAW_FILE, engine=parquet_engine, index=False)

        # 5. Output pipeline metrics
        elapsed_time = time.time() - start_time
        print("\nCompleted in {:.1f} seconds".format(elapsed_time))
        print("Files saved:")
        print(f" - {CUSTOMERS_RAW_FILE.name} ({get_file_metrics(RAW_DATA_DIR, CUSTOMERS_RAW_FILE.name)})")
        print(f" - {PRODUCTS_RAW_FILE.name} ({get_file_metrics(RAW_DATA_DIR, PRODUCTS_RAW_FILE.name)})")
        print(f" - {ORDERS_RAW_FILE.name} ({get_file_metrics(RAW_DATA_DIR, ORDERS_RAW_FILE.name)})")

    except IOError as ioe:
        logger.error(f"Write operation failed due to filesystem IO permissions: {str(ioe)}")
    except Exception as e:
        logger.error(f"A pipeline execution collapse occurred: {str(e)}", exc_info=True)


if __name__ == "__main__":
    main()