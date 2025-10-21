"""
Quick Database Reset and Initialization
Run this if you're getting "Registration failed" errors
"""
import os
from app import app, db, init_db

print("=" * 60)
print("DATABASE RESET & INITIALIZATION")
print("=" * 60)
print()

with app.app_context():
    try:
        # Check if database exists
        db_path = 'instance/photo_registration.db'
        
        if os.path.exists(db_path):
            print(f"Database file exists: {db_path}")
            
            # Try to query tables
            try:
                from app import Registration, EmailAccount, AdminSettings, User
                
                # Test each table
                reg_count = Registration.query.count()
                print(f"✅ Registration table: {reg_count} records")
                
                email_count = EmailAccount.query.count()
                print(f"✅ EmailAccount table: {email_count} records")
                
                settings_count = AdminSettings.query.count()
                print(f"✅ AdminSettings table: {settings_count} records")
                
                user_count = User.query.count()
                print(f"✅ User table: {user_count} records")
                
                print()
                print("✅ Database appears to be working correctly!")
                
                if email_count == 0:
                    print()
                    print("⚠️  WARNING: No email accounts configured!")
                    print("   Please add an email account in the admin panel:")
                    print("   1. Login to admin panel")
                    print("   2. Go to 'Email Accounts'")
                    print("   3. Click 'Add New Account'")
                    print("   4. Configure your SMTP settings")
                
            except Exception as e:
                print(f"❌ Database tables have issues: {str(e)}")
                print()
                print("Attempting to recreate database tables...")
                
                # Drop and recreate all tables
                db.drop_all()
                db.create_all()
                
                print("✅ Database tables recreated!")
                print()
                print("⚠️  Note: All data has been reset!")
                print("   You'll need to:")
                print("   1. Create a new admin account")
                print("   2. Configure email accounts")
        else:
            print(f"Database file doesn't exist: {db_path}")
            print("Initializing database...")
            init_db()
            print("✅ Database initialized!")
        
        print()
        print("=" * 60)
        print("You can now start the application with: python app.py")
        print("=" * 60)
        
    except Exception as e:
        print(f"❌ Error: {str(e)}")
        import traceback
        traceback.print_exc()
