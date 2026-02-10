import logging
import os
import re
import subprocess
from datetime import datetime

from ..config import get_settings

logger = logging.getLogger("app.backup")


def run_backup():
    settings = get_settings()
    db_url = settings.database_url

    # Robust parsing of DB URL using regex
    # Format: postgresql://user:password@host:port/dbname
    pattern = r"postgresql://(?P<user>[^:]+):(?P<password>[^@]+)@(?P<host>[^:]+):(?P<port>\d+)/(?P<dbname>.+)"
    match = re.search(pattern, db_url)

    if not match:
        logger.error(
            "Failed to parse database URL. Ensure it matches 'postgresql://user:password@host:port/dbname'"
        )
        return False

    db_info = match.groupdict()
    user = db_info["user"]
    password = db_info["password"]
    host = db_info["host"]
    port = db_info["port"]
    dbname = db_info["dbname"]

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    # Use absolute path for backups directory
    project_root = os.path.abspath(
        os.path.join(os.path.dirname(__file__), "..", "..", "..")
    )
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
        "-h",
        host,
        "-p",
        port,
        "-U",
        user,
        "-f",
        backup_file,
        dbname,
    ]

    logger.info(f"Starting backup of database '{dbname}' to {backup_file}...")
    try:
        subprocess.run(command, env=env, check=True, capture_output=True, text=True)
        logger.info(f"Backup completed successfully: {backup_file}")
        return True
    except subprocess.CalledProcessError as e:
        logger.error(f"Backup process failed: {e.stderr}")
        return False
    except Exception as e:
        logger.exception(f"An unexpected error occurred during backup: {e}")
        return False


if __name__ == "__main__":
    run_backup()
