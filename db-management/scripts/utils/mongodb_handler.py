import importlib

class MongoDBHandler:
    def __init__(self, cfg: dict, dry_run: bool = False):
        self.cfg = cfg
        self.dry = dry_run

    def _client(self):
        MongoClient = importlib.import_module("pymongo").MongoClient
        host = self.cfg.get("host", "localhost")
        port = int(self.cfg.get("port", 27017))
        user = self.cfg.get("admin_username", "")
        pwd = self.cfg.get("admin_password", "")
        auth_db = self.cfg.get("auth_source", "admin")
        if user:
            uri = f"mongodb://{user}:{pwd}@{host}:{port}/?authSource={auth_db}"
        else:
            uri = f"mongodb://{host}:{port}/"
        return MongoClient(uri)

    def get_existing_users(self) -> set:
        if self.dry:
            return set()
        c = self._client()
        admin = c[self.cfg.get("auth_source", "admin")]
        info = admin.command("usersInfo")
        users = {u["user"] for u in info.get("users", [])}
        return users

    def get_existing_databases(self) -> list:
        if self.dry:
            return []
        c = self._client()
        return c.list_database_names()

    def create_user(self, username: str, password: str):
        if self.dry:
            print(f"[Mongo][DRY] Create user '{username}'")
            return
        print(f"[Mongo] Creating user '{username}'")
        c = self._client()
        admin = c[self.cfg.get("auth_source", "admin")]
        try:
            admin.command("createUser", username, pwd=password, roles=[])
        except Exception as e:
            # Check if error is "User already exists" (code 51003)
            if hasattr(e, 'code') and e.code == 51003:
                 print(f"User '{username}' already exists, skipping creation.")
            else:
                 # Check string message for older mongo versions or different drivers
                 if "already exists" in str(e):
                      print(f"User '{username}' already exists, skipping creation.")
                 else:
                      raise e

    def create_database(self, name: str):
        if self.dry:
            print(f"[Mongo][DRY] Create database '{name}'")
            return
        print(f"[Mongo] Creating database '{name}'")
        c = self._client()
        db = c[name]
        # MongoDB creates databases lazily. We must create a collection to make it persist.
        if "init_marker" not in db.list_collection_names():
            db.create_collection("init_marker")

    def grant_full_privileges(self, username: str, db_name: str):
        if self.dry:
            print(f"[Mongo][DRY] Grant privileges on '{db_name}' to '{username}'")
            return
        print(f"[Mongo] Granting privileges on '{db_name}' to '{username}'")
        c = self._client()
        admin = c[self.cfg.get("auth_source", "admin")]
        info = admin.command("usersInfo", username)
        roles = info.get("users", [{}])[0].get("roles", [])
        if not any(r.get("db") == db_name and r.get("role") == "readWrite" for r in roles):
            roles.append({"role": "readWrite", "db": db_name})
            admin.command("updateUser", username, roles=roles)

    def drop_user(self, username: str):
        if self.dry:
            print(f"[Mongo][DRY] Drop user '{username}'")
            return
        print(f"[Mongo] Dropping user '{username}'")
        c = self._client()
        admin = c[self.cfg.get("auth_source", "admin")]
        admin.command("dropUser", username)

    def drop_database(self, name: str):
        if self.dry:
            print(f"[Mongo][DRY] Drop database '{name}'")
            return
        print(f"[Mongo] Dropping database '{name}'")
        c = self._client()
        c.drop_database(name)

    def update_user_password(self, username: str, password: str):
        if self.dry:
            print(f"[Mongo][DRY] Update password for '{username}'")
            return
        print(f"[Mongo] Updating password for '{username}'")
        c = self._client()
        admin = c[self.cfg.get("auth_source", "admin")]
        admin.command("updateUser", username, pwd=password)
