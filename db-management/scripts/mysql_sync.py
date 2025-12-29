import sys
from pathlib import Path
sys.path.append(str(Path(__file__).parent))
sys.path.append(str(Path(__file__).parent / "utils"))
import argparse
from utils.common import read_users_file, read_template_databases, load_connections, extract_managed_users_from_dbnames
from utils.mysql_handler import MySQLHandler

def run(config_dir: str, dry_run: bool):
    users = read_users_file(str(Path(config_dir) / "users.txt"))
    templates = read_template_databases(str(Path(config_dir) / "mysql_databases.txt"))
    cfg = load_connections(config_dir, "mysql")
    handler = MySQLHandler(cfg, dry_run)
    existing_users = handler.get_existing_users()
    existing_dbs = handler.get_existing_databases()
    managed_users = extract_managed_users_from_dbnames(existing_dbs, templates)
    desired = set(users.keys())
    to_add = desired - managed_users
    to_remove = managed_users - desired
    to_update = desired & managed_users
    for username in to_add:
        try:
            handler.create_user(username, users[username])
            for t in templates:
                dbn = f"{username}_{t}"
                try:
                    handler.create_database(dbn)
                    handler.grant_full_privileges(username, dbn)
                except Exception as e:
                    print(f"Error creating database {dbn}: {e}")
        except Exception as e:
            print(f"Error creating user {username}: {e}")
    for username in to_update:
        try:
            handler.update_user_password(username, users[username])
            
            # 1. Ensure all REQUIRED databases exist
            for t in templates:
                dbn = f"{username}_{t}"
                try:
                    handler.create_database(dbn)
                    handler.grant_full_privileges(username, dbn)
                except Exception as e:
                    print(f"Error creating/granting database {dbn}: {e}")

            # 2. Remove databases that are NO LONGER required
            # Get all databases for this user
            user_dbs = [d for d in existing_dbs if d.startswith(f"{username}_")]
            # Extract the template suffix (everything after username_)
            # Be careful if template contains underscores, so we use length of username + 1
            existing_templates = {d[len(username)+1:] for d in user_dbs}
            
            # Find templates that exist but are not in the desired list
            to_drop = existing_templates - set(templates)
            
            for t in to_drop:
                dbn = f"{username}_{t}"
                try:
                    handler.drop_database(dbn)
                except Exception as e:
                    print(f"Error dropping database {dbn}: {e}")
                    
        except Exception as e:
            print(f"Error updating user {username}: {e}")
    for username in to_remove:
        for t in templates:
            dbn = f"{username}_{t}"
            try:
                handler.drop_database(dbn)
            except Exception as e:
                print(f"Error dropping database {dbn}: {e}")
        try:
            handler.drop_user(username)
        except Exception as e:
            print(f"Error dropping user {username}: {e}")

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--config", required=True)
    ap.add_argument("--dry-run", action="store_true")
    args = ap.parse_args()
    run(args.config, args.dry_run)

if __name__ == "__main__":
    main()
