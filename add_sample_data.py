"""
Add sample fleet data for testing
"""
import sys
from datetime import date, timedelta
from app.database import SessionLocal
from app.models import FleetRecord

def add_sample_data():
    db = SessionLocal()
    
    try:
        # Check if we already have data
        existing = db.query(FleetRecord).count()
        if existing > 0:
            print(f"✓ Database already has {existing} records. Skipping sample data insertion.")
            return
        
        # Sample data for the last 30 days
        fleets = ["Fleet A", "Fleet B", "Fleet C", "Fleet D"]
        base_amounts = [15000, 22000, 18500, 12000]
        
        records = []
        today = date.today()
        
        for days_ago in range(30):
            current_date = today - timedelta(days=days_ago)
            
            for i, fleet in enumerate(fleets):
                # Vary amounts slightly
                import random
                amount = base_amounts[i] * (0.8 + random.random() * 0.4)  # ±20% variation
                
                record = FleetRecord(
                    date=current_date,
                    fleet=fleet,
                    amount=round(amount, 2)
                )
                records.append(record)
        
        # Add all records
        db.add_all(records)
        db.commit()
        
        print(f"✓ Successfully added {len(records)} sample fleet records")
        print(f"  - Date range: {records[-1].date} to {records[0].date}")
        print(f"  - Fleets: {', '.join(fleets)}")
        
    except Exception as e:
        print(f"✗ Error adding sample data: {str(e)}")
        db.rollback()
    finally:
        db.close()

if __name__ == "__main__":
    add_sample_data()
