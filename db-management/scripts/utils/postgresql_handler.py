import importlib

class PostgreSQLHandler:
    def __init__(self, cfg: dict, dry_run: bool = False):
        self.cfg = cfg
        self.dry = dry_run

    def _conn(self):
        psycopg2 = importlib.import_module("psycopg2")
        conn = psycopg2.connect(
            host=self.cfg.get("host", "localhost"),
            port=int(self.cfg.get("port", 5432)),
            user=self.cfg.get("admin_username", ""),
            password=self.cfg.get("admin_password", ""),
            dbname="postgres",
        )
        conn.autocommit = True
        return conn

    def get_existing_users(self) -> set:
        if self.dry:
            return set()
        with self._conn() as conn:
            with conn.cursor() as cur:
                cur.execute("SELECT rolname FROM pg_roles")
                return {r[0] for r in cur.fetchall()}

    def get_existing_databases(self) -> list:
        if self.dry:
            return []
        with self._conn() as conn:
            with conn.cursor() as cur:
                cur.execute("SELECT datname FROM pg_database WHERE datistemplate = false")
                return [r[0] for r in cur.fetchall()]

    def create_user(self, username: str, password: str):
        if self.dry:
            print(f"[PG][DRY] Create role '{username}'")
            return
        print(f"[PG] Creating role '{username}'")
        psycopg2 = importlib.import_module("psycopg2")
        with self._conn() as conn:
            with conn.cursor() as cur:
                try:
                    cur.execute(f"CREATE ROLE {self._ident(username)} LOGIN PASSWORD %s", (password,))
                except psycopg2.errors.DuplicateObject:
                    print(f"Role '{username}' already exists, skipping creation.")
                    pass

    def create_database(self, name: str, owner: str):
        if self.dry:
            print(f"[PG][DRY] Create database '{name}' owner '{owner}'")
            return
        print(f"[PG] Creating database '{name}' owner '{owner}'")
        psycopg2 = importlib.import_module("psycopg2")
        
        # Check if database exists first to avoid error spam
        # We need a dedicated connection for checking to ensure clean state
        conn = self._conn()
        try:
            with conn.cursor() as cur:
                cur.execute("SELECT 1 FROM pg_database WHERE datname = %s", (name,))
                if cur.fetchone():
                    return
        finally:
            conn.close()

        # Connect again for creation.
        # CRITICAL: PostgreSQL CREATE DATABASE cannot run inside a transaction block.
        # psycopg2 connection with autocommit=True SHOULD handle this, but using 'with self._conn() as conn'
        # might imply context manager behavior that affects transaction state.
        # Let's use a raw connection object without 'with' for the creation to be explicit.
        conn = self._conn()
        conn.autocommit = True
        try:
            with conn.cursor() as cur:
                try:
                    cur.execute(f"CREATE DATABASE {self._ident(name)} OWNER {self._ident(owner)}")
                except psycopg2.errors.DuplicateDatabase:
                     pass
        finally:
            conn.close()
                     
    def grant_full_privileges(self, username: str, db_name: str):
        if self.dry:
            print(f"[PG][DRY] Grant privileges on '{db_name}' to '{username}'")
            return
        print(f"[PG] Granting privileges on '{db_name}' to '{username}'")
        # GRANT ALL ON DATABASE only grants connect/create/temp. 
        # It does NOT grant rights to tables inside schemas.
        # But per task, we grant "full privileges" on database level.
        # For a user to actually do things, they are usually the OWNER (which we set in create_database).
        # Owners implicitly have full control.
        # So GRANT ALL PRIVILEGES ON DATABASE is actually somewhat redundant if they are owner,
        # but good for ensuring CONNECT rights etc.
        
        with self._conn() as conn:
            with conn.cursor() as cur:
                cur.execute(f"GRANT ALL PRIVILEGES ON DATABASE {self._ident(db_name)} TO {self._ident(username)}")
                
                # NOTE: In Postgres, just granting on DATABASE isn't enough for tables created by others.
                # But since we create the DB with this user as OWNER, they will have full rights by default.
                # So this is sufficient.

    def drop_user(self, username: str):
        if self.dry:
            print(f"[PG][DRY] Drop role '{username}'")
            return
        print(f"[PG] Dropping role '{username}'")
        with self._conn() as conn:
            with conn.cursor() as cur:
                cur.execute(f"DROP ROLE IF EXISTS {self._ident(username)}")

    def drop_database(self, name: str):
        if self.dry:
            print(f"[PG][DRY] Drop database '{name}'")
            return
        print(f"[PG] Dropping database '{name}'")
        conn = self._conn()
        conn.autocommit = True
        try:
            with conn.cursor() as cur:
                # Terminate connections first or DROP will fail
                cur.execute(f"""
                    SELECT pg_terminate_backend(pg_stat_activity.pid)
                    FROM pg_stat_activity
                    WHERE pg_stat_activity.datname = %s
                    AND pid <> pg_backend_pid()
                """, (name,))
                cur.execute(f"DROP DATABASE IF EXISTS {self._ident(name)}")
        finally:
            conn.close()

    def update_user_password(self, username: str, password: str):
        if self.dry:
            print(f"[PG][DRY] Update password for '{username}'")
            return
        print(f"[PG] Updating password for '{username}'")
        with self._conn() as conn:
            with conn.cursor() as cur:
                cur.execute(f"ALTER ROLE {self._ident(username)} WITH PASSWORD %s", (password,))

    def _ident(self, s: str) -> str:
        return '"' + s.replace('"', '""') + '"'
