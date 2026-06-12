### `src/config.py`
"""Configuration settings and path management for the data pipeline."""

import logging
from pathlib import Path

# Base Directory Resolution
BASE_DIR: Path = Path(__file__).resolve().parent.parent

# Data Directories
RAW_DATA_DIR: Path = BASE_DIR / "data" / "raw"
PROCESSED_DATA_DIR: Path = BASE_DIR / "data" / "processed"

# Supported raw data format and naming
RAW_DATA_FORMAT: str = "parquet"
RAW_FILE_EXTENSION: str = ".parquet"
CUSTOMERS_RAW_FILE: Path = RAW_DATA_DIR / f"customers{RAW_FILE_EXTENSION}"
PRODUCTS_RAW_FILE: Path = RAW_DATA_DIR / f"products{RAW_FILE_EXTENSION}"
ORDERS_RAW_FILE: Path = RAW_DATA_DIR / f"orders{RAW_FILE_EXTENSION}"

# Processed analytics output directories
CATEGORY_REVENUE_OUTPUT_DIR: Path = PROCESSED_DATA_DIR / "category_revenue"
CUSTOMER_SPEND_OUTPUT_DIR: Path = PROCESSED_DATA_DIR / "customer_spend"

# Ensure runtime directories exist
RAW_DATA_DIR.mkdir(parents=True, exist_ok=True)
PROCESSED_DATA_DIR.mkdir(parents=True, exist_ok=True)

# Centralized Logging Configuration
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(filename)s:%(lineno)d - %(message)s",
    handlers=[logging.StreamHandler()],
)

logger: logging.Logger = logging.getLogger("EcommercePipeline")