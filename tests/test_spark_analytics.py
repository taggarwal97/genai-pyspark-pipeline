import pytest
from pyspark.sql import Row
from pyspark.sql.functions import col

from src.spark_analytics import SalesAnalytics


def test_top_customers_by_revenue_returns_expected_order(spark):
    orders = spark.createDataFrame(
        [
            Row(order_id=1, customer_id=101, product_id=1001, quantity=2),
            Row(order_id=2, customer_id=102, product_id=1002, quantity=1),
            Row(order_id=3, customer_id=101, product_id=1003, quantity=3),
        ]
    )
    products = spark.createDataFrame(
        [
            Row(product_id=1001, price=10.0),
            Row(product_id=1002, price=20.0),
            Row(product_id=1003, price=30.0),
        ]
    )

    result = SalesAnalytics.top_customers_by_revenue(orders, products, n=2)
    rows = result.collect()

    assert len(rows) == 2
    assert rows[0]["customer_id"] == 101
    assert rows[0]["total_revenue"] == 110.0
    assert rows[1]["customer_id"] == 102
    assert rows[1]["total_revenue"] == 20.0


def test_sales_by_category_aggregates_units_and_revenue(spark):
    orders = spark.createDataFrame(
        [
            Row(order_id=1, customer_id=101, product_id=1001, quantity=2),
            Row(order_id=2, customer_id=101, product_id=1002, quantity=1),
            Row(order_id=3, customer_id=102, product_id=1001, quantity=3),
        ]
    )
    products = spark.createDataFrame(
        [
            Row(product_id=1001, category="Electronics", price=15.0),
            Row(product_id=1002, category="Books", price=25.0),
        ]
    )

    result = SalesAnalytics.sales_by_category(orders, products)
    rows = {row["category"]: (row["units_sold"], row["revenue"]) for row in result.collect()}

    assert rows["Electronics"] == (5, 75.0)
    assert rows["Books"] == (1, 25.0)


def test_monthly_trends_calculates_mom_growth(spark):
    orders = spark.createDataFrame(
        [
            Row(order_id=1, customer_id=101, product_id=1001, quantity=2, order_date="2025-01-10 12:00:00"),
            Row(order_id=2, customer_id=102, product_id=1001, quantity=1, order_date="2025-01-20 12:00:00"),
            Row(order_id=3, customer_id=101, product_id=1001, quantity=3, order_date="2025-02-05 12:00:00"),
        ]
    )
    products = spark.createDataFrame([Row(product_id=1001, price=10.0)])

    result = SalesAnalytics.monthly_trends(orders, products).orderBy(col("month_year"))
    rows = {row["month_year"]: (row["current_month_revenue"], row["mom_growth_percentage"]) for row in result.collect()}

    assert rows["2025-01"][0] == 30.0
    assert rows["2025-01"][1] == 0.0
    assert rows["2025-02"][0] == 30.0
    assert rows["2025-02"][1] == pytest.approx(0.0)


def test_monthly_trends_handles_missing_previous_month(spark):
    orders = spark.createDataFrame(
        [Row(order_id=1, customer_id=101, product_id=1001, quantity=5, order_date="2025-03-01 08:00:00")]
    )
    products = spark.createDataFrame([Row(product_id=1001, price=12.0)])

    result = SalesAnalytics.monthly_trends(orders, products).collect()

    assert len(result) == 1
    assert result[0]["month_year"] == "2025-03"
    assert result[0]["current_month_revenue"] == 60.0
    assert result[0]["mom_growth_percentage"] == 0.0
