"""
Script to create an admin user
Run this to create the initial admin account
"""
from app.database import SessionLocal
from app.crud import create_user
from app.models import User

db = SessionLocal()

username = "admin"
password = "admin123"  # Change this to a secure password in production

try:
    existing = db.query(User).filter(User.username == username).first()
    if existing:
        print(f"SUCCESS: Admin user '{username}' already exists")
    else:
        # Create admin user with admin role
        admin_user = create_user(db, username, password, role="admin")
        print(f"SUCCESS: Admin user '{username}' created successfully")
        print(f"  Username: {admin_user.username}")
        print(f"  Role: {admin_user.role}")
        print("\nWARNING: Change the default password immediately!")
except Exception as e:
    print(f"FAILURE: Error creating admin user: {str(e)}")
    db.rollback()
finally:
    db.close()

