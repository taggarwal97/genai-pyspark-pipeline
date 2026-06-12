### `src/config.py`
```python
"""Configuration settings and path management for the data pipeline."""

import logging
import os
from pathlib import Path

# Base Directory Resolution
BASE_DIR: Path = Path(__file__).resolve().parent.parent

# Data Pathway Mappings
RAW_DATA_DIR: Path = BASE_DIR / "data" / "raw"
PROCESSED_DATA_DIR: Path = BASE_DIR / "data" / "processed"

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