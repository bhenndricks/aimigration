# Oracle Autonomous Database Migration Demonstration

A comprehensive demonstration of migrating data between Oracle Autonomous Database instances using Oracle Data Pump and OCI Object Storage, specifically designed to showcase Oracle ADB capabilities and AI-assisted database operations.

## Overview

This project demonstrates a production-ready approach to migrating data between Oracle Autonomous Database (ADB) instances across different OCI regions. The solution leverages OCI Object Storage as an intermediary staging area and uses Oracle Data Pump for efficient data export and import operations.

**Key Highlights:**
- Migration of 50,000+ row dataset between ADB instances
- Cross-region migration capability (San Jose to Phoenix regions)
- Python-based automation for consistency and reliability
- Pre-Authenticated Request (PAR) approach for simplified authentication
- Complete end-to-end workflow documentation

## Architecture

```
Source ADB (Region 1)
    ↓
    ↓ [Data Pump Export]
    ↓
OCI Object Storage Bucket (with PAR)
    ↓
    ↓ [Data Pump Import]
    ↓
Target ADB (Region 2)
```

## Prerequisites

### Oracle Cloud Infrastructure
- Two Oracle Autonomous Database instances (source and target)
- OCI Object Storage bucket
- Database wallet files for both ADB instances
- Appropriate OCI permissions for Object Storage operations

### Local Development Environment
- Python 3.x
- Oracle SQLcl or SQL*Plus
- VS Code (recommended) with Python extension
- Oracle Instant Client (if using SQL*Plus)

### Python Libraries
```bash
pip install oracledb
pip install python-dotenv  # for environment variable management
```

## Setup Instructions

### 1. Database Wallet Configuration

Download and configure wallet files for both source and target databases:

```bash
# Create wallet directories
mkdir -p ~/wallets/source_db
mkdir -p ~/wallets/target_db

# Extract wallet files
unzip Wallet_SourceDB.zip -d ~/wallets/source_db/
unzip Wallet_TargetDB.zip -d ~/wallets/target_db/
```

Update `sqlnet.ora` in each wallet directory with the correct path:
```
WALLET_LOCATION = (SOURCE = (METHOD = file) (METHOD_DATA = (DIRECTORY="/path/to/wallet")))
SSL_SERVER_DN_MATCH=yes
```

### 2. OCI Object Storage Setup

Create a bucket and generate a Pre-Authenticated Request (PAR):

```sql
-- In OCI Console:
-- 1. Navigate to Object Storage
-- 2. Create a bucket (e.g., "migration-staging")
-- 3. Generate PAR with read/write permissions
-- 4. Save the PAR URL for use in scripts
```

### 3. Environment Configuration

Create a `.env` file for sensitive credentials:

```bash
# Source Database
SOURCE_USER=ADMIN
SOURCE_PASSWORD=your_source_password
SOURCE_DSN=source_db_high

# Target Database
TARGET_USER=ADMIN
TARGET_PASSWORD=your_target_password
TARGET_DSN=target_db_high

# OCI Object Storage
OCI_PAR_URL=https://objectstorage.region.oraclecloud.com/p/xxx/n/xxx/b/bucket/o/
```

## Usage

### Export from Source Database

```python
import oracledb
import os
from dotenv import load_dotenv

load_dotenv()

# Configure wallet location
oracledb.init_oracle_client(
    config_dir="/path/to/wallet/source_db"
)

# Connect to source database
connection = oracledb.connect(
    user=os.getenv('SOURCE_USER'),
    password=os.getenv('SOURCE_PASSWORD'),
    dsn=os.getenv('SOURCE_DSN')
)

cursor = connection.cursor()

# Export using Data Pump with PAR
export_sql = """
BEGIN
    DBMS_CLOUD.EXPORT_DATA(
        credential_name => NULL,
        file_uri_list => 'https://your-par-url/export_data.dmp',
        format => json_object('type' value 'datapump'),
        query => 'SELECT * FROM your_schema.your_table'
    );
END;
"""

cursor.execute(export_sql)
connection.commit()

print("Export completed successfully!")

cursor.close()
connection.close()
```

### Import to Target Database

```python
import oracledb
import os
from dotenv import load_dotenv

load_dotenv()

# Configure wallet location
oracledb.init_oracle_client(
    config_dir="/path/to/wallet/target_db"
)

# Connect to target database
connection = oracledb.connect(
    user=os.getenv('TARGET_USER'),
    password=os.getenv('TARGET_PASSWORD'),
    dsn=os.getenv('TARGET_DSN')
)

cursor = connection.cursor()

# Create target table if needed
create_table_sql = """
CREATE TABLE your_schema.your_table (
    -- Define columns matching source structure
    id NUMBER PRIMARY KEY,
    name VARCHAR2(100),
    created_date DATE
)
"""
cursor.execute(create_table_sql)

# Import using Data Pump with PAR
import_sql = """
BEGIN
    DBMS_CLOUD.IMPORT_DATA(
        table_name => 'YOUR_TABLE',
        credential_name => NULL,
        file_uri_list => 'https://your-par-url/export_data.dmp',
        format => json_object('type' value 'datapump')
    );
END;
"""

cursor.execute(import_sql)
connection.commit()

print("Import completed successfully!")

cursor.close()
connection.close()
```

## Key Learnings

### Authentication Approach

After extensive troubleshooting with traditional Data Pump credential methods (ORA-39001 errors), we discovered that **Pre-Authenticated Requests (PAR)** provide a simpler and more reliable approach:

- **Traditional approach challenges:** Creating OCI credentials with `DBMS_CLOUD.CREATE_CREDENTIAL` often encountered authentication issues
- **PAR solution:** Using `credential_name => NULL` with PAR URLs bypasses credential complexity
- **Benefits:** Simpler setup, fewer points of failure, easier troubleshooting

### Development Best Practices

1. **Plan Mode over Autonomous Execution:** For critical database operations, always review plans before execution
2. **Python for Automation:** Python scripts provide better consistency and repeatability than manual SQL execution
3. **Single Session Context:** Complete related operations in one development session to maintain context
4. **Wallet Configuration:** Ensure `sqlnet.ora` paths are correctly configured for each database connection

### Performance Considerations

- Export operations on 50,000 rows completed efficiently with Data Pump
- OCI Object Storage provides reliable intermediary staging with cross-region support
- Monitor `DBA_DATAPUMP_JOBS` view for operation status and troubleshooting

## Troubleshooting

### Common Issues

**ORA-39001: invalid argument value**
- Solution: Switch to PAR-based authentication instead of credential objects
- Verify PAR URL has correct read/write permissions

**Wallet Connection Issues**
- Verify `sqlnet.ora` DIRECTORY path is absolute and correct
- Check wallet files are properly extracted and unzipped
- Ensure TNS_ADMIN environment variable points to wallet directory

**DBMS_CLOUD Package Not Found**
- Verify you're connected to an Autonomous Database instance
- Ensure proper schema permissions for DBMS_CLOUD operations

**Network Access Issues**
- Confirm database network access is properly configured
- Check OCI security lists and network security groups
- Verify PAR hasn't expired

## Monitoring and Validation

### Check Export/Import Status

```sql
-- Monitor Data Pump jobs
SELECT * FROM DBA_DATAPUMP_JOBS;

-- Verify record counts
SELECT COUNT(*) FROM source_schema.source_table;
SELECT COUNT(*) FROM target_schema.target_table;

-- Check DBMS_CLOUD operations
SELECT * FROM USER_LOAD_OPERATIONS
ORDER BY start_time DESC;
```

## Production Considerations

### For Enterprise Deployments

- **Oracle GoldenGate:** Consider for real-time replication and minimal downtime
- **OCI Database Migration Service:** Automated solution for complex migrations
- **Incremental Migrations:** Use Oracle's change data capture for large datasets
- **Backup Strategy:** Always maintain backups before migration operations

### Security Best Practices

- Use IAM policies to restrict Object Storage access
- Generate time-limited PARs for migration windows
- Rotate database passwords after migration
- Encrypt sensitive data in transit and at rest
- Audit all DBMS_CLOUD operations

## Project Structure

```
.
├── README.md
├── .env.example
├── scripts/
│   ├── export_data.py
│   ├── import_data.py
│   ├── verify_migration.py
│   └── cleanup.py
├── wallets/
│   ├── source_db/
│   └── target_db/
└── docs/
    ├── architecture.md
    └── troubleshooting.md
```

## Use Cases

This demonstration is ideal for:

- **Product Demonstrations:** Showcasing Oracle ADB capabilities to stakeholders
- **Technical Evaluations:** Proving migration approaches before production implementation
- **Training and Education:** Teaching database migration best practices
- **POC Development:** Rapid prototyping of migration workflows
- **AI-Assisted Operations:** Demonstrating AI integration with database operations

## Additional Resources

- [Oracle Autonomous Database Documentation](https://docs.oracle.com/en/cloud/paas/autonomous-database/)
- [DBMS_CLOUD Package Reference](https://docs.oracle.com/en/cloud/paas/autonomous-database/adbsa/dbms-cloud-package.html)
- [Oracle Data Pump Documentation](https://docs.oracle.com/en/database/oracle/oracle-database/19/sutil/oracle-data-pump.html)
- [OCI Object Storage Documentation](https://docs.oracle.com/en-us/iaas/Content/Object/home.htm)

## Contributing

This project serves as a demonstration and reference implementation. For suggestions or improvements:

1. Review the existing implementation
2. Test changes in a non-production environment
3. Document any modifications or enhancements
4. Share learnings with the team

## License

This demonstration project is provided as-is for educational and evaluation purposes within Oracle product management and development teams.

## Contact

For questions or discussions about this migration demonstration, please reach out to the Oracle Autonomous Database Product Management team.

---

**Note:** This project demonstrates AI-assisted database operations and showcases Oracle ADB capabilities. Always follow your organization's security policies and change management procedures when implementing in production environments.
