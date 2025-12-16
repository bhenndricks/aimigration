"""Import CUSTOMER_ORDERS_DEMO into adb_phoenix from Object Storage using DBMS_CLOUD.COPY_DATA.

- Uses OBJ_STORE_CRED (already created) to access Object Storage
- Reads the CSV exported by export_cloud.py
- Loads data into ADMIN.CUSTOMER_ORDERS_DEMO
- Truncates the table before load for idempotence
- Prints timing and verifies target row count

Prerequisites:
    pip install oracledb
    OBJ_STORE_CRED exists in adb_phoenix
    CUSTOMER_ORDERS_DEMO table exists in adb_phoenix
"""

import getpass
import sys
import time

try:
    import oracledb
except ImportError:
    print("python-oracledb is not installed. Install it with: pip install oracledb")
    sys.exit(1)

# Connection DSN for adb_phoenix (with wallet directory)
ADB_PHX_DSN = (
    "(description=(retry_count=20)(retry_delay=3)"
    "(address=(protocol=tcps)(port=1522)"
    "(host=adb.us-phoenix-1.oraclecloud.com))"
    "(connect_data=(service_name=bk8uwrvkgqzvi2h_adbphx_high.adb.oraclecloud.com))"
    "(security=(ssl_server_dn_match=yes)"
    "(my_wallet_directory=C:\\Users\\Blake\\Downloads\\Wallet_ADBPHX)))"
)

CREDENTIAL_NAME = "OBJ_STORE_CRED"
TABLE_NAME = "CUSTOMER_ORDERS_DEMO"

FILE_URI = (
    "https://objectstorage.us-sanjose-1.oraclecloud.com/p/WJ9GXh4EWOuj5myI-HjzufYbg7H9yu0tnzzLBpsXeXp7u_PsyYzydvE17NttDdlp/"
    "n/oraclepartnersas/b/adb_migration_bucket/o/customer_orders_demo_export*.csv"
)

IMPORT_PLSQL = f"""
BEGIN
  -- Drop external table if it exists
  BEGIN
    EXECUTE IMMEDIATE 'DROP TABLE CO_DEMO_EXT PURGE';
  EXCEPTION
    WHEN OTHERS THEN NULL;
  END;

  -- Create external table over the CSV exported from adb_sanjose
  DBMS_CLOUD.CREATE_EXTERNAL_TABLE(
    table_name      => 'CO_DEMO_EXT',
    file_uri_list   => '{FILE_URI}',
    format        => json_object(
                    'type'        VALUE 'csv',
                    'delimiter'   VALUE ',',
                    'skipheaders' VALUE '1'
                  ),
    column_list     => '
      order_id             NUMBER(38,0),
      customer_id          NUMBER,
      customer_name        VARCHAR2(100),
      customer_email       VARCHAR2(255),
      order_status         VARCHAR2(30),
      order_channel        VARCHAR2(20),
      order_date           DATE,
      order_ts             TIMESTAMP(6) WITH LOCAL TIME ZONE,
      shipping_address     CLOB,
      shipping_city        VARCHAR2(100),
      shipping_state       VARCHAR2(50),
      shipping_postal      VARCHAR2(20),
      shipping_country     VARCHAR2(50),
      shipping_status      VARCHAR2(50),
      order_total          NUMBER(12,2),
      discount_percent     NUMBER(5,2),
      tax_amount           NUMBER(10,2),
      currency_code        CHAR(3),
      payment_method       VARCHAR2(30),
      payment_auth_code    VARCHAR2(32),
      is_fraud_suspected   CHAR(1),
      metadata_json        CLOB,
      product_details_json CLOB,
      customer_notes       CLOB,
      created_at           TIMESTAMP(6),
      updated_at           TIMESTAMP(6)
    '
  );

  -- Truncate the real table to make the demo idempotent
  EXECUTE IMMEDIATE 'TRUNCATE TABLE CUSTOMER_ORDERS_DEMO';

  -- Load data from external table into real table
  INSERT /*+ APPEND */ INTO CUSTOMER_ORDERS_DEMO (
    order_id,
    customer_id,
    customer_name,
    customer_email,
    order_status,
    order_channel,
    order_date,
    order_ts,
    shipping_address,
    shipping_city,
    shipping_state,
    shipping_postal,
    shipping_country,
    shipping_status,
    order_total,
    discount_percent,
    tax_amount,
    currency_code,
    payment_method,
    payment_auth_code,
    is_fraud_suspected,
    metadata_json,
    product_details_json,
    customer_notes,
    created_at,
    updated_at
  )
  SELECT
    order_id,
    customer_id,
    customer_name,
    customer_email,
    order_status,
    order_channel,
    order_date,
    order_ts,
    shipping_address,
    shipping_city,
    shipping_state,
    shipping_postal,
    shipping_country,
    shipping_status,
    order_total,
    discount_percent,
    tax_amount,
    currency_code,
    payment_method,
    payment_auth_code,
    is_fraud_suspected,
    metadata_json,
    product_details_json,
    customer_notes,
    created_at,
    updated_at
  FROM CO_DEMO_EXT;

  COMMIT;

  -- Drop external table now that data is loaded
  EXECUTE IMMEDIATE 'DROP TABLE CO_DEMO_EXT PURGE';
END;
"""


def main() -> None:
    print("Importing ADMIN.CUSTOMER_ORDERS_DEMO into adb_phoenix using DBMS_CLOUD.COPY_DATA...")
    print(f"Source Object Storage file: {FILE_URI}")

    password = getpass.getpass(
        "Enter password for ADMIN on adb_phoenix (adbphx_high): "
    )

    start = time.perf_counter()

    try:
        with oracledb.connect(user="ADMIN", password=password, dsn=ADB_PHX_DSN) as conn:
            with conn.cursor() as cur:
                print("\nCalling DBMS_CLOUD.COPY_DATA (with truncate)...")
                cur.execute(IMPORT_PLSQL)
                print("DBMS_CLOUD.COPY_DATA completed.")

                # Verify target row count
                print("\nVerifying row count in target table...")
                cur.execute(f"SELECT COUNT(*) FROM {TABLE_NAME}")
                (tgt_count,) = cur.fetchone()
                print(f"Target row count in {TABLE_NAME}: {tgt_count}")

    except Exception as e:
        print("An error occurred during import:")
        print(e)
        sys.exit(1)

    elapsed = time.perf_counter() - start
    print(f"\nImport finished in {elapsed:.2f} seconds.")


if __name__ == "__main__":
    main()
