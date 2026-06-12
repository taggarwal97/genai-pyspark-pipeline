"""Generates synthetic e-commerce data (Customers, Products, Orders) and writes them to CSV."""

import csv
import random
from datetime import datetime, timedelta
from typing import List, Tuple
from config import RAW_DATA_DIR, logger
from faker import Faker


def generate_customers(num_customers: int = 100) -> List[Tuple[int, str, str, str]]:
    """Generates synthetic customer data.

    Args:
        num_customers: The number of unique customer records to build.

    Returns:
        A list of tuples containing (customer_id, name, email, country).
    """
    logger.info("Starting customer data generation...")
    fake = Faker()
    customers: List[Tuple[int, str, str, str]] = []

    for i in range(1, num_customers + 1):
        customers.append(
            (i, fake.name(), fake.unique.email(), fake.country())
        )
    
    logger.info(f"Successfully generated {num_customers} customer records.")
    return customers


def generate_products(num_products: int = 30) -> List[Tuple[int, str, str, float]]:
    """Generates synthetic product catalog data.

    Args:
        num_products: Total distinct products in catalog.

    Returns:
        A list of tuples containing (product_id, product_name, category, price).
    """
    logger.info("Starting product data generation...")
    fake = Faker()
    categories: List[str] = ["Electronics", "Clothing", "Home & Kitchen", "Books", "Sports"]
    products: List[Tuple[int, str, str, float]] = []

    for i in range(1, num_products + 1):
        category = random.choice(categories)
        product_name = f"{category} Item {fake.word().capitalize()}"
        price = round(random.uniform(5.0, 500.0), 2)
        products.append((i, product_name, category, price))

    logger.info(f"Successfully generated {num_products} product records.")
    return products


def generate_orders(
    num_orders: int = 500, customer_count: int = 100, product_count: int = 30
) -> List[Tuple[int, int, int, int, str]]:
    """Generates synthetic order transaction records.

    Args:
        num_orders: Total order entries to log.
        customer_count: Upper bounds of client identity references.
        product_count: Upper bounds of catalog option references.

    Returns:
        A list of tuples containing (order_id, customer_id, product_id, quantity, order_date).
    """
    logger.info("Starting order transaction generation...")
    orders: List[Tuple[int, int, int, int, str]] = []
    start_date: datetime = datetime.now() - timedelta(days=180)

    for i in range(1, num_orders + 1):
        customer_id = random.randint(1, customer_count)
        product_id = random.randint(1, product_count)
        quantity = random.randint(1, 5)
        random_days = random.randint(0, 180)
        order_date = (start_date + timedelta(days=random_days)).strftime("%Y-%m-%d %H:%M:%S")
        
        orders.append((i, customer_id, product_id, quantity, order_date))

    logger.info(f"Successfully generated {num_orders} transactional orders.")
    return orders


def save_to_csv(data: List[Tuple], headers: List[str], filename: str) -> None:
    """Saves generated dataset tables directly to the designated target filesystems.

    Args:
        data: The dataset table records.
        headers: Column schema labels.
        filename: Destination target label.
    """
    target_path = RAW_DATA_DIR / filename
    logger.info(f"Writing data asset to {target_path}...")
    
    with open(target_path, mode="w", newline="", encoding="utf-8") as file:
        writer = csv.writer(file)
        writer.writerow(headers)
        writer.writerows(data)
        
    logger.info(f"Saved file successfully: {filename}")


def main() -> None:
    """Orchestrates generation sequence and disk execution blocks."""
    logger.info("Initializing complete data generation sequence.")
    
    cust_count, prod_count, ord_count = 200, 50, 1500
    
    customers = generate_customers(cust_count)
    products = generate_products(prod_count)
    orders = generate_orders(ord_count, cust_count, prod_count)
    
    save_to_csv(customers, ["customer_id", "name", "email", "country"], "customers.csv")
    save_to_csv(products, ["product_id", "product_name", "category", "price"], "products.csv")
    save_to_csv(orders, ["order_id", "customer_id", "product_id", "quantity", "order_date"], "orders.csv")
    
    logger.info("All mockup datasets have been generated and deployed successfully.")


if __name__ == "__main__":
    main()