"""Drop external table and create regular table in adb_phoenix"""
import getpass
import oracledb

ADB_PHX_DSN = (
    "(description=(retry_count=20)(retry_delay=3)"
    "(address=(protocol=tcps)(port=1522)"
    "(host=adb.us-phoenix-1.oraclecloud.com))"
    "(connect_data=(service_name=bk8uwrvkgqzvi2h_adbphx_high.adb.oraclecloud.com))"
    "(security=(ssl_server_dn_match=yes)"
    "(my_wallet_directory=C:\\Users\\Blake\\Downloads\\Wallet_ADBPHX)))"
)

password = getpass.getpass("Enter password for adb_phoenix: ")

try:
    with oracledb.connect(user="ADMIN", password=password, dsn=ADB_PHX_DSN) as conn:
        with conn.cursor() as cur:
            print("Dropping CUSTOMER_ORDERS_DEMO (external table)...")
            cur.execute("DROP TABLE CUSTOMER_ORDERS_DEMO PURGE")
            print("✓ Dropped")
            
            print("\nCreating CUSTOMER_ORDERS_DEMO as regular table...")
            cur.execute("""
                CREATE TABLE customer_orders_demo (
                    order_id              NUMBER,
                    customer_id           NUMBER NOT NULL,
                    customer_name         VARCHAR2(100) NOT NULL,
                    customer_email        VARCHAR2(255) NOT NULL,
                    order_status          VARCHAR2(30) NOT NULL,
                    order_channel         VARCHAR2(20),
                    order_date            DATE NOT NULL,
                    order_ts              TIMESTAMP(6) WITH LOCAL TIME ZONE NOT NULL,
                    shipping_address      CLOB,
                    shipping_city         VARCHAR2(100),
                    shipping_state        VARCHAR2(50),
                    shipping_postal       VARCHAR2(20),
                    shipping_country      VARCHAR2(50),
                    shipping_status       VARCHAR2(50),
                    order_total           NUMBER(12,2) NOT NULL,
                    discount_percent      NUMBER(5,2),
                    tax_amount            NUMBER(10,2),
                    currency_code         CHAR(3) NOT NULL,
                    payment_method        VARCHAR2(30),
                    payment_auth_code     VARCHAR2(32),
                    is_fraud_suspected    CHAR(1) NOT NULL,
                    metadata_json         CLOB,
                    product_details_json  CLOB,
                    customer_notes        CLOB,
                    created_at            TIMESTAMP(6),
                    updated_at            TIMESTAMP(6),
                    CONSTRAINT co_demo_pk PRIMARY KEY (order_id)
                )
            """)
            print("✓ Created as regular table")
            
            conn.commit()
            print("\n✓ Table is now ready for COPY_DATA import!")

except Exception as e:
    print(f"❌ ERROR: {e}")