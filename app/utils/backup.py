
import os
import subprocess
from datetime import datetime
from ..config import get_settings

def run_backup():
    settings = get_settings()
    db_url = settings.database_url
    
    # Parse DB URL (postgresql://user:password@host:port/dbname)
    # This is a bit brittle, a better way would be to have separate config vars
    # but for now we'll parse the URL
    try:
        # Expected format: postgresql://postgres:postgres@localhost:5432/fleetdb
        parts = db_url.replace("postgresql://", "").replace("@", ":").replace("/", ":").split(":")
        user = parts[0]
        password = parts[1]
        host = parts[2]
        port = parts[3]
        dbname = parts[4]
    except Exception as e:
        print(f"Error parsing database URL: {e}")
        return False

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    # Use absolute path for backups directory
    project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", ".."))
    backup_dir = os.path.join(project_root, "backups")
    if not os.path.exists(backup_dir):
        os.makedirs(backup_dir)
    
    backup_file = os.path.join(backup_dir, f"backup_{dbname}_{timestamp}.sql")
    
    # PostgreSQL version 18 path found on this system
    pg_dump_path = r"C:\Program Files\PostgreSQL\18\bin\pg_dump.exe"
    
    if not os.path.exists(pg_dump_path):
        # Fallback to just "pg_dump" if the hardcoded path doesn't exist elsewhere
        pg_dump_path = "pg_dump"

    env = os.environ.copy()
    env["PGPASSWORD"] = password

    command = [
        pg_dump_path,
        "-h", host,
        "-p", port,
        "-U", user,
        "-f", backup_file,
        dbname
    ]

    print(f"Starting backup of {dbname} to {backup_file}...")
    try:
        result = subprocess.run(command, env=env, check=True, capture_output=True, text=True)
        print(f"Backup completed successfully: {backup_file}")
        return True
    except subprocess.CalledProcessError as e:
        print(f"Backup failed: {e.stderr}")
        return False
    except Exception as e:
        print(f"An error occurred: {e}")
        return False

if __name__ == "__main__":
    run_backup()
