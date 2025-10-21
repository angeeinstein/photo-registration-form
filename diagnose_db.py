"""
Database Diagnostic Tool
Run this to check if the database is properly initialized
"""
import os
import sys

# Set up the database path
db_path = 'instance/photo_registration.db'

print("=" * 60)
print("DATABASE DIAGNOSTIC TOOL")
print("=" * 60)
print()

# Check if database file exists
print("1. Checking database file...")
if os.path.exists(db_path):
    print(f"   ✅ Database file exists: {db_path}")
    
    # Check permissions
    if os.access(db_path, os.R_OK):
        print(f"   ✅ Database is readable")
    else:
        print(f"   ❌ Database is NOT readable")
    
    if os.access(db_path, os.W_OK):
        print(f"   ✅ Database is writable")
    else:
        print(f"   ❌ Database is NOT writable")
    
    # Get file size
    size = os.path.getsize(db_path)
    print(f"   📊 Database size: {size} bytes")
else:
    print(f"   ❌ Database file does NOT exist: {db_path}")
    print(f"   💡 Run 'python app.py' to initialize the database")
    sys.exit(1)

print()

# Try to connect to database
print("2. Checking database connection...")
try:
    import sqlite3
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    print("   ✅ Successfully connected to database")
    
    # List all tables
    print()
    print("3. Checking database tables...")
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
    tables = cursor.fetchall()
    
    if tables:
        print(f"   ✅ Found {len(tables)} tables:")
        for table in tables:
            table_name = table[0]
            cursor.execute(f"SELECT COUNT(*) FROM {table_name}")
            count = cursor.fetchone()[0]
            print(f"      - {table_name}: {count} records")
    else:
        print("   ❌ No tables found in database")
        print("   💡 The database may not be initialized properly")
    
    # Check specific tables
    print()
    print("4. Checking required tables...")
    required_tables = ['registration', 'email_account', 'admin_settings', 'user']
    
    existing_tables = [t[0] for t in tables]
    
    for table in required_tables:
        if table in existing_tables:
            print(f"   ✅ Table '{table}' exists")
        else:
            print(f"   ❌ Table '{table}' is MISSING")
    
    # Check for email accounts
    print()
    print("5. Checking email configuration...")
    if 'email_account' in existing_tables:
        cursor.execute("SELECT COUNT(*) FROM email_account WHERE is_active = 1")
        active_count = cursor.fetchone()[0]
        
        cursor.execute("SELECT COUNT(*) FROM email_account WHERE is_default = 1")
        default_count = cursor.fetchone()[0]
        
        print(f"   📧 Active email accounts: {active_count}")
        print(f"   ⭐ Default email account: {'Yes' if default_count > 0 else 'No'}")
        
        if active_count == 0:
            print("   ⚠️  WARNING: No active email accounts configured!")
            print("   💡 Add an email account in the admin panel")
    
    conn.close()
    
    print()
    print("=" * 60)
    print("DIAGNOSIS COMPLETE")
    print("=" * 60)
    
except Exception as e:
    print(f"   ❌ Error: {str(e)}")
    import traceback
    traceback.print_exc()
