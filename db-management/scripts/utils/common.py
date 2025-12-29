from pathlib import Path
import re
import yaml

def read_users_file(path: str) -> dict:
    p = Path(path)
    result = {}
    if not p.exists():
        return result
    for raw in p.read_text(encoding="utf-8").splitlines():
        line = raw.strip()
        if not line or line.startswith("#"):
            continue
        if ":" not in line:
            continue
        username, password = line.split(":", 1)
        u = username.strip()
        pw = password.strip()
        if not u or not pw:
            continue
        if not validate_password(pw):
            continue
        result[u] = pw
    return result

def read_template_databases(path: str) -> list:
    p = Path(path)
    if not p.exists():
        return []
    items = []
    for raw in p.read_text(encoding="utf-8").splitlines():
        line = raw.strip()
        if not line or line.startswith("#"):
            continue
        items.append(line)
    return items

def load_connections(config_dir: str, key: str) -> dict:
    config_path = Path(config_dir) / "connections.yaml"
    if not config_path.exists():
        return {}
    data = yaml.safe_load(config_path.read_text(encoding="utf-8")) or {}
    return data.get(key, {}) or {}

def validate_password(password: str) -> bool:
    if len(password) < 8:
        return False
    if not re.search(r"[A-Za-z]", password):
        return False
    if not re.search(r"\d", password):
        return False
    return True

def extract_managed_users_from_dbnames(dbnames: list, templates: list) -> set:
    users = set()
    for db in dbnames:
        for t in templates:
            suffix = f"_{t}"
            if db.endswith(suffix) and len(db) > len(suffix):
                users.add(db[: -len(suffix)])
    return users
