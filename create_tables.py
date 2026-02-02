"""
Script to create database tables
Run this to initialize the database schema
"""
from app.database import engine
from app.models import Base

print("Creating database tables...")
try:
    Base.metadata.create_all(bind=engine)
    print("SUCCESS: Database tables created successfully")
except Exception as e:
    print(f"FAILURE: Error creating tables: {str(e)}")

