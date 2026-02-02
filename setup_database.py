"""
Database setup and verification script
Tests connection and creates database if needed
"""
import sys
from sqlalchemy import create_engine, text
from sqlalchemy.exc import OperationalError, ProgrammingError
import os
from dotenv import load_dotenv

load_dotenv()

# Get database URL from environment
DATABASE_URL = os.getenv("DATABASE_URL", "postgresql://postgres:postgres@localhost:5432/fleetdb")

print("=" * 60)
print("PostgreSQL Database Setup")
print("=" * 60)
# Hide password in output
safe_url = DATABASE_URL
if "@" in DATABASE_URL:
    try:
        prefix, suffix = DATABASE_URL.split("@")
        if "//" in prefix and ":" in prefix.split("//")[1]:
            schema_user, password = prefix.split(":")
            # Reconstruct safely
            safe_url = f"{schema_user}:***@{suffix}"
    except:
        pass # If parsing fails, just print what we have carefully or generic
        safe_url = "postgresql://... (hidden)"

print(f"\nDatabase URL: {safe_url}")

# Parse database URL to get connection info
if DATABASE_URL.startswith("postgresql://"):
    # Extract components
    try:
        parts = DATABASE_URL.replace("postgresql://", "").split("/")
        connection_part = parts[0] # user:pass@host:port
        db_name = parts[1] if len(parts) > 1 else "fleetdb"
        # Handle potential query params
        if "?" in db_name:
            db_name = db_name.split("?")[0]
            
        # Connect to postgres database (default) to check if our DB exists
        # We need to strip the db name from the original URL and append 'postgres'
        # simpler way: parse the original URL
        from sqlalchemy.engine.url import make_url
        url_obj = make_url(DATABASE_URL)
        
        # Create URL for 'postgres' db
        postgres_url = url_obj.set(database="postgres")
        
        print(f"\nTarget database: {db_name}")
        print("\nStep 1: Testing connection to PostgreSQL server...")
        
        # Connect to default postgres database
        engine = create_engine(postgres_url)
        with engine.connect() as conn:
            print("SUCCESS: Successfully connected to PostgreSQL server")
            
            # Check if our database exists
            print(f"\nStep 2: Checking if database '{db_name}' exists...")
            result = conn.execute(text(
                f"SELECT 1 FROM pg_database WHERE datname = '{db_name}'"
            ))
            exists = result.scalar()
            
            if exists:
                print(f"SUCCESS: Database '{db_name}' already exists")
            else:
                print(f"INFO: Database '{db_name}' does not exist")
                print(f"\nStep 3: Creating database '{db_name}'...")
                
                # Need to commit the current transaction and use autocommit
                conn.commit()
                conn.execution_options(isolation_level="AUTOCOMMIT").execute(
                    text(f"CREATE DATABASE {db_name}")
                )
                print(f"SUCCESS: Database '{db_name}' created successfully")
        
        # Now test connection to the actual database
        print(f"\nStep 4: Testing connection to database '{db_name}'...")
        target_engine = create_engine(DATABASE_URL)
        with target_engine.connect() as conn:
            print(f"SUCCESS: Successfully connected to database '{db_name}'")
            
        print("\n" + "=" * 60)
        print("DATABASE SETUP COMPLETE!")
        print("=" * 60)
        print("\nNext steps:")
        print("  1. Run: python create_tables.py")
        print("  2. Run: python create_admin.py")
        print("  3. Start server: python -m uvicorn main:app --reload")
        
        sys.exit(0)
        
    except OperationalError as e:
        print(f"\nFAILURE: Connection failed: {e}")
        print("\nPossible issues:")
        print("  1. PostgreSQL service is not running")
        print("  2. Wrong username/password in DATABASE_URL")
        print("  3. PostgreSQL is not listening on localhost:5432")
        print("\nCheck your .env file and PostgreSQL configuration")
        sys.exit(1)
        
    except Exception as e:
        print(f"\nFAILURE: Unexpected error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
        
else:
    print("FAILURE: DATABASE_URL does not appear to be a PostgreSQL URL")
    print(f"  Got: {DATABASE_URL}")
    sys.exit(1)
