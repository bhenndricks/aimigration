"""Import without CLOB columns - they're causing the CSV parsing issues"""
import getpass
import sys
import oracledb

ADB_PHX_DSN = (
    "(description=(retry_count=20)(retry_delay=3)"
    "(address=(protocol=tcps)(port=1522)"
    "(host=adb.us-phoenix-1.oraclecloud.com))"
    "(connect_data=(service_name=bk8uwrvkgqzvi2h_adbphx_high.adb.oraclecloud.com))"
    "(security=(ssl_server_dn_match=yes)"
    "(my_wallet_directory=C:\\Users\\Blake\\Downloads\\Wallet_ADBPHX)))"
)

FILE_URI = (
    "https://objectstorage.us-sanjose-1.oraclecloud.com/p/WJ9GXh4EWOuj5myI-HjzufYbg7H9yu0tnzzLBpsXeXp7u_PsyYzydvE17NttDdlp/"
    "n/oraclepartnersas/b/adb_migration_bucket/o/customer_orders_clean_1_20251216T132352037130Z.csv"
)

password = getpass.getpass("Enter password: ")

try:
    with oracledb.connect(user="ADMIN", password=password, dsn=ADB_PHX_DSN) as conn:
        with conn.cursor() as cur:
            print("[1/4] Creating staging table without CLOBs...")
            cur.execute("""
                CREATE TABLE customer_orders_stage (
                    order_id              NUMBER,
                    customer_id           NUMBER,
                    customer_name         VARCHAR2(100),
                    customer_email        VARCHAR2(255),
                    order_status          VARCHAR2(30),
                    order_channel         VARCHAR2(20),
                    order_date            DATE,
                    order_ts              TIMESTAMP(6) WITH LOCAL TIME ZONE,
                    shipping_city         VARCHAR2(100),
                    shipping_state        VARCHAR2(50),
                    shipping_postal       VARCHAR2(20),
                    shipping_country      VARCHAR2(50),
                    shipping_status       VARCHAR2(50),
                    order_total           NUMBER(12,2),
                    discount_percent      NUMBER(5,2),
                    tax_amount            NUMBER(10,2),
                    currency_code         CHAR(3),
                    payment_method        VARCHAR2(30),
                    payment_auth_code     VARCHAR2(32),
                    is_fraud_suspected    CHAR(1),
                    created_at            TIMESTAMP(6),
                    updated_at            TIMESTAMP(6)
                )
            """)
            print("✓ Staging table created")
            
            print("\n[2/4] Loading non-CLOB data...")
            cur.execute(f"""
                BEGIN
                  DBMS_CLOUD.COPY_DATA(
                    table_name => 'CUSTOMER_ORDERS_STAGE',
                    file_uri_list => '{FILE_URI}',
                    format => json_object(
                      'type' VALUE 'csv',
                      'skipheaders' VALUE '1',
                      'ignoremissingcolumns' VALUE 'true',
                      'blankasnull' VALUE 'true'
                    )
                  );
                END;
            """)
            print("✓ Data loaded into staging")
            
            print("\n[3/4] Copying to final table (without CLOBs)...")
            cur.execute("TRUNCATE TABLE customer_orders_demo")
            cur.execute("""
                INSERT INTO customer_orders_demo (
                    order_id, customer_id, customer_name, customer_email,
                    order_status, order_channel, order_date, order_ts,
                    shipping_city, shipping_state, shipping_postal, shipping_country,
                    shipping_status, order_total, discount_percent, tax_amount,
                    currency_code, payment_method, payment_auth_code,
                    is_fraud_suspected, created_at, updated_at
                )
                SELECT
                    order_id, customer_id, customer_name, customer_email,
                    order_status, order_channel, order_date, order_ts,
                    shipping_city, shipping_state, shipping_postal, shipping_country,
                    shipping_status, order_total, discount_percent, tax_amount,
                    currency_code, payment_method, payment_auth_code,
                    is_fraud_suspected, created_at, updated_at
                FROM customer_orders_stage
            """)
            rows = cur.rowcount
            print(f"✓ Copied {rows} rows")
            
            print("\n[4/4] Cleanup...")
            cur.execute("DROP TABLE customer_orders_stage PURGE")
            
            conn.commit()
            
            cur.execute("SELECT COUNT(*) FROM customer_orders_demo")
            count = cur.fetchone()[0]
            print(f"\n✓ SUCCESS! {count} rows imported (CLOB columns will be NULL)")

except Exception as e:
    print(f"\n❌ ERROR: {e}")
    try:
        with oracledb.connect(user="ADMIN", password=password, dsn=ADB_PHX_DSN) as conn:
            conn.cursor().execute("DROP TABLE customer_orders_stage PURGE")
    except:
        pass
    sys.exit(1)