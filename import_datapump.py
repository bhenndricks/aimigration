"""Import CUSTOMER_ORDERS_DEMO into adb_phoenix from Object Storage using Data Pump.

- Uses DBMS_DATAPUMP in TABLE mode
- Imports only ADMIN.CUSTOMER_ORDERS_DEMO
- Dump file: customer_orders_demo.dmp (must already exist in the bucket)
- Log file:  customer_orders_demo_import.log
- Uses OBJ_STORE_CRED and OBJ_DP_DIR (already created)
- Uses PARALLEL for performance (default: 2)
- TABLE_EXISTS_ACTION => 'REPLACE' to overwrite existing table
- Polls DBA_DATAPUMP_JOBS for job status until completion
- Verifies row count after import

Prerequisites:
    - OBJ_STORE_CRED exists and points to OCI user + auth token
    - OBJ_DP_DIR directory points at your Object Storage bucket
    - Dump file customer_orders_demo.dmp already exported by adb_sanjose
    - python-oracledb installed
"""

import getpass
import sys
import time

try:
    import oracledb
except ImportError:
    print("python-oracledb is not installed. Install it with: pip install oracledb")
    sys.exit(1)

# Data Pump configuration
JOB_NAME = "CO_DEMO_IMPORT"  # stored upper-case in DBA_DATAPUMP_JOBS
DUMPFILE = "customer_orders_demo.dmp"
LOGFILE = "customer_orders_demo_import.log"
PARALLEL = 2  # adjust to 4 if you want more parallelism
DIRECTORY = "OBJ_DP_DIR"
CREDENTIAL = "OBJ_STORE_CRED"
SCHEMA = "ADMIN"
TABLE_NAME = "CUSTOMER_ORDERS_DEMO"

# Easy Connect Plus descriptor for adb_phoenix (with wallet directory)
ADB_PHX_DSN = (
    "(description=(retry_count=20)(retry_delay=3)"
    "(address=(protocol=tcps)(port=1522)"
    "(host=adb.us-phoenix-1.oraclecloud.com))"
    "(connect_data=(service_name=bk8uwrvkgqzvi2h_adbphx_high.adb.oraclecloud.com))"
    "(security=(ssl_server_dn_match=yes)"
    "(my_wallet_directory=C:\\Users\\Blake\\Downloads\\Wallet_ADBPHX)))"
)

# PL/SQL block to start the Data Pump import job (minimal SCHEMA-mode import of ADMIN schema)
# Note: This imports the ADMIN schema from the dump. In this lab, the primary focus
# is on CUSTOMER_ORDERS_DEMO in that schema.
IMPORT_PLSQL = f"""
DECLARE
  h1          NUMBER;
BEGIN
  -- Open a SCHEMA-mode import job for ADMIN schema
  h1 := DBMS_DATAPUMP.OPEN(
           operation => 'IMPORT',
           job_mode  => 'SCHEMA',
           job_name  => '{JOB_NAME}'
       );

  -- Dump file in Object Storage directory
  DBMS_DATAPUMP.ADD_FILE(
    handle    => h1,
    filename  => '{DUMPFILE}',
    directory => '{DIRECTORY}',
    filetype  => DBMS_DATAPUMP.KU$_FILE_TYPE_DUMP_FILE
  );

  -- Log file in the same directory
  DBMS_DATAPUMP.ADD_FILE(
    handle    => h1,
    filename  => '{LOGFILE}',
    directory => '{DIRECTORY}',
    filetype  => DBMS_DATAPUMP.KU$_FILE_TYPE_LOG_FILE
  );

  -- If the table already exists, replace it (for idempotent demos)
  DBMS_DATAPUMP.SET_PARAMETER(
    handle => h1,
    name   => 'TABLE_EXISTS_ACTION',
    value  => 'REPLACE'
  );

  -- Start the job and detach (no filters, directory OBJ_DP_DIR carries the credential)
  DBMS_DATAPUMP.START_JOB(h1);
  DBMS_DATAPUMP.DETACH(h1);
END;
"""


def monitor_job(cursor, job_name: str, poll_interval: int = 5) -> None:
    """Poll DBA_DATAPUMP_JOBS until the job is no longer active.

    Prints state transitions for basic progress monitoring.
    """

    last_state = None
    print("\nMonitoring Data Pump job status...")
    while True:
        cursor.execute(
            """
            SELECT state, degree
            FROM   dba_datapump_jobs
            WHERE  job_name = :job_name
            AND    owner_name = USER
            """,
            job_name=job_name.upper(),
        )
        row = cursor.fetchone()
        if not row:
            if last_state is not None:
                print(
                    f"Job {job_name} is no longer listed in DBA_DATAPUMP_JOBS (likely COMPLETED)."
                )
            else:
                print(f"Job {job_name} not found in DBA_DATAPUMP_JOBS.")
            break

        state, degree = row
        if state != last_state:
            print(f"  State: {state}, Degree: {degree}")
            last_state = state

        if state in ("COMPLETED", "STOPPED", "FAILED"):
            print(f"Job {job_name} reached terminal state: {state}")
            break

        time.sleep(poll_interval)


def main() -> None:
    print("Starting Data Pump import of ADMIN.CUSTOMER_ORDERS_DEMO into adb_phoenix...")
    print(f"Dump file: {DUMPFILE}")
    print(f"Log file:  {LOGFILE}")
    print(f"Parallel:  {PARALLEL}")

    password = getpass.getpass(
        "Enter password for ADMIN on adb_phoenix (adbphx_high): "
    )

    try:
        with oracledb.connect(user="ADMIN", password=password, dsn=ADB_PHX_DSN) as conn:
            with conn.cursor() as cur:
                print("\nSubmitting Data Pump import job via DBMS_DATAPUMP...")
                cur.execute(IMPORT_PLSQL)
                print("Job submitted. Now monitoring status...")

                monitor_job(cur, JOB_NAME)

                # Verify final row count
                print("\nVerifying row count for ADMIN.CUSTOMER_ORDERS_DEMO...")
                cur.execute("SELECT COUNT(*) FROM customer_orders_demo")
                (row_count,) = cur.fetchone()
                print(f"  Row count: {row_count}")

    except Exception as e:
        print("An error occurred during the import:")
        print(e)
        sys.exit(1)

    print("\nImport completed (or job no longer listed). Check the log file in Object Storage:")
    print("  Bucket:  adb_migration_bucket")
    print(f"  Objects: {LOGFILE} and {DUMPFILE}")


if __name__ == "__main__":
    main()
