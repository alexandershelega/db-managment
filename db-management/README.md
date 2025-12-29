# Database User Sync Scripts

Completely independent, password-aware synchronization scripts for managing developer users and their per-template databases across MySQL, PostgreSQL, ClickHouse, and MongoDB.

## Highlights
- Single source of truth: `config/users.txt` (`username:password` per line, comments supported).
- Per-DB templates: databases created as `<username>_<template>` for each template in `config/*_databases.txt`.
- Idempotent sync: calculates adds, removals, and password updates; safe to re-run.
- Independent scripts: each DB has its own script and dependencies; no cross-DB coupling.
- Dry-run mode: preview operations without executing changes.
- Security-aware: password validation, least privilege grants, no plaintext password logging.

## Directory Structure
```
db-management/
├── scripts/
│   ├── mysql_sync.py
│   ├── postgresql_sync.py
│   ├── clickhouse_sync.py
│   ├── mongodb_sync.py
│   └── utils/
│       ├── common.py
│       ├── mysql_handler.py
│       ├── postgresql_handler.py
│       ├── clickhouse_handler.py
│       └── mongodb_handler.py
├── config/
│   ├── users.txt
│   ├── mysql_databases.txt
│   ├── postgresql_databases.txt
│   ├── clickhouse_databases.txt
│   ├── mongodb_databases.txt
│   └── connections.yaml
└── requirements.txt
```

## Supported Databases
- MySQL (`PyMySQL`)
- PostgreSQL (`psycopg2-binary`)
- ClickHouse (`clickhouse-driver`)
- MongoDB (`pymongo`)

## Installation

### Using Virtual Environment (Recommended)
To avoid installing dependencies globally, use a virtual environment.

**Option 1: Automatic Setup**
Run the provided setup script:
```bash
./db-management/setup_env.sh
source .venv/bin/activate
```

**Option 2: Manual Setup**
```bash
# Create virtual environment named .venv
python3 -m venv .venv

# Activate it (MacOS/Linux)
source .venv/bin/activate

# Install dependencies into the virtual environment
pip install -r db-management/requirements.txt
```

Note: You need to run `source .venv/bin/activate` in every new terminal session before running the scripts.


## Configuration
### `config/users.txt`
- Format: `username:password` (one per line)
- Comments: lines starting with `#` are ignored
- Passwords must pass validation (>=8 chars, contains letters and digits)

Example:
```
developer1:MySecurePass123!
developer2:AnotherPass456@
# qa user
qa_user:TestPassword789#
```

### Template database files
One template per line. Databases will be created as `<username>_<template>`.
Files:
- `mysql_databases.txt`
- `postgresql_databases.txt`
- `clickhouse_databases.txt`
- `mongodb_databases.txt`

Example (`mysql_databases.txt`):
```
tools
web
analytics
```

### `config/connections.yaml`
Provide admin connection details for each DB. Only fill the sections you plan to use.
```
mysql:
  host: localhost
  port: 3306
  admin_username: root
  admin_password: ""
  ssl: false
postgresql:
  host: localhost
  port: 5432
  admin_username: postgres
  admin_password: ""
  sslmode: disable
clickhouse:
  host: localhost
  port: 9000
  admin_username: default
  admin_password: ""
mongodb:
  host: localhost
  port: 27017
  admin_username: admin
  admin_password: ""
  auth_source: admin
```

## Running
Use `--dry-run` to preview changes without executing. Remove it to apply.
```
python db-management/scripts/mysql_sync.py --config db-management/config --dry-run
python db-management/scripts/postgresql_sync.py --config db-management/config --dry-run
python db-management/scripts/clickhouse_sync.py --config db-management/config --dry-run
python db-management/scripts/mongodb_sync.py --config db-management/config --dry-run
```

## What Sync Does
For each DB script:
- Reads desired users and passwords from `users.txt`.
- Reads templates from the corresponding `*_databases.txt`.
- Discovers managed users by scanning existing databases named `<user>_<template>`.
- Computes:
  - Users to add (in file, not managed yet)
  - Users to remove (managed, not in file)
  - Users to update (managed, password changed in file)
- Executes:
  - Create user with specified password
  - Create `<user>_<template>` databases and grant privileges
  - Update existing user passwords
  - Drop `<user>_<template>` databases and user upon removal

Notes per DB:
- MySQL: grants `ALL PRIVILEGES` on `<db>.*` to the user and flushes privileges.
- PostgreSQL: databases are created with the user as owner; additionally grants `ALL PRIVILEGES ON DATABASE`.
- ClickHouse: grants `ALL ON <db>.*`; user identified using plaintext password auth method.
- MongoDB: assigns `readWrite` role per user database.

## Security
- Do not log passwords; scripts avoid printing secrets.
- Limit access to `config/users.txt` (e.g., `chmod 600`).
- Strong password validation (basic) is enforced before operations.
- Use least privilege for created users; only per-database privileges are granted.

## Error Handling
- Continues with other users if one operation fails.
- Skips invalid `users.txt` lines; comments and empty lines ignored.
- Validates passwords before DB operations; skips users with invalid passwords.

## Dry Run Behavior
- When `--dry-run` is set, scripts avoid connecting and performing DB mutations.
- Driver modules are imported lazily to keep dry-run lightweight.

## Testing
- Edit `config/users.txt` to add/update/remove users and run with `--dry-run` first.
- Verify that computed operations match expectations, then run without `--dry-run`.
- Edge cases: empty files, duplicate names, special characters in passwords.

## Examples
Add a user and sync:
```
echo "new_developer:SecurePass123!" >> db-management/config/users.txt
python db-management/scripts/mysql_sync.py --config db-management/config
```

Update a user password:
```
sed -i '' 's/developer1:MySecurePass123!/developer1:NewStrongPass456%/' db-management/config/users.txt
python db-management/scripts/postgresql_sync.py --config db-management/config
```

Remove a user:
```
sed -i '' '/old_developer:/d' db-management/config/users.txt
python db-management/scripts/clickhouse_sync.py --config db-management/config
```

## Internals (Code Pointers)
- Common utilities: `scripts/utils/common.py`
  - Password validation: `validate_password` enforces minimal policy.
  - Managed user detection via database name suffix.
- MySQL handler: `scripts/utils/mysql_handler.py`
- PostgreSQL handler: `scripts/utils/postgresql_handler.py`
- ClickHouse handler: `scripts/utils/clickhouse_handler.py`
- MongoDB handler: `scripts/utils/mongodb_handler.py`

## Limitations
- Password validation is basic; enhance per-DB policies if required.
- MongoDB roles are limited to `readWrite`; customize as needed.
- ClickHouse uses plaintext password identity for simplicity; adapt to your auth policy.

## FAQ
- Permissions errors: ensure admin credentials in `connections.yaml` have rights to create users and databases.
- SSL/TLS: basic toggles are provided; extend connection options in handlers for advanced setups.
- Idempotency: scripts are safe to re-run; they reconcile against current state and `users.txt`.
