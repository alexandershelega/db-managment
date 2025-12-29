from pathlib import Path

class MySQLHandler:
    def __init__(self, cfg: dict, dry_run: bool = False):
        self.cfg = cfg
        self.dry = dry_run

    def _conn(self):
        import pymysql
        return pymysql.connect(
            host=self.cfg.get("host", "localhost"),
            port=int(self.cfg.get("port", 3306)),
            user=self.cfg.get("admin_username", ""),
            password=self.cfg.get("admin_password", ""),
            ssl=self.cfg.get("ssl", False) or None,
            autocommit=True,
        )

    def get_existing_users(self) -> set:
        if self.dry:
            return set()
        with self._conn() as conn:
            with conn.cursor() as cur:
                cur.execute("SELECT User FROM mysql.user")
                return {row[0] for row in cur.fetchall()}

    def get_existing_databases(self) -> list:
        if self.dry:
            return []
        with self._conn() as conn:
            with conn.cursor() as cur:
                cur.execute("SHOW DATABASES")
                return [row[0] for row in cur.fetchall()]

    def create_user(self, username: str, password: str):
        if self.dry:
            print(f"[MySQL][DRY] Create user '{username}'")
            return
        print(f"[MySQL] Creating user '{username}'")
        with self._conn() as conn:
            with conn.cursor() as cur:
                cur.execute(f"CREATE USER IF NOT EXISTS `{username}`@'%%' IDENTIFIED BY %s", (password,))
                cur.execute("FLUSH PRIVILEGES")

    def create_database(self, name: str):
        if self.dry:
            print(f"[MySQL][DRY] Create database '{name}'")
            return
        print(f"[MySQL] Creating database '{name}'")
        with self._conn() as conn:
            with conn.cursor() as cur:
                cur.execute(f"CREATE DATABASE IF NOT EXISTS `{name}`")

    def grant_full_privileges(self, username: str, db_name: str):
        if self.dry:
            print(f"[MySQL][DRY] Grant privileges on '{db_name}' to '{username}'")
            return
        print(f"[MySQL] Granting privileges on '{db_name}' to '{username}'")
        with self._conn() as conn:
            with conn.cursor() as cur:
                # Use %% for wildcard to ensure PyMySQL handles it correctly even if no args
                # Although theoretically no args = no formatting, safe bet is %% if we suspect issues
                # But let's try strict % first with print
                sql = f"GRANT ALL PRIVILEGES ON `{db_name}`.* TO `{username}`@'%%'"
                # We pass empty tuple to force escaping check, or just rely on text
                # Let's assume we need to escape % to %% if PyMySQL thinks it's a format string
                # If we use execute(sql), PyMySQL sends as is.
                # If we use execute(sql, ()), PyMySQL formats.
                # Let's try sending as is but verify content.
                
                # REVISION: To be safe, let's use parameter substitution for user/host if possible? 
                # No, identifiers can't be parameters.
                
                # Let's revert to using %% and passing an empty tuple to force formatting, 
                # which guarantees % is sent as %
                cur.execute(f"GRANT ALL PRIVILEGES ON `{db_name}`.* TO `{username}`@'%%'", ())
                cur.execute("FLUSH PRIVILEGES")

    def drop_user(self, username: str):
        if self.dry:
            print(f"[MySQL][DRY] Drop user '{username}'")
            return
        print(f"[MySQL] Dropping user '{username}'")
        with self._conn() as conn:
            with conn.cursor() as cur:
                cur.execute(f"DROP USER IF EXISTS `{username}`@'%'")
                cur.execute("FLUSH PRIVILEGES")

    def drop_database(self, name: str):
        if self.dry:
            print(f"[MySQL][DRY] Drop database '{name}'")
            return
        print(f"[MySQL] Dropping database '{name}'")
        with self._conn() as conn:
            with conn.cursor() as cur:
                cur.execute(f"DROP DATABASE IF EXISTS `{name}`")

    def update_user_password(self, username: str, password: str):
        if self.dry:
            print(f"[MySQL][DRY] Update password for '{username}'")
            return
        print(f"[MySQL] Updating password for '{username}'")
        with self._conn() as conn:
            with conn.cursor() as cur:
                cur.execute(f"ALTER USER `{username}`@'%%' IDENTIFIED BY %s", (password,))
                cur.execute("FLUSH PRIVILEGES")
