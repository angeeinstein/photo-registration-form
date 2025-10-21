#!/usr/bin/env python3
"""
Database initialization script
Ensures the database is created before the application starts
"""
import os
import sys

# Ensure we're in the correct directory
os.chdir('/opt/photo-registration-form')
sys.path.insert(0, '/opt/photo-registration-form')

from app import app, init_db

print("=" * 60)
print("DATABASE INITIALIZATION")
print("=" * 60)

with app.app_context():
    try:
        init_db()
        print("✅ Database initialized successfully!")
        
        # Verify database exists
        db_path = 'instance/photo_registration.db'
        if os.path.exists(db_path):
            size = os.path.getsize(db_path)
            print(f"✅ Database file exists: {db_path}")
            print(f"   Size: {size} bytes")
        else:
            print(f"⚠️  Warning: Database file not found at {db_path}")
            print("   It may be created on first request")
        
        print("=" * 60)
        sys.exit(0)
        
    except Exception as e:
        print(f"❌ Error initializing database: {str(e)}")
        import traceback
        traceback.print_exc()
        print("=" * 60)
        sys.exit(1)
