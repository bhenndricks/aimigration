"""Generate realistic demo data for CUSTOMER_ORDERS_DEMO in adb_sanjose.

- Connects to Autonomous Database in San Jose using Easy Connect Plus + wallet
- Prompts for ADMIN password via getpass (no echo)
- Inserts 50,000 realistic e-commerce orders in batches using executemany
- Commits in batches (default: 5,000 rows per commit)
- Prints progress every 10,000 rows
- Measures and reports total execution time
- Verifies final row count in CUSTOMER_ORDERS_DEMO

IMPORTANT:
    This script assumes the CUSTOMER_ORDERS_DEMO table already exists
    with the DDL you approved. Run the CREATE TABLE / CREATE INDEX
    statements before executing this script.

Prerequisites:
    pip install oracledb
"""

import datetime as dt
import getpass
import json
import random
import sys
import time

try:
    import oracledb
except ImportError as exc:  # pragma: no cover - environment-specific
    print("python-oracledb is not installed.")
    print("Install it with: pip install oracledb")
    sys.exit(1)

# Configuration
TOTAL_ROWS = 50_000
BATCH_SIZE = 5_000  # commit after this many rows
PROGRESS_INTERVAL = 10_000  # print progress every N rows

# Easy Connect Plus-style descriptor for adb_sanjose (with wallet directory)
ADB_SJ_DSN = (
    "(description=(retry_count=20)(retry_delay=3)"
    "(address=(protocol=tcps)(port=1522)"
    "(host=adb.us-sanjose-1.oraclecloud.com))"
    "(connect_data=(service_name=fp7cb75hkszpygo_adbsj_high.adb.oraclecloud.com))"
    "(security=(ssl_server_dn_match=yes)"
    "(my_wallet_directory=C:\\Users\\Blake\\Downloads\\Wallet_ADBSJ)))"
)


FIRST_NAMES = [
    "Alex",
    "Jordan",
    "Taylor",
    "Morgan",
    "Casey",
    "Riley",
    "Jamie",
    "Avery",
    "Chris",
    "Dana",
]

LAST_NAMES = [
    "Smith",
    "Johnson",
    "Williams",
    "Brown",
    "Jones",
    "Garcia",
    "Miller",
    "Davis",
    "Rodriguez",
    "Martinez",
]

PRODUCT_CATEGORIES = [
    "Electronics",
    "Home & Garden",
    "Books",
    "Clothing",
    "Sports",
    "Beauty",
    "Toys",
    "Automotive",
]

PRODUCT_NAMES = [
    "Wireless Headphones",
    "Smartphone",
    "Coffee Maker",
    "Running Shoes",
    "LED Monitor",
    "Bluetooth Speaker",
    "Backpack",
    "Cookware Set",
    "Desk Lamp",
    "Noise Cancelling Earbuds",
]

ORDER_CHANNELS = ["WEB", "MOBILE", "CALL_CENTER", "MARKETPLACE"]

ORDER_STATUSES = [
    "NEW",
    "PENDING_PAYMENT",
    "PAID",
    "SHIPPED",
    "DELIVERED",
    "CANCELLED",
    "RETURNED",
]

ORDER_STATUS_WEIGHTS = [0.15, 0.15, 0.25, 0.2, 0.18, 0.04, 0.03]

SHIPPING_STATUSES = [
    "PENDING",
    "PICKED",
    "IN_TRANSIT",
    "DELIVERED",
    "RETURNED",
    "LOST",
]

SHIPPING_STATUS_WEIGHTS = [0.25, 0.1, 0.3, 0.3, 0.04, 0.01]

PAYMENT_METHODS = [
    "CARD",
    "PAYPAL",
    "APPLE_PAY",
    "GOOGLE_PAY",
    "BANK_TRANSFER",
]

CUSTOMER_NOTES_EXAMPLES = [
    "Please leave the package at the front door.",
    "Gift order, do not include price on receipt.",
    "Call me before delivery.",
    "Deliver after 5 PM if possible.",
    "Leave with neighbor if not home.",
]

CITIES = ["San Francisco", "Los Angeles", "Seattle", "Portland", "Phoenix"]
STATES = ["CA", "WA", "OR", "AZ", "NV"]
COUNTRIES = ["USA"]


def random_order_row() -> dict:
    """Generate a single realistic order row as bind parameters.

    Only includes columns that we explicitly insert; other columns
    rely on database defaults (e.g., order_id identity, order_ts,
    currency_code, is_fraud_suspected, created_at).
    """

    # Basic customer info
    customer_id = random.randint(1, 10_000)
    first = random.choice(FIRST_NAMES)
    last = random.choice(LAST_NAMES)
    customer_name = f"{first} {last}"
    email_suffix = random.randint(1, 9999)
    customer_email = f"{first.lower()}.{last.lower()}{email_suffix}@example.com"

    # Order status / channel
    order_status = random.choices(ORDER_STATUSES, weights=ORDER_STATUS_WEIGHTS, k=1)[0]
    order_channel = random.choice(ORDER_CHANNELS)

    # Order date in the last 2 years
    today = dt.date.today()
    days_back = random.randint(0, 365 * 2)
    order_date = today - dt.timedelta(days=days_back)

    # Shipping info
    city = random.choice(CITIES)
    state = random.choice(STATES)
    country = random.choice(COUNTRIES)
    street_no = random.randint(100, 9999)
    street_name = random.choice([
        "Main St",
        "Oak Ave",
        "Pine Rd",
        "Maple Dr",
        "Cedar Ln",
    ])
    shipping_address = f"{street_no} {street_name}"
    postal = f"{random.randint(85000, 96999)}"

    shipping_status = random.choices(
        SHIPPING_STATUSES, weights=SHIPPING_STATUS_WEIGHTS, k=1
    )[0]

    # Pricing
    base_price = round(random.uniform(10.0, 5000.0), 2)
    discount_percent = random.choice([0.0, 5.0, 10.0, 15.0, 20.0])
    discount_amount = base_price * (discount_percent / 100.0)
    taxable_amount = base_price - discount_amount
    tax_rate = random.uniform(0.05, 0.1)
    tax_amount = round(taxable_amount * tax_rate, 2)
    order_total = round(taxable_amount + tax_amount, 2)

    # Payment
    payment_method = random.choice(PAYMENT_METHODS)
    payment_auth_code = "".join(random.choices("0123456789ABCDEF", k=12))

    # Metadata JSON (optional)
    if random.random() < 0.6:
        device = random.choice([
            "desktop",
            "mobile_ios",
            "mobile_android",
            "tablet",
        ])
        campaign = random.choice([
            "spring_sale",
            "black_friday",
            "email_newsletter",
            "social_media",
            "direct",
        ])
        referrer = random.choice([
            "google",
            "bing",
            "facebook",
            "twitter",
            "direct",
        ])
        metadata_json = json.dumps(
            {
                "device": device,
                "campaign": campaign,
                "referrer": referrer,
            }
        )
    else:
        metadata_json = None

    # Product details JSON (always populated)
    product_name = random.choice(PRODUCT_NAMES)
    category = random.choice(PRODUCT_CATEGORIES)
    quantity = random.randint(1, 5)
    unit_price = round(base_price / max(quantity, 1), 2)
    sku = f"SKU-{random.randint(10000, 99999)}"
    product_details_json = json.dumps(
        {
            "product_name": product_name,
            "category": category,
            "quantity": quantity,
            "unit_price": unit_price,
            "sku": sku,
        }
    )

    # Customer notes (optional)
    if random.random() < 0.25:
        customer_notes = random.choice(CUSTOMER_NOTES_EXAMPLES)
    else:
        customer_notes = None

    return {
        "customer_id": customer_id,
        "customer_name": customer_name,
        "customer_email": customer_email,
        "order_status": order_status,
        "order_channel": order_channel,
        "order_date": order_date,
        "shipping_address": shipping_address,
        "shipping_city": city,
        "shipping_state": state,
        "shipping_postal": postal,
        "shipping_country": country,
        "shipping_status": shipping_status,
        "order_total": order_total,
        "discount_percent": discount_percent,
        "tax_amount": tax_amount,
        "payment_method": payment_method,
        "payment_auth_code": payment_auth_code,
        "metadata_json": metadata_json,
        "product_details_json": product_details_json,
        "customer_notes": customer_notes,
    }


INSERT_SQL = """
INSERT INTO customer_orders_demo (
    customer_id,
    customer_name,
    customer_email,
    order_status,
    order_channel,
    order_date,
    shipping_address,
    shipping_city,
    shipping_state,
    shipping_postal,
    shipping_country,
    shipping_status,
    order_total,
    discount_percent,
    tax_amount,
    payment_method,
    payment_auth_code,
    metadata_json,
    product_details_json,
    customer_notes
) VALUES (
    :customer_id,
    :customer_name,
    :customer_email,
    :order_status,
    :order_channel,
    :order_date,
    :shipping_address,
    :shipping_city,
    :shipping_state,
    :shipping_postal,
    :shipping_country,
    :shipping_status,
    :order_total,
    :discount_percent,
    :tax_amount,
    :payment_method,
    :payment_auth_code,
    :metadata_json,
    :product_details_json,
    :customer_notes
)
"""


def main() -> None:
    print("This script will generate demo data in CUSTOMER_ORDERS_DEMO (adb_sanjose).")
    print(f"Total rows to insert: {TOTAL_ROWS}")
    print(f"Batch size: {BATCH_SIZE} rows per commit")
    print("")

    password = getpass.getpass(
        "Enter password for ADMIN on adb_sanjose (adbsj_high): "
    )

    user = "ADMIN"

    start_time = time.perf_counter()

    try:
        with oracledb.connect(
            user=user,
            password=password,
            dsn=ADB_SJ_DSN,
        ) as conn:
            with conn.cursor() as cursor:
                # Sanity check: ensure table exists
                try:
                    cursor.execute("SELECT COUNT(*) FROM customer_orders_demo WHERE 1 = 0")
                except Exception as table_exc:
                    print("Error checking CUSTOMER_ORDERS_DEMO existence.")
                    print("Make sure the table is created before running this script.")
                    print(f"Details: {table_exc}")
                    return

                inserted = 0
                while inserted < TOTAL_ROWS:
                    remaining = TOTAL_ROWS - inserted
                    batch_size = min(BATCH_SIZE, remaining)

                    rows = [random_order_row() for _ in range(batch_size)]

                    cursor.executemany(INSERT_SQL, rows)
                    conn.commit()

                    inserted += batch_size

                    if inserted % PROGRESS_INTERVAL == 0 or inserted == TOTAL_ROWS:
                        print(f"Inserted {inserted} / {TOTAL_ROWS} rows...")

                # Verify final row count
                cursor.execute("SELECT COUNT(*) FROM customer_orders_demo")
                (row_count,) = cursor.fetchone()

    except Exception as e:  # pragma: no cover - manual diagnostics
        print("An error occurred during data generation:")
        print(e)
        return

    end_time = time.perf_counter()
    elapsed = end_time - start_time

    print("")
    print("Data generation complete.")
    print(f"Total rows reported by database: {row_count}")
    print(f"Total execution time: {elapsed:.2f} seconds")


if __name__ == "__main__":
    main()
