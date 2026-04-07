
from app.database import SessionLocal
from app.models import User, FleetRecord, AuditLog

def check_database_data():
    db = SessionLocal()
    try:
        # Check Users
        user_count = db.query(User).count()
        print(f"Total users: {user_count}")
        if user_count > 0:
            for user in db.query(User).all():
                print(f"  - User: {user.username} ({user.role})")
        
        # Check Fleet Records
        fleet_count = db.query(FleetRecord).count()
        print(f"Total fleet records: {fleet_count}")
        
        # Check Audit Logs
        log_count = db.query(AuditLog).count()
        print(f"Total audit logs: {log_count}")
        if log_count > 0:
            for log in db.query(AuditLog).order_by(AuditLog.timestamp.desc()).limit(10).all():
                print(f"  - [{log.timestamp}] User: {log.username} | Action: {log.action} | Details: {log.details}")
        
    except Exception as e:
        print(f"Error connecting to database: {e}")
        print("\nPossible reasons:")
        print("1. Database server (PostgreSQL) is not running.")
        print("2. Database 'fleetdb' does not exist.")
        print("3. Tables have not been created yet (try running create_tables.py).")
    finally:
        db.close()

if __name__ == "__main__":
    check_database_data()
