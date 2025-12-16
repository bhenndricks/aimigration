"""Setup Object Storage credential and directory in adb_sanjose.

- Creates DBMS_CLOUD credential OBJ_STORE_CRED using OCI username + auth token
- Creates or replaces directory OBJ_DP_DIR pointing to the Object Storage bucket
- Verifies setup via USER_CREDENTIALS and USER_DIRECTORIES

Run this against adb_sanjose BEFORE doing Data Pump export.

Prerequisites:
    pip install oracledb
"""

import getpass
import sys

try:
    import oracledb
except ImportError:
    print("python-oracledb is not installed. Install it with: pip install oracledb")
    sys.exit(1)

# OCI Object Storage configuration
OCI_USERNAME = "blake.hendricks@oracle.com"  # or your user OCID
OCI_AUTH_TOKEN = "KTy}Qd<9_Em3)8z7dqMd"      # auth token, not console password
OCI_NAMESPACE = "oraclepartnersas"
OCI_BUCKET = "adb_migration_bucket"
OCI_REGION = "us-sanjose-1"

OBJECT_STORAGE_BASE_URL = f"https://objectstorage.{OCI_REGION}.oraclecloud.com"
OBJECT_STORAGE_DIR_URL = (
    f"{OBJECT_STORAGE_BASE_URL}/n/{OCI_NAMESPACE}/b/{OCI_BUCKET}/o/"
)

CREDENTIAL_NAME = "OBJ_STORE_CRED"
DIRECTORY_NAME = "OBJ_DP_DIR"

# Easy Connect Plus descriptor for adb_sanjose (with wallet directory)
ADB_SJ_DSN = (
    "(description=(retry_count=20)(retry_delay=3)"
    "(address=(protocol=tcps)(port=1522)"
    "(host=adb.us-sanjose-1.oraclecloud.com))"
    "(connect_data=(service_name=fp7cb75hkszpygo_adbsj_high.adb.oraclecloud.com))"
    "(security=(ssl_server_dn_match=yes)"
    "(my_wallet_directory=C:\\Users\\Blake\\Downloads\\Wallet_ADBSJ)))"
)


CREATE_CRED_PLSQL = f"""
BEGIN
  DBMS_CLOUD.CREATE_CREDENTIAL(
    credential_name => '{CREDENTIAL_NAME}',
    username        => '{OCI_USERNAME}',
    password        => '{OCI_AUTH_TOKEN}'
  );
END;
"""

CREATE_DIR_SQL = f"""
CREATE OR REPLACE DIRECTORY {DIRECTORY_NAME} AS '{OBJECT_STORAGE_DIR_URL}'
"""

CHECK_CRED_SQL = f"""
SELECT credential_name, username
FROM   user_credentials
WHERE  credential_name = '{CREDENTIAL_NAME}'
"""

CHECK_DIR_SQL = f"""
SELECT directory_name, directory_path
FROM   all_directories
WHERE  directory_name = '{DIRECTORY_NAME}'
"""


def main() -> None:
    print("Setting up Object Storage credential and directory in adb_sanjose...")
    password = getpass.getpass(
        "Enter password for ADMIN on adb_sanjose (adbsj_high): "
    )

    try:
        with oracledb.connect(user="ADMIN", password=password, dsn=ADB_SJ_DSN) as conn:
            with conn.cursor() as cur:
                print("\nCreating DBMS_CLOUD credential (OBJ_STORE_CRED)...")
                try:
                    cur.execute(CREATE_CRED_PLSQL)
                    print("Credential created successfully.")
                except Exception as e:
                    print("Warning: error while creating credential (it may already exist):")
                    print(e)

                print("\nCreating or replacing directory OBJ_DP_DIR...")
                cur.execute(CREATE_DIR_SQL)
                print("Directory created/replaced successfully.")

                print("\nVerifying credential...")
                cur.execute(CHECK_CRED_SQL)
                cred_rows = cur.fetchall()
                if cred_rows:
                    for name, user in cred_rows:
                        print(f"  Credential: {name}, Username: {user}")
                else:
                    print("  No credential named OBJ_STORE_CRED found.")

                print("\nVerifying directory...")
                cur.execute(CHECK_DIR_SQL)
                dir_rows = cur.fetchall()
                if dir_rows:
                    for name, path in dir_rows:
                        print(f"  Directory: {name}, Path: {path}")
                else:
                    print("  No directory named OBJ_DP_DIR found.")

                conn.commit()

    except Exception as e:
        print("An error occurred while setting up Object Storage in adb_sanjose:")
        print(e)
        sys.exit(1)


if __name__ == "__main__":
    main()
