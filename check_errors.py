"""Check COPY_DATA error log - see more records"""
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

password = getpass.getpass("Enter password: ")

with oracledb.connect(user="ADMIN", password=password, dsn=ADB_PHX_DSN) as conn:
    with conn.cursor() as cur:
        # Find the latest error log table
        cur.execute("""
            SELECT table_name 
            FROM user_tables 
            WHERE table_name LIKE 'COPY$%LOG'
            ORDER BY table_name DESC
        """)
        
        log_table = cur.fetchone()[0]
        print(f"Checking {log_table}...")
        print("="*80)
        
        # Get all records
        cur.execute(f"SELECT RECORD FROM {log_table}")
        
        for i, (record,) in enumerate(cur, 1):
            if record:
                print(f"{i}: {record}")