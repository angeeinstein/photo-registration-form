#!/usr/bin/env python3
"""Test database creation and permissions"""
import os
import sys

# Check if database file exists
db_path = 'registrations.db'

print("=" * 60)
print("Database Permission Test")
print("=" * 60)

if os.path.exists(db_path):
    print(f"✓ Database file exists: {db_path}")
    
    # Check if writable
    if os.access(db_path, os.W_OK):
        print("✓ Database is writable")
    else:
        print("✗ WARNING: Database is READ-ONLY")
        print("\nFix: Run the following command:")
        print(f"  attrib -r {db_path}")
        sys.exit(1)
    
    # Check file size
    size = os.path.getsize(db_path)
    print(f"✓ Database size: {size:,} bytes")
else:
    print(f"! Database file doesn't exist yet: {db_path}")
    print("  It will be created when you first run the application")

# Try to import app and initialize database
print("\n" + "=" * 60)
print("Testing database initialization...")
print("=" * 60)

try:
    from app import init_db
    print("✓ Successfully imported app module")
    
    print("\nInitializing database...")
    init_db()
    print("✓ Database initialized successfully!")
    
    # Verify database was created
    if os.path.exists(db_path):
        print(f"✓ Database file created: {db_path}")
        
        if os.access(db_path, os.W_OK):
            print("✓ Database is writable")
        else:
            print("✗ ERROR: Database was created but is READ-ONLY")
            sys.exit(1)
    
except Exception as e:
    print(f"✗ ERROR: {str(e)}")
    import traceback
    traceback.print_exc()
    sys.exit(1)

print("\n" + "=" * 60)
print("✓ All tests passed!")
print("=" * 60)
