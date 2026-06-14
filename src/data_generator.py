"""Module for generating scalable, highly realistic synthetic e-commerce datasets using NumPy and Faker."""

import random
from datetime import datetime, timedelta
from typing import List, Tuple
import numpy as np
import pandas as pd
from faker import Faker
from tqdm import tqdm

from src.config import logger


class SyntheticDataGenerator:
    """A statistical dataset generator that produces interconnected relational tables

    for customers, products, and transactional e-commerce orders.
    """

    def __init__(self, seed: int = 42) -> None:
        """Initializes generators, ensuring statistical distributions remain reproducible.

        Args:
            seed: Random seed for predictability across NumPy and Faker instances.
        """
        self.fake = Faker()
        Faker.seed(seed)
        np.random.seed(seed)
        random.seed(seed)
        logger.info(f"Initialized SyntheticDataGenerator with random seed: {seed}")

    def _validate_dataframe(self, df: pd.DataFrame, unique_id_column: str) -> None:
        """Validate generated DataFrame to prevent discrepancies.

        Validations:
            - no null values anywhere in the DataFrame
            - no duplicate rows across all columns
            - the unique id column exists and has no blanks or nulls
            - all values in the unique id column are unique
        """
        if df.isnull().values.any():
            missing = df.isnull().sum().loc[lambda x: x > 0]
            raise ValueError(f"Generated DataFrame contains null values in columns: {missing.index.tolist()}")

        if df.duplicated().any():
            raise ValueError("Generated DataFrame contains duplicate rows.")

        if unique_id_column not in df.columns:
            raise ValueError(f"Expected unique id column '{unique_id_column}' not found in DataFrame.")

        if df[unique_id_column].isnull().any():
            raise ValueError(f"'{unique_id_column}' contains null values.")

        if df[unique_id_column].astype(str).str.strip().eq("").any():
            raise ValueError(f"'{unique_id_column}' contains blank or empty values.")

        if df[unique_id_column].duplicated().any():
            duplicated_ids = df[df[unique_id_column].duplicated()][unique_id_column].unique().tolist()
            raise ValueError(
                f"'{unique_id_column}' contains duplicate ids: {duplicated_ids[:10]}"
            )

    def generate_customers(self, num_customers: int = 100000) -> pd.DataFrame:
        """Generates customer demographic records with normally distributed age variables.

        Args:
            num_customers: Number of unique customer records to generate. Default 100K.

        Returns:
            A pandas DataFrame containing customer records.
        """
        try:
            logger.info(f"Generating {num_customers} customer profiles...")
            
            # Statistically model ages: Normal distribution centered around 35 (STD = 10) bounded between 18 and 85
            ages = np.random.normal(loc=35.0, scale=10.0, size=num_customers).astype(int)
            ages = np.clip(ages, 18, 85)

            data: List[Tuple] = []
            start_date = datetime(2022, 1, 1)
            end_date = datetime(2026, 1, 1)
            time_delta_days = (end_date - start_date).days

            # Progress tracking via tqdm
            for i in tqdm(range(1, num_customers + 1), desc="Customers Generation"):
                name = self.fake.name()
                email = self.fake.unique.email()
                city = self.fake.city()
                country = self.fake.country()
                
                # Linear distribution across a 4-year registration window
                reg_date = start_date + timedelta(days=int(np.random.randint(0, time_delta_days)))
                
                data.append((
                    i, name, email, int(ages[i - 1]), city, country, reg_date.strftime("%Y-%m-%d %H:%M:%S")
                ))

            columns = ["customer_id", "name", "email", "age", "city", "country", "registration_date"]
            df = pd.DataFrame(data, columns=columns)
            self._validate_dataframe(df, unique_id_column="customer_id")
            return df
        except Exception as exc:
            logger.error(f"Failed to generate customer data: {exc}")
            raise

    def generate_products(self, num_products: int = 10000) -> pd.DataFrame:
        """Generates an indexed product catalog with randomized pricing arrays.

        Args:
            num_products: Total distinct items in catalog inventory. Default 10K.

        Returns:
            A pandas DataFrame containing product records.
        """
        try:
            logger.info(f"Generating {num_products} catalog items...")
            categories = ["Electronics", "Clothing", "Home", "Sports", "Books"]
            
            data: List[Tuple] = []
            for i in tqdm(range(1, num_products + 1), desc="Products Generation"):
                category = random.choice(categories)
                name = f"{category} Specific Item {i}"
                
                # Uniform continuous float price mapping bounded within $10 to $500
                price = round(float(np.random.uniform(10.0, 500.0)), 2)
                stock = int(np.random.randint(0, 1001))
                rating = round(float(np.random.uniform(1.0, 5.0)), 1)
                
                data.append((i, name, category, price, stock, rating))

            columns = ["product_id", "name", "category", "price", "stock", "rating"]
            df = pd.DataFrame(data, columns=columns)
            self._validate_dataframe(df, unique_id_column="product_id")
            return df
        except Exception as exc:
            logger.error(f"Failed to generate product data: {exc}")
            raise

    def generate_orders(
        self, num_orders: int = 1000000, num_customers: int = 100000, num_products: int = 10000
    ) -> pd.DataFrame:
        """Generates transactional logs utilizing a Pareto distribution (80/20 rule).

        Ensures 20% of customer IDs generate roughly 80% of total order records.

        Args:
            num_orders: Total transaction lines to write. Default 1M.
            num_customers: Max bounds of target customer primary keys.
            num_products: Max bounds of target product primary keys.

        Returns:
            A pandas DataFrame containing order transactions.
        """
        try:
            logger.info(f"Generating {num_orders} order transaction entries...")
            
            # Pareto shape parameter alpha closely approximating an 80/20 split is ~1.16
            alpha = 1.16
            pareto_samples = np.random.pareto(alpha, size=num_orders)
            
            # Normalize and map values onto the valid index range of customer keys
            max_sample = pareto_samples.max()
            if max_sample == 0:
                max_sample = 1
                
            customer_indices = (pareto_samples / max_sample * (num_customers - 1)).astype(int) + 1
            customer_indices = np.clip(customer_indices, 1, num_customers)

            # Uniformly pick product IDs and item quantities (1 to 10)
            product_ids = np.random.randint(1, num_products + 1, size=num_orders)
            quantities = np.random.randint(1, 11, size=num_orders)
            
            # Build chronological timeline sequences spanning the past year
            now = datetime.now()
            data: List[Tuple] = []

            for i in tqdm(range(1, num_orders + 1), desc="Orders Generation"):
                cust_id = int(customer_indices[i - 1])
                prod_id = int(product_ids[i - 1])
                qty = int(quantities[i - 1])
                
                # Distribute execution dates backwards over a 365-day range
                seconds_offset = np.random.randint(0, 365 * 24 * 60 * 60)
                order_time = now - timedelta(seconds=int(seconds_offset))
                
                data.append((i, cust_id, prod_id, qty, order_time.strftime("%Y-%m-%d %H:%M:%S")))

            columns = ["order_id", "customer_id", "product_id", "quantity", "order_date"]
            df = pd.DataFrame(data, columns=columns)
            self._validate_dataframe(df, unique_id_column="order_id")
            return df
        except Exception as exc:
            logger.error(f"Failed to generate order data: {exc}")
            raise


if __name__ == "__main__":
    # Test execution block verifying system output behaviors
    import time
    
    start = time.time()
    generator = SyntheticDataGenerator()
    
    # Executing localized micro-batch generations for safe testing
    cust_df = generator.generate_customers(num_customers=1000)
    prod_df = generator.generate_products(num_products=100)
    ord_df = generator.generate_orders(num_orders=5000, num_customers=1000, num_products=100)
    
    logger.info(f"Test Generation completed in {time.time() - start:.2f} seconds.")
    logger.info(f"Customer Shape: {cust_df.shape}, Product Shape: {prod_df.shape}, Orders Shape: {ord_df.shape}")