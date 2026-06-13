"""
spark_analytics.py
A PySpark analytics module for processing sales and customer performance metrics.
"""

from pyspark.sql import SparkSession, DataFrame
import pyspark.sql.functions as F
from pyspark.sql.window import Window

from src.config import ORDERS_RAW_FILE, PRODUCTS_RAW_FILE, logger


class SalesAnalytics:
    """Class containing methods for sales data processing and analytics."""

    @staticmethod
    def create_spark_session() -> SparkSession:
        """
        Configures and initializes a local SparkSession.
        
        Configurations applied:
        - Local mode execution
        - 4GB Driver memory
        - Adaptive Query Execution (AQE) enabled
        - Kryo Serialization for improved performance
        
        Returns:
            SparkSession: The active Spark session.
        """
        return (
            SparkSession.builder.appName("SalesAnalytics")
            .master("local[*]")
            .config("spark.driver.memory", "4g")
            .config("spark.sql.adaptive.enabled", "true")
            .config("spark.serializer", "org.apache.spark.serializer.KryoSerializer")
            .getOrCreate()
        )

    @staticmethod
    def load_parquet(spark: SparkSession, path: str) -> DataFrame:
        """
        Loads data from a Parquet file into a DataFrame.
        
        Args:
            spark (SparkSession): The active Spark session.
            path (str): Path to the Parquet file or directory.
            
        Returns:
            DataFrame: The loaded PySpark DataFrame.
        """
        return spark.read.parquet(path)

    @staticmethod
    def top_customers_by_revenue(
        orders_df: DataFrame, products_df: DataFrame, n: int = 10
    ) -> DataFrame:
        """
        Calculates the total spend per customer and returns the top N customers.
        
        Assumes orders_df has 'product_id', 'customer_id', and 'quantity'.
        Assumes products_df has 'product_id' and 'price'.
        
        Args:
            orders_df (DataFrame): DataFrame of order transactions.
            products_df (DataFrame): DataFrame of product details.
            n (int): Number of top customers to return. Default is 10.
            
        Returns:
            DataFrame: Top N customers by total revenue.
        """
        return (
            orders_df.join(products_df, on="product_id", how="inner")
            .withColumn("revenue", F.col("quantity").cast("double") * F.col("price").cast("double"))
            .groupBy("customer_id")
            .agg(F.round(F.sum("revenue"), 2).alias("total_revenue"))
            .orderBy(F.col("total_revenue").desc())
            .limit(n)
        )

    @staticmethod
    def sales_by_category(orders_df: DataFrame, products_df: DataFrame) -> DataFrame:
        """
        Groups sales by product category to sum total revenue and units sold.
        
        Assumes orders_df has 'product_id' and 'quantity'.
        Assumes products_df has 'product_id', 'category', and 'price'.
        
        Args:
            orders_df (DataFrame): DataFrame of order transactions.
            products_df (DataFrame): DataFrame of product details.
            
        Returns:
            DataFrame: Aggregated sales metrics per category.
        """
        return (
            orders_df.join(products_df, on="product_id", how="inner")
            .withColumn("revenue", F.col("quantity") * F.col("price"))
            .groupBy("category")
            .agg(
                F.sum("quantity").alias("units_sold"),
                F.sum("revenue").alias("revenue")
            )
            .orderBy(F.col("revenue").desc())
        )

    @staticmethod
    def monthly_trends(orders_df: DataFrame, products_df: DataFrame) -> DataFrame:
        """
        Calculates month-over-month (MoM) revenue growth percentage.
        
        Assumes orders_df has 'product_id', 'quantity', and 'order_date'.
        Assumes products_df has 'product_id' and 'price'.
        
        Args:
            orders_df (DataFrame): DataFrame of order transactions.
            products_df (DataFrame): DataFrame of product details.
            
        Returns:
            DataFrame: Monthly trends with MoM growth percentage.
        """
        # Join data, normalize order_date to timestamp, calculate revenue, and format month-year
        daily_revenue = (
            orders_df.join(products_df, on="product_id", how="inner")
            .withColumn("order_date", F.to_timestamp("order_date", "yyyy-MM-dd HH:mm:ss"))
            .withColumn("revenue", F.col("quantity") * F.col("price"))
            .withColumn("month_year", F.date_format("order_date", "yyyy-MM"))
        )

        # Aggregate total revenue per month
        monthly_revenue = (
            daily_revenue.groupBy("month_year")
            .agg(F.sum("revenue").alias("current_month_revenue"))
        )

        # Define Window specification ordered by chronological month
        window_spec = Window.orderBy("month_year")

        # Calculate Lag (previous month's revenue) and MoM Growth
        trends_df = (
            monthly_revenue.withColumn(
                "prev_month_revenue", 
                F.lag("current_month_revenue", 1).over(window_spec)
            )
            .withColumn(
                "mom_growth_percentage",
                F.when(
                    F.col("prev_month_revenue").isNull(), 0.0
                ).otherwise(
                    ((F.col("current_month_revenue") - F.col("prev_month_revenue")) 
                     / F.col("prev_month_revenue")) * 100
                )
            )
            .orderBy("month_year")
        )

        return trends_df


# --- Execution Example ---
if __name__ == "__main__":
    spark = SalesAnalytics.create_spark_session()
    spark.sparkContext.setLogLevel("ERROR")

    try:
        orders_df = SalesAnalytics.load_parquet(spark, ORDERS_RAW_FILE.as_posix())
        products_df = SalesAnalytics.load_parquet(spark, PRODUCTS_RAW_FILE.as_posix())

        print(f"Loaded orders from {ORDERS_RAW_FILE}")
        print(f"Loaded products from {PRODUCTS_RAW_FILE}\n")

        print("--- Top Customers by Revenue ---")
        top_customers = SalesAnalytics.top_customers_by_revenue(orders_df, products_df, n=10)
        top_customers.show(truncate=False)

        print("--- Sales by Category ---")
        category_sales = SalesAnalytics.sales_by_category(orders_df, products_df)
        category_sales.show(truncate=False)

        print("--- Monthly Trends (MoM Growth %) ---")
        monthly_trends = SalesAnalytics.monthly_trends(orders_df, products_df)
        monthly_trends.show(truncate=False)

    except Exception as exc:
        logger.error("Failed to run analytics: %s", str(exc), exc_info=True)
        print(
            "Analytics execution failed. Ensure raw Parquet files exist in data/raw and "
            "run main.py to generate them if needed."
        )
    finally:
        spark.stop()
