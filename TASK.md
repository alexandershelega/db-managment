Database Management Scripts Implementation Plan
1. Project Structure Setup
Create directory structure:
db-management/
├── scripts/
│   ├── mysql_sync.py           # MySQL-only user sync
│   ├── postgresql_sync.py      # PostgreSQL-only user sync
│   ├── clickhouse_sync.py      # ClickHouse-only user sync
│   ├── mongodb_sync.py         # MongoDB-only user sync
│   └── utils/                  # Database handler modules
├── config/
│   ├── users.txt               # List of developers with passwords (source of truth)
│   ├── mysql_databases.txt     # MySQL template database names
│   ├── postgresql_databases.txt
│   ├── clickhouse_databases.txt
│   ├── mongodb_databases.txt
│   └── connections.yaml        # Connection strings for all databases
└── requirements.txt
2. Configuration Files Design
users.txt format:

Format: username:password (one per line)
Example:

  developer1:MySecurePass123!
  developer2:AnotherPass456@
  qa_user:TestPassword789#

Source of truth for user management
Adding user line = creates all their databases with specified password
Removing user line = deletes all their databases
Changing password = updates user password in database

Database list files format:

One template database name per line per file type
Example: mysql_databases.txt contains: tools, web, analytics
These are templates for creating user-specific databases

connections.yaml format:

YAML structure with connection configs for each DB type
Include host, port, username, password, additional params
Only destination database configs needed

3. Database Handler Classes
Create separate handler classes for each database type:
MySQLHandler:

Methods: get_existing_users(), get_existing_databases(), create_user(), create_database(), grant_privileges(), drop_user(), drop_database(), update_user_password()
Handle MySQL-specific syntax and connection parameters
Methods to query existing state for synchronization
New: Password management methods

PostgreSQLHandler:

Handle PostgreSQL user/database creation with ownership
Manage connection isolation levels for DDL operations
Methods to list existing users and databases for sync
New: PostgreSQL password update methods

ClickHouseHandler:

Implement ClickHouse-specific user/database management
Handle ClickHouse permissions system
Query existing state for synchronization
New: ClickHouse password management

MongoDBHandler:

Manage MongoDB users with role-based permissions
Handle authentication database specifications
List existing users and databases for sync
New: MongoDB password update methods

4. User Configuration Parsing
User Data Structure:
python# Example parsed user data
users = {
    'developer1': 'MySecurePass123!',
    'developer2': 'AnotherPass456@',
    'qa_user': 'TestPassword789#'
}
Parsing Logic:

Read users.txt line by line
Split each line on ':' delimiter
Validate username and password format
Handle parsing errors gracefully
Support comments (lines starting with #)

Password Validation:

Minimum length requirements per database type
Character set validation
Database-specific password policy compliance
Clear error messages for invalid passwords

5. Individual Database Sync Scripts
Each database type has its own standalone sync script that operates independently
mysql_sync.py:

Purpose: Synchronize MySQL users/databases with users.txt
Arguments: --config-path, --dry-run
Logic:

Parse users.txt to get desired users with passwords
Read template databases from mysql_databases.txt
Query existing MySQL users matching managed pattern
Query existing databases matching {user}_{template} pattern
Calculate differences:

Users to add (in file, not in database)
Users to remove (in database, not in file)
Users with password changes
Databases to add/remove


Execute sync operations to match desired state


Independent operation: Works only with MySQL

postgresql_sync.py:

Purpose: Synchronize PostgreSQL users/databases with users.txt
Arguments: --config-path, --dry-run
Logic:

Parse users.txt to get desired users with passwords
Read template databases from postgresql_databases.txt
Query existing PostgreSQL roles and databases
Compare current state with desired state
Execute sync operations (create/drop/update users and databases)


Independent operation: Works only with PostgreSQL

clickhouse_sync.py:

Purpose: Synchronize ClickHouse users/databases with users.txt
Arguments: --config-path, --dry-run
Logic:

Parse users.txt to get desired users with passwords
Read template databases from clickhouse_databases.txt
Query existing ClickHouse users and databases
Calculate required changes including password updates
Execute synchronization operations


Independent operation: Works only with ClickHouse

mongodb_sync.py:

Purpose: Synchronize MongoDB users/databases with users.txt
Arguments: --config-path, --dry-run
Logic:

Parse users.txt to get desired users with passwords
Read template databases from mongodb_databases.txt
Query existing MongoDB users and databases
Compare with desired state including password verification
Execute MongoDB-specific sync operations


Independent operation: Works only with MongoDB

6. Enhanced Synchronization Algorithm
Core Logic (same for all scripts):
python# Read desired state
desired_users = parse_users_file()  # Returns dict {username: password}
template_databases = read_template_databases()

# Query current state  
current_managed_users = get_managed_users_from_database()
current_managed_databases = get_managed_databases_from_database()

# Calculate changes needed
users_to_add = set(desired_users.keys()) - current_managed_users
users_to_remove = current_managed_users - set(desired_users.keys())
users_to_update = []

# Check for password changes
for username in set(desired_users.keys()) & current_managed_users:
    if password_needs_update(username, desired_users[username]):
        users_to_update.append(username)

# Execute changes
for username in users_to_add:
    password = desired_users[username]
    create_user(username, password)
    for template_db in template_databases:
        db_name = f"{username}_{template_db}"
        create_database(db_name)
        grant_full_privileges(username, db_name)

for username in users_to_update:
    update_user_password(username, desired_users[username])

for username in users_to_remove:
    for template_db in template_databases:
        db_name = f"{username}_{template_db}"
        drop_database(db_name)
    drop_user(username)
7. Password Management
Password Security:

Support for complex passwords with special characters
Database-specific password policy enforcement
Secure password transmission to databases
No password logging in plain text

Password Updates:

Detect when user password has changed in users.txt
Update existing user passwords in database
Validate password before applying changes
Handle password update failures gracefully

Password Storage:

Important: users.txt contains plain text passwords
File should have restricted permissions (600)
Consider encryption for users.txt file
Document security requirements for file handling

8. Script Independence Requirements
Standalone Operation:

Each script operates completely independently
No cross-database dependencies or communication
Can run when other database systems are unavailable
Separate configuration validation for each database type

Dependency Isolation:

mysql_sync.py requires only PyMySQL + PyYAML
postgresql_sync.py requires only psycopg2 + PyYAML
mongodb_sync.py requires only pymongo + PyYAML
clickhouse_sync.py requires only clickhouse-driver + PyYAML

Configuration Independence:

Each script reads only its relevant config sections
Validates only required connection parameters
Gracefully handles missing config for other database types

9. Error Handling Strategy
Sync Failures:

Continue processing other users if one user operation fails
Detailed error reporting per user/database operation
Support partial synchronization completion
Rollback failed operations where possible

Password Validation Errors:

Validate password format before database operations
Clear error messages for password policy violations
Skip users with invalid passwords, continue with others

File Parsing Errors:

Handle malformed lines in users.txt gracefully
Report line numbers for parsing errors
Continue processing valid lines

10. Security Considerations
File Security:

users.txt should have restricted file permissions (600 or 640)
Store in secure location with limited access
Consider encrypting users.txt file
Document security requirements clearly

Password Security:

Support strong password requirements
Validate passwords against database policies
Secure transmission of passwords to databases
No password logging in plain text

Access Control:

Validate administrative privileges before sync operations
Use principle of least privilege for created users
Audit trail for all user/database operations (without passwords)

11. Usage Examples
Basic Operations:
bash# Sync MySQL based on current users.txt
python mysql_sync.py --config config/

# Sync PostgreSQL based on current users.txt  
python postgresql_sync.py --config config/

# Dry run to see what MySQL changes would be made
python mysql_sync.py --config config/ --dry-run

# Sync all database types (run each script)
python mysql_sync.py --config config/
python postgresql_sync.py --config config/
python clickhouse_sync.py --config config/
python mongodb_sync.py --config config/
users.txt Management:
bash# Add new developer with password
echo "new_developer:SecurePass123!" >> config/users.txt

# Update existing user password (edit file)
sed -i 's/old_developer:old_pass/old_developer:new_pass/' config/users.txt

# Remove developer (removes line from file)
sed -i '/old_developer:/d' config/users.txt

# After any change, sync databases
python mysql_sync.py --config config/
```

## 12. Dependencies and Installation

### Per-Script Dependencies:
```
mysql_sync.py:
- PyMySQL==1.0.2
- PyYAML==6.0

postgresql_sync.py:  
- psycopg2-binary==2.9.5
- PyYAML==6.0

mongodb_sync.py:
- pymongo==4.3.3
- PyYAML==6.0

clickhouse_sync.py:
- clickhouse-driver==0.2.5
- PyYAML==6.0
File Permissions Setup:
bash# Secure users.txt file
chmod 600 config/users.txt
chown admin_user:admin_group config/users.txt
13. Testing and Validation
User File Testing:

Test various username:password formats
Verify password special character handling
Test malformed line handling
Validate password update detection

Sync Logic Validation:

Verify users.txt changes result in correct database operations
Test password updates work correctly
Test edge cases (empty files, duplicate names, special characters in passwords)
Validate dry-run accuracy compared to actual operations

Security Testing:

Verify passwords are not logged in plain text
Test file permission requirements
Validate password policy enforcement

This approach provides password-aware user management where the users.txt file contains both usernames and their desired passwords, allowing for complete user lifecycle management including password updates.