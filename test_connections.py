"""Simple script to test connections to two Autonomous Databases.

- Prompts for ADMIN passwords for both databases using getpass.getpass()
- Connects to each DB using the given wallet directories and TNS aliases
- Executes SELECT 1 FROM DUAL on each
- Prints clear success/failure messages and exits with non-zero status if any test fails

Prerequisites:
    pip install oracledb

Adjust wallet paths and TNS aliases below if your environment differs.
"""

import getpass
import sys

try:
    import oracledb
except ImportError as exc:  # pragma: no cover - environment-specific
    print("python-oracledb is not installed.")
    print("Install it with: pip install oracledb")
    sys.exit(1)


def test_db_connection(label: str, user: str, password: str, dsn: str) -> bool:
    """Test a single database connection by running SELECT 1 FROM DUAL.

    Args:
        label: Human-readable label for the database (for logging).
        user: Database username.
        password: Database password.
        dsn: Full Easy Connect Plus-style connect descriptor.

    Returns:
        True if connection and query succeed, False otherwise.
    """

    print(f"\nTesting connection to {label}...")

    try:
        with oracledb.connect(
            user=user,
            password=password,
            dsn=dsn,
        ) as conn:
            with conn.cursor() as cur:
                cur.execute("SELECT 1 FROM DUAL")
                row = cur.fetchone()
                print(f"{label}: query result = {row[0]}")

        print(f"{label}: SUCCESS")
        return True

    except Exception as e:  # pragma: no cover - for manual diagnostics
        print(f"{label}: FAILED")
        print(f"Error: {e}")
        return False


def main() -> None:
    # Prompt for passwords without echoing
    print("This script will test connectivity to two Autonomous Databases.")
    print("Passwords will not be echoed.")

    sj_password = getpass.getpass(
        "Enter password for ADMIN on adb_sanjose (adbsj_high): "
    )
    phx_password = getpass.getpass(
        "Enter password for ADMIN on adb_phoenix (adbphx_high): "
    )

    user = "ADMIN"

    # Full Easy Connect Plus-style connect descriptors (include wallet directory)
    sj_dsn = "(description=(retry_count=20)(retry_delay=3)(address=(protocol=tcps)(port=1522)(host=adb.us-sanjose-1.oraclecloud.com))(connect_data=(service_name=fp7cb75hkszpygo_adbsj_high.adb.oraclecloud.com))(security=(ssl_server_dn_match=yes)(my_wallet_directory=C:\\Users\\Blake\\Downloads\\Wallet_ADBSJ)))"

    phx_dsn = "(description=(retry_count=20)(retry_delay=3)(address=(protocol=tcps)(port=1522)(host=adb.us-phoenix-1.oraclecloud.com))(connect_data=(service_name=bk8uwrvkgqzvi2h_adbphx_high.adb.oraclecloud.com))(security=(ssl_server_dn_match=yes)(my_wallet_directory=C:\\Users\\Blake\\Downloads\\Wallet_ADBPHX)))"

    # Test both connections
    sj_ok = test_db_connection(
        "adb_sanjose (adbsj_high)", user, sj_password, sj_dsn
    )
    phx_ok = test_db_connection(
        "adb_phoenix (adbphx_high)", user, phx_password, phx_dsn
    )

    print("\nSummary:")
    print(f"  San Jose:  {'OK' if sj_ok else 'FAILED'}")
    print(f"  Phoenix:   {'OK' if phx_ok else 'FAILED'}")

    if not (sj_ok and phx_ok):
        sys.exit(1)


if __name__ == "__main__":
    main()
