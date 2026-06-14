# E-Commerce Data Pipeline Project

An end-to-end Python data pipeline that generates synthetic e-commerce datasets, writes them to Parquet, and executes PySpark analytics for customer and revenue insights.

This project is released under the MIT License.

## Features
- Synthetic customer, product, and order data generation
- Parquet storage for raw data
- PySpark analytics for:
  - Top customers by revenue
  - Sales by category
  - Monthly revenue trends with MoM growth
- Single-command analytics runner: `python run_analytics.py`

## Prerequisites
- Python 3.10 or 3.11
- Java JDK 8+ / 11+ for PySpark
- pip package manager
- Optional: a virtual environment for isolation
- Windows users:
  - install `winutils.exe`
  - set `HADOOP_HOME` to a local Hadoop root containing `bin\winutils.exe`
  - use a Spark-compatible `winutils.exe` version for PySpark 3.5.1

## Installation
1. Clone the repository:
```bash
git clone <repository-url>
cd genai-pyspark-pipeline
```
2. Create and activate a virtual environment:
```bash
python -m venv venv
# Windows
venv\Scripts\activate
# macOS / Linux
source venv/bin/activate
```
3. Install dependencies:
```bash
pip install -r requirements.txt
```

## Setup
The project stores generated raw files under `data/raw/` and processed outputs under `data/processed/`.

### Generate synthetic data
Run the data generation pipeline to produce raw Parquet files:
```bash
python main.py
```
This will generate:
- `data/raw/customers.parquet`
- `data/raw/products.parquet`
- `data/raw/orders.parquet`

## Usage
### Run analytics
Execute the analytics launcher to load raw Parquet files, compute metrics, and display results:
```bash
python run_analytics.py
```

### Windows-specific PySpark setup
PySpark on Windows often requires `winutils.exe` and `HADOOP_HOME` to be configured correctly. If Spark emits warnings such as "Did not find winutils.exe" or "HADOOP_HOME and hadoop.home.dir are unset", follow these steps:

1. Download a `winutils.exe` binary compatible with Spark 3.5.1 / Hadoop 3.x.
2. Create a local folder such as `C:\hadoop`.
3. Place `winutils.exe` in `C:\hadoop\bin\winutils.exe`.
4. Set the environment variable:
```powershell
setx HADOOP_HOME C:\hadoop
```
5. Restart your terminal and rerun the project commands.

This repository's Windows test setup checks for `HADOOP_HOME` and `winutils.exe` before creating a Spark session.

### Available analytics
- `SalesAnalytics.top_customers_by_revenue(...)`
- `SalesAnalytics.sales_by_category(...)`
- `SalesAnalytics.monthly_trends(...)`

## Example Output
A successful run prints analytics sections like:

```text
Top 10 Customers by Revenue:
+-----------+----------------+
|customer_id|total_revenue   |
+-----------+----------------+
|45632      |$15,432.50      |
|12847      |$14,891.20      |
|78234      |$13,567.80      |
...         ...              

Sales by Category:
+-----------+----------+---------+
|category   |units_sold|revenue  |
+-----------+----------+---------+
|Electronics|245,632   |$2,400,000|
|Clothing   |198,456   |$1,800,000|

Completed in 18.5 seconds
```

## Project Structure
```
genai-pyspark-pipeline/
├── data/
│   ├── processed/
│   └── raw/
├── notebooks/
├── src/
│   ├── config.py
│   ├── data_generator.py
│   └── spark_analytics.py
├── run_analytics.py
├── main.py
├── requirements.txt
└── README.md
```

## Architecture Diagram
```
+----------------------+      +------------------------+      +------------------------+
| Synthetic Data       |      | Storage / Configuration|      | Spark Analytics        |
| Generator            | ---> | - data/raw/*.parquet   | ---> | - load_parquet()       |
| (src/data_generator) |      | - src/config.py        |      | - top_customers_by_revenue()
+----------------------+      +------------------------+      | - sales_by_category()  |
                                                                   | - monthly_trends()     |
                                                                   +------------------------+
```

## License
This repository is licensed under the MIT License. See `LICENSE` for details.
