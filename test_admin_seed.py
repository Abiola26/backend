"""
Test script to verify admin seeding logic
"""
import os
import sys

# Set environment to use local SQLite for testing
os.environ["DATABASE_URL"] = "sqlite:///./test_seed.db"

# Remove existing test database if it exists
if os.path.exists("test_seed.db"):
    os.remove("test_seed.db")
    print("Removed existing test database")

# Import after setting environment
from app.database import SessionLocal, Base, engine
from app.models import User

# Create tables
print("Creating tables...")
Base.metadata.create_all(bind=engine)

# Check if any users exist
db = SessionLocal()
user_count = db.query(User).count()
print(f"User count before seeding: {user_count}")

if user_count == 0:
    print("No users found. Testing seeding logic...")
    from app.crud import create_user
    
    admin_user = create_user(db, username="admin", password="admin123", role="admin")
    print(f"[OK] Admin user created: {admin_user.username}")
    print(f"  Role: {admin_user.role}")
    print(f"  Account ID: {admin_user.account_id}")
    
    # Verify authentication works
    from app.auth import authenticate_user
    auth_result = authenticate_user(db, "admin", "admin123")
    
    if auth_result:
        print("[OK] Authentication test PASSED")
    else:
        print("[FAIL] Authentication test FAILED")
        sys.exit(1)
else:
    print(f"Database already has {user_count} users")

db.close()

# Cleanup
if os.path.exists("test_seed.db"):
    os.remove("test_seed.db")
    print("\n[OK] Test completed successfully. Cleanup done.")
