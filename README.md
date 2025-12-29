# Database User Management System

This project provides a robust, automated solution for managing users and databases across multiple database systems: **MySQL**, **PostgreSQL**, **MongoDB**, and **ClickHouse**.

It uses Docker Compose to spin up the database infrastructure and Python scripts to synchronize users, databases, and privileges based on configuration files.

## Features

*   **Multi-Database Support**: Unified management for MySQL (8.0), PostgreSQL (15), MongoDB (6.0), and ClickHouse (23.8).
*   **Idempotent Synchronization**: Scripts can be run multiple times safely. They create missing resources, update existing ones, and remove obsolete ones (cleanup).
*   **Configuration as Code**: Users and database templates are defined in simple text/YAML files.
*   **Secure & Robust**:
    *   Handles authentication nuances (e.g., MySQL `caching_sha2_password`, ClickHouse manual escaping).
    *   Supports ClickHouse clusters (`ON CLUSTER` operations).
    *   Handles MongoDB lazy database creation.
    *   Safe transaction management for PostgreSQL.

## Prerequisites

*   Docker & Docker Compose
*   Python 3.10+

## Project Structure

```
.
├── data/                   # Persistent data for databases (ignored by git)
├── db-management/
│   ├── config/             # Configuration files
│   │   ├── connections.yaml       # Admin credentials and connection details
│   │   ├── users.txt              # List of users to manage
│   │   ├── mysql_databases.txt    # Database templates for MySQL
│   │   ├── postgresql_databases.txt # Database templates for PostgreSQL
│   │   ├── mongodb_databases.txt    # Database templates for MongoDB
│   │   └── clickhouse_databases.txt # Database templates for ClickHouse
│   └── scripts/            # Synchronization scripts
│       ├── mysql_sync.py
│       ├── postgresql_sync.py
│       ├── mongodb_sync.py
│       ├── clickhouse_sync.py
│       └── utils/          # Helper classes for each DB
├── init/                   # Initialization scripts/configs for Docker containers
│   └── clickhouse/
│       └── config.xml      # ClickHouse cluster configuration
├── docker-compose.yaml     # Service definitions
└── README.md
```

## Setup & Installation

1.  **Start the Database Infrastructure**

    ```bash
    docker-compose up -d
    ```
    This will start MySQL, PostgreSQL, MongoDB, ClickHouse (with Zookeeper), and Adminer.

2.  **Set up Python Environment**

    ```bash
    python3 -m venv .venv
    source .venv/bin/activate
    pip install pymysql cryptography psycopg2-binary pymongo clickhouse-driver pyyaml
    ```

## Configuration

### 1. Define Users
Edit `db-management/config/users.txt` to add or remove users. Format: `username:password`
```text
developer1:pass123
qauser:securePass!
```

### 2. Define Database Templates
Edit `db-management/config/*_databases.txt`. Each line represents a suffix.
If `users.txt` has `dev1` and `mysql_databases.txt` has `web`, the script will create a database named `dev1_web`.

### 3. Connection Settings
`db-management/config/connections.yaml` contains admin credentials. These match the `docker-compose.yaml` defaults.
*Note: ClickHouse is configured as a single-node cluster named `single_node_cluster`. Make sure the `cluster` key in `connections.yaml` matches this name.*

```yaml
clickhouse:
  host: localhost
  port: 9000
  admin_username: clickhouse_user
  admin_password: "clickhouse_password"
  cluster: "single_node_cluster"  # Important for ON CLUSTER operations
```

## Usage

Run the synchronization scripts to apply changes. You can use `--dry-run` to preview changes without executing them.

### MySQL
```bash
python db-management/scripts/mysql_sync.py --config db-management/config
```

### PostgreSQL
```bash
python db-management/scripts/postgresql_sync.py --config db-management/config
```

### MongoDB
```bash
python db-management/scripts/mongodb_sync.py --config db-management/config
```

### ClickHouse
```bash
python db-management/scripts/clickhouse_sync.py --config db-management/config
```

## Infrastructure Details

| Service | Host (Local) | Port | Admin User | Password | Notes |
| :--- | :--- | :--- | :--- | :--- | :--- |
| **MySQL** | localhost | 3306 | `root` | `mysql_root_password` | Ver 8.0 |
| **PostgreSQL** | localhost | 5432 | `postgres` | `postgres_password` | Ver 15 |
| **MongoDB** | localhost | 27017 | `mongo_admin` | `mongo_password` | Ver 6.0 |
| **ClickHouse** | localhost | 9000 (TCP)<br>8123 (HTTP) | `clickhouse_user` | `clickhouse_password` | Ver 23.8, Clustered |
| **Zookeeper** | localhost | 2181 | - | - | For ClickHouse |
| **Adminer** | localhost | 8080 | - | - | Web UI |

## Troubleshooting

*   **ClickHouse**: If you see authentication errors, ensure `connections.yaml` uses `clickhouse_user`, not `default`. The scripts handle `ON CLUSTER` commands automatically.
*   **MongoDB**: Databases are "lazy". The script creates a dummy `init_marker` collection to force the database to persist.
*   **PostgreSQL**: `DROP DATABASE` forces termination of active connections to ensure success.
*   **Permissions**: Scripts grant `ALL PRIVILEGES` on the user's specific databases (e.g., `user_dbname.*`), ensuring isolation.
