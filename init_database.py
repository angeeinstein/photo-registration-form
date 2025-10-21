#!/usr/bin/env python3
"""
Database initialization script
Ensures the database is created before the application starts
"""
import os
import sys

# Get the directory where this script is located
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))

# Change to the script directory (should be the app root)
os.chdir(SCRIPT_DIR)
sys.path.insert(0, SCRIPT_DIR)

try:
    from app import app, init_db
    
    print("=" * 60)
    print("DATABASE INITIALIZATION")
    print("=" * 60)
    print(f"Working directory: {os.getcwd()}")
    
    with app.app_context():
        try:
            init_db()
            print("✅ Database initialized successfully!")
            
            # Verify database exists
            db_path = 'registrations.db'
            if os.path.exists(db_path):
                size = os.path.getsize(db_path)
                print(f"✅ Database file exists: {db_path}")
                print(f"   Size: {size} bytes")
            else:
                print(f"⚠️  Warning: Database file not found at {db_path}")
                print("   It will be created on first request")
            
            print("=" * 60)
            sys.exit(0)
            
        except Exception as e:
            print(f"❌ Error initializing database: {str(e)}")
            import traceback
            traceback.print_exc()
            print("=" * 60)
            # Exit with 0 to allow service to continue - database will be created on first request
            print("ℹ️  Database will be created on first application request")
            sys.exit(0)

except ImportError as e:
    print(f"❌ Failed to import app: {str(e)}")
    import traceback
    traceback.print_exc()
    # Exit with 0 to allow service to continue
    print("ℹ️  Service will attempt to initialize database on startup")
    sys.exit(0)
