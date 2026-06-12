"""Ingests e-commerce CSV datasets using PySpark and computes business insights."""

from config import (
    CATEGORY_REVENUE_OUTPUT_DIR,
    CUSTOMER_SPEND_OUTPUT_DIR,
    CUSTOMERS_RAW_FILE,
    ORDERS_RAW_FILE,
    PRODUCTS_RAW_FILE,
    logger,
)
from pyspark.sql import DataFrame, SparkSession
from pyspark.sql import functions as F


def create_spark_session() -> SparkSession:
    """Instantiates a localized SparkSession worker context instance.

    Returns:
        An active SparkSession object.
    """
    logger.info("Initializing localized SparkSession container...")
    spark = (
        SparkSession.builder.appName("EcommerceDataAnalytics")
        .master("local[*]")
        .getOrCreate()
    )
    logger.info("SparkSession initialized successfully.")
    return spark


def load_datasets(spark: SparkSession) -> tuple[DataFrame, DataFrame, DataFrame]:
    """Loads raw structured infrastructure objects into Spark DataFrame sets.

    Args:
        spark: Active context control workspace manager variable.

    Returns:
        A tuple of (customers_df, products_df, orders_df).
    """
    logger.info("Loading raw Parquet tables into Spark DataFrames...")

    cust_df = spark.read.parquet(str(CUSTOMERS_RAW_FILE))
    prod_df = spark.read.parquet(str(PRODUCTS_RAW_FILE))
    ord_df = spark.read.parquet(str(ORDERS_RAW_FILE))

    logger.info("Datasets ingested into Spark DataFrames.")
    return cust_df, prod_df, ord_df


def run_business_analysis(
    customers: DataFrame, products: DataFrame, orders: DataFrame
) -> tuple[DataFrame, DataFrame]:
    """Runs data transformations to extract meaningful metrics.

    Metrics include:
      1. Total revenue breakdown by catalog product category.
      2. Top purchasing customer groups categorized by spend levels.

    Args:
        customers: Transformed customer table dataframe.
        products: Transformed product properties database matrix.
        orders: Transformed customer-order log history sheets.

    Returns:
        A tuple containing (category_revenue_df, top_customers_df).
    """
    logger.info("Beginning execution of analytic aggregation calculations...")

    # Calculate Total Sales Value per individual transaction entry line
    joined_transactions = orders.join(products, on="product_id", how="inner").join(
        customers, on="customer_id", how="inner"
    )
    
    enriched_sales_df = joined_transactions.withColumn(
        "total_revenue", F.col("quantity") * F.col("price")
    )

    # Insight Metric 1: Total Revenue Generated per Category Classification Segment
    logger.info("Computing revenue summaries broken down by product group...")
    category_insights = (
        enriched_sales_df.groupBy("category")
        .agg(
            F.round(F.sum("total_revenue"), 2).alias("total_sales_revenue"),
            F.sum("quantity").alias("units_sold_count"),
        )
        .orderBy(F.desc("total_sales_revenue"))
    )

    # Insight Metric 2: High-Value Customer VIP Tier Group List
    logger.info("Compiling client valuation summary table data matrices...")
    customer_insights = (
        enriched_sales_df.groupBy("customer_id", "name", "country")
        .agg(F.round(F.sum("total_revenue"), 2).alias("aggregate_customer_spend"))
        .orderBy(F.desc("aggregate_customer_spend"))
    )

    return category_insights, customer_insights


def main() -> None:
    """Coordinates Spark analysis operations and writes outputs."""
    spark = create_spark_session()
    
    try:
        customers, products, orders = load_datasets(spark)
        category_rev, top_cust = run_business_analysis(customers, products, orders)
        
        # Display insights in console
        logger.info("--- CATEGORY REVENUE INSIGHTS ---")
        category_rev.show(10, truncate=False)
        
        logger.info("--- TOP 10 PURCHASING CUSTOMERS ---")
        top_cust.show(10, truncate=False)
        
        # Save results out to disk as Single Partitioned Coalesced CSVs
        category_output = PROCESSED_DATA_DIR / "category_revenue"
        customer_output = PROCESSED_DATA_DIR / "customer_spend"
        
        logger.info(f"Writing category revenue outputs to: {category_output}")
        category_rev.coalesce(1).write.mode("overwrite").csv(str(category_output), header=True)
        
        logger.info(f"Writing customer value outputs to: {customer_output}")
        top_cust.coalesce(1).write.mode("overwrite").csv(str(customer_output), header=True)
        
        logger.info("Data pipeline analytics job completed successfully.")
        
    except Exception as e:
        logger.error(f"Pipeline execution failed: {str(e)}", exc_info=True)
    finally:
        logger.info("Shutting down active Spark Session workspace execution layer.")
        spark.stop()


if __name__ == "__main__":
    main()