"""
Database Migration: Add DriveOAuthToken table
Run this after updating the code to add OAuth 2.0 support
"""

from app import app, db, DriveOAuthToken

def migrate():
    with app.app_context():
        print("Creating DriveOAuthToken table...")
        
        # Create the table
        db.create_all()
        
        print("✅ Migration complete!")
        print("\nThe DriveOAuthToken table has been created.")
        print("\nNext steps:")
        print("1. Add GOOGLE_OAUTH_CLIENT_ID and GOOGLE_OAUTH_CLIENT_SECRET to your .env file")
        print("2. Restart the application")
        print("3. Visit /admin/drive/oauth to connect your Google account")

if __name__ == '__main__':
    migrate()
