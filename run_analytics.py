"""Run SalesAnalytics against raw Parquet input files."""

import time

import pyspark.sql.functions as F
from src.config import CUSTOMERS_RAW_FILE, ORDERS_RAW_FILE, PRODUCTS_RAW_FILE
from src.spark_analytics import SalesAnalytics


def main() -> None:
    spark = SalesAnalytics.create_spark_session()
    spark.sparkContext.setLogLevel("ERROR")

    try:
        customers_df = SalesAnalytics.load_parquet(spark, CUSTOMERS_RAW_FILE.as_posix())
        products_df = SalesAnalytics.load_parquet(spark, PRODUCTS_RAW_FILE.as_posix())
        orders_df = SalesAnalytics.load_parquet(spark, ORDERS_RAW_FILE.as_posix())

        print(f"Loaded customers from {CUSTOMERS_RAW_FILE}")
        print(f"Loaded products from {PRODUCTS_RAW_FILE}")
        print(f"Loaded orders from {ORDERS_RAW_FILE}\n")

        total_start = time.perf_counter()

        start = time.perf_counter()
        top_customers = SalesAnalytics.top_customers_by_revenue(orders_df, products_df, n=10)
        top_elapsed = time.perf_counter() - start
        print("\nTop 10 Customers by Revenue:")
        top_customers.select(
            "customer_id",
            F.concat(F.lit("$"), F.format_number("total_revenue", 2)).alias("total_revenue")
        ).show(10, truncate=False)
        print(f"Completed in {top_elapsed:.3f} seconds\n")

        start = time.perf_counter()
        category_sales = SalesAnalytics.sales_by_category(orders_df, products_df)
        category_elapsed = time.perf_counter() - start
        print("Sales by Category:")
        category_sales.select(
            "category",
            "units_sold",
            F.concat(F.lit("$"), F.format_number("revenue", 0)).alias("revenue")
        ).orderBy(F.col("revenue").desc()).show(10, truncate=False)
        print(f"Completed in {category_elapsed:.3f} seconds\n")

        start = time.perf_counter()
        monthly_trends = SalesAnalytics.monthly_trends(orders_df, products_df)
        trends_elapsed = time.perf_counter() - start
        print("Monthly Trends (MoM Growth %):")
        monthly_trends.select(
            "month_year",
            F.concat(F.lit("$"), F.format_number("current_month_revenue", 0)).alias("current_month_revenue"),
            F.concat(F.lit("$"), F.format_number("prev_month_revenue", 0)).alias("prev_month_revenue"),
            F.concat(F.format_number("mom_growth_percentage", 2), F.lit("%"))
                .alias("mom_growth_percentage")
        ).show(10, truncate=False)
        print(f"Completed in {trends_elapsed:.3f} seconds\n")

        total_elapsed = time.perf_counter() - total_start
        print(f"Completed in {total_elapsed:.3f} seconds")

    except Exception as exc:
        print(f"Analytics execution failed: {exc}")
    finally:
        spark.stop()


if __name__ == "__main__":
    main()
