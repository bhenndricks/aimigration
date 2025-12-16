"""Cleanup script to stop and remove a lingering CO_DEMO_EXPORT Data Pump job in adb_sanjose.

Run this if export_datapump.py reports that job CO_DEMO_EXPORT already exists.

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

# Easy Connect Plus descriptor for adb_sanjose (with wallet directory)
ADB_SJ_DSN = (
    "(description=(retry_count=20)(retry_delay=3)"
    "(address=(protocol=tcps)(port=1522)"
    "(host=adb.us-sanjose-1.oraclecloud.com))"
    "(connect_data=(service_name=fp7cb75hkszpygo_adbsj_high.adb.oraclecloud.com))"
    "(security=(ssl_server_dn_match=yes)"
    "(my_wallet_directory=C:\\Users\\Blake\\Downloads\\Wallet_ADBSJ)))"
)


def main() -> None:
    password = getpass.getpass("Enter password for ADMIN on adb_sanjose: ")

    try:
        with oracledb.connect(user="ADMIN", password=password, dsn=ADB_SJ_DSN) as conn:
            with conn.cursor() as cur:
                print("Checking for existing CO_DEMO_EXPORT job...")

                # Check if job exists
                cur.execute(
                    """
                    SELECT COUNT(*)
                    FROM   dba_datapump_jobs
                    WHERE  job_name  = 'CO_DEMO_EXPORT'
                    AND    owner_name = 'ADMIN'
                    """
                )
                count = cur.fetchone()[0]

                if count == 0:
                    print("No existing job found. Ready to run export.")
                else:
                    print(f"Found {count} existing job(s). Cleaning up...")

                    # Attach to job and stop it with force (immediate=1, keep_master=0)
                    try:
                        cur.execute(
                            """
                            DECLARE
                                h1 NUMBER;
                            BEGIN
                                h1 := DBMS_DATAPUMP.ATTACH('CO_DEMO_EXPORT', 'ADMIN');
                                DBMS_DATAPUMP.STOP_JOB(h1, 1, 0);
                            EXCEPTION
                                WHEN OTHERS THEN
                                    NULL;
                            END;
                            """
                        )
                        print("Job stopped and removed successfully (or did not exist)")
                    except Exception as e:  # pragma: no cover - diagnostic only
                        print(f"Cleanup attempt error: {e}")

                conn.commit()

    except Exception as e:
        print(f"Error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
