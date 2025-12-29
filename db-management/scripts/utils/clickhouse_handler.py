import importlib

class ClickHouseHandler:
    def __init__(self, cfg: dict, dry_run: bool = False):
        self.cfg = cfg
        self.dry = dry_run

    def _client(self):
        Client = importlib.import_module("clickhouse_driver").Client
        return Client(
            host=self.cfg.get("host", "localhost"),
            port=int(self.cfg.get("port", 9000)),
            user=self.cfg.get("admin_username", ""),
            password=self.cfg.get("admin_password", ""),
        )

    def get_existing_users(self) -> set:
        if self.dry:
            return set()
        c = self._client()
        rows = c.execute("SELECT name FROM system.users")
        return {r[0] for r in rows}

    def get_existing_databases(self) -> list:
        if self.dry:
            return []
        c = self._client()
        rows = c.execute("SELECT name FROM system.databases")
        return [r[0] for r in rows]

    def create_user(self, username: str, password: str):
        if self.dry:
            print(f"[CH][DRY] Create user '{username}'")
            return
        print(f"[CH] Creating user '{username}'")
        c = self._client()
        escaped_pwd = self._escape(password)
        cluster = self.cfg.get("cluster")
        if cluster:
             c.execute(f"CREATE USER IF NOT EXISTS {self._ident(username)} ON CLUSTER {self._ident(cluster)} IDENTIFIED WITH plaintext_password BY '{escaped_pwd}'")
        else:
             c.execute(f"CREATE USER IF NOT EXISTS {self._ident(username)} IDENTIFIED WITH plaintext_password BY '{escaped_pwd}'")

    def create_database(self, name: str):
        if self.dry:
            print(f"[CH][DRY] Create database '{name}'")
            return
        print(f"[CH] Creating database '{name}'")
        c = self._client()
        cluster = self.cfg.get("cluster")
        if cluster:
            c.execute(f"CREATE DATABASE IF NOT EXISTS {self._ident(name)} ON CLUSTER {self._ident(cluster)}")
        else:
            c.execute(f"CREATE DATABASE IF NOT EXISTS {self._ident(name)}")

    def grant_full_privileges(self, username: str, db_name: str):
        if self.dry:
            print(f"[CH][DRY] Grant privileges on '{db_name}' to '{username}'")
            return
        print(f"[CH] Granting privileges on '{db_name}' to '{username}'")
        c = self._client()
        cluster = self.cfg.get("cluster")
        if cluster:
            c.execute(f"GRANT ON CLUSTER {self._ident(cluster)} ALL ON {self._ident(db_name)}.* TO {self._ident(username)}")
        else:
            c.execute(f"GRANT ALL ON {self._ident(db_name)}.* TO {self._ident(username)}")

    def drop_user(self, username: str):
        if self.dry:
            print(f"[CH][DRY] Drop user '{username}'")
            return
        print(f"[CH] Dropping user '{username}'")
        c = self._client()
        cluster = self.cfg.get("cluster")
        if cluster:
            c.execute(f"DROP USER IF EXISTS {self._ident(username)} ON CLUSTER {self._ident(cluster)}")
        else:
            c.execute(f"DROP USER IF EXISTS {self._ident(username)}")

    def drop_database(self, name: str):
        if self.dry:
            print(f"[CH][DRY] Drop database '{name}'")
            return
        print(f"[CH] Dropping database '{name}'")
        c = self._client()
        cluster = self.cfg.get("cluster")
        if cluster:
            c.execute(f"DROP DATABASE IF EXISTS {self._ident(name)} ON CLUSTER {self._ident(cluster)}")
        else:
            c.execute(f"DROP DATABASE IF EXISTS {self._ident(name)}")

    def update_user_password(self, username: str, password: str):
        if self.dry:
            print(f"[CH][DRY] Update password for '{username}'")
            return
        print(f"[CH] Updating password for '{username}'")
        c = self._client()
        escaped_pwd = self._escape(password)
        cluster = self.cfg.get("cluster")
        if cluster:
            c.execute(f"ALTER USER {self._ident(username)} ON CLUSTER {self._ident(cluster)} IDENTIFIED WITH plaintext_password BY '{escaped_pwd}'")
        else:
            c.execute(f"ALTER USER {self._ident(username)} IDENTIFIED WITH plaintext_password BY '{escaped_pwd}'")

    def _ident(self, s: str) -> str:
        return "`" + s.replace("`", "``") + "`"

    def _escape(self, s: str) -> str:
        # ClickHouse string escaping: \ -> \\ and ' -> \'
        return s.replace("\\", "\\\\").replace("'", "\\'")
