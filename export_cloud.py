"""Export CUSTOMER_ORDERS_DEMO from adb_sanjose to Object Storage using DBMS_CLOUD.EXPORT_DATA.

- Uses OBJ_STORE_CRED (already created) to access Object Storage
- Writes a single CSV file to your adb_migration_bucket
- Exports the entire CUSTOMER_ORDERS_DEMO table
- Prints timing and verifies source row count

Prerequisites:
    pip install oracledb
    OBJ_STORE_CRED exists in adb_sanjose
"""

import getpass
import sys
import time

try:
    import oracledb
except ImportError:
    print("python-oracledb is not installed. Install it with: pip install oracledb")
    sys.exit(1)

# Connection DSN for adb_sanjose (with wallet directory)
ADB_SJ_DSN = (
    "(description=(retry_count=20)(retry_delay=3)"
    "(address=(protocol=tcps)(port=1522)"
    "(host=adb.us-sanjose-1.oraclecloud.com))"
    "(connect_data=(service_name=fp7cb75hkszpygo_adbsj_high.adb.oraclecloud.com))"
    "(security=(ssl_server_dn_match=yes)"
    "(my_wallet_directory=C:\\Users\\Blake\\Downloads\\Wallet_ADBSJ)))"
)

TABLE_NAME = "CUSTOMER_ORDERS_DEMO"

# Target file in Object Storage using PAR URL (no credential needed)
FILE_URI = (
    "https://objectstorage.us-sanjose-1.oraclecloud.com/"
    "p/WJ9GXh4EWOuj5myI-HjzufYbg7H9yu0tnzzLBpsXeXp7u_PsyYzydvE17NttDdlp/"
    "n/oraclepartnersas/b/adb_migration_bucket/o/customer_orders_demo_export.csv"
)

EXPORT_PLSQL = f"""
BEGIN
  DBMS_CLOUD.EXPORT_DATA(
    file_uri_list => '{FILE_URI}',
    query         => 'SELECT * FROM {TABLE_NAME}',
    format        => json_object(
                       'type'      VALUE 'csv',
                       'delimiter' VALUE ','
                     )
  );
END;
"""


def main() -> None:
    print("Exporting ADMIN.CUSTOMER_ORDERS_DEMO from adb_sanjose using DBMS_CLOUD.EXPORT_DATA...")
    print(f"Target Object Storage file: {FILE_URI}")

    password = getpass.getpass(
        "Enter password for ADMIN on adb_sanjose (adbsj_high): "
    )

    start = time.perf_counter()

    try:
        with oracledb.connect(user="ADMIN", password=password, dsn=ADB_SJ_DSN) as conn:
            with conn.cursor() as cur:
                # Verify source row count
                cur.execute(f"SELECT COUNT(*) FROM {TABLE_NAME}")
                (src_count,) = cur.fetchone()
                print(f"Source row count in {TABLE_NAME}: {src_count}")

                print("\nCalling DBMS_CLOUD.EXPORT_DATA...")
                cur.execute(EXPORT_PLSQL)
                print("DBMS_CLOUD.EXPORT_DATA completed.")

    except Exception as e:
        print("An error occurred during export:")
        print(e)
        sys.exit(1)

    elapsed = time.perf_counter() - start
    print(f"\nExport finished in {elapsed:.2f} seconds.")
    print("Check your Object Storage bucket for customer_orders_demo_export.csv.")


if __name__ == "__main__":
    main()
