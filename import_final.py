"""Import using DBMS_CLOUD.COPY_DATA with proper CSV format"""
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

TABLE_NAME = "CUSTOMER_ORDERS_DEMO"

FILE_URI = (
    "https://objectstorage.us-sanjose-1.oraclecloud.com/p/WJ9GXh4EWOuj5myI-HjzufYbg7H9yu0tnzzLBpsXeXp7u_PsyYzydvE17NttDdlp/"
    "n/oraclepartnersas/b/adb_migration_bucket/o/customer_orders_demo_export*.csv"
)

print("Import with proper CSV format handling for CLOBs")
print(f"Source: {FILE_URI}")

password = getpass.getpass("Enter password: ")

try:
    with oracledb.connect(user="ADMIN", password=password, dsn=ADB_PHX_DSN) as conn:
        with conn.cursor() as cur:
            print("\n[1/2] Truncating table...")
            cur.execute(f"TRUNCATE TABLE {TABLE_NAME}")
            
            print("[2/2] Loading data with proper format...")
            cur.execute(f"""
                BEGIN
                  DBMS_CLOUD.COPY_DATA(
                    table_name => '{TABLE_NAME}',
                    file_uri_list => '{FILE_URI}',
                    format => json_object(
                      'type' VALUE 'csv',
                      'skipheaders' VALUE '1',
                      'blankasnull' VALUE 'true',
                      'trimspaces' VALUE 'lrtrim',
                      'truncatecol' VALUE 'true',
                      'ignoremissingcolumns' VALUE 'true'
                    )
                  );
                END;
            """)
            
            conn.commit()
            
            print("\n[3/3] Verifying...")
            cur.execute(f"SELECT COUNT(*) FROM {TABLE_NAME}")
            count = cur.fetchone()[0]
            
            if count > 0:
                print(f"\n✓ SUCCESS! {count} rows imported into {TABLE_NAME}")
            else:
                print("\n⚠ Table is empty after import")

except Exception as e:
    print(f"\n❌ ERROR: {e}")
    sys.exit(1)