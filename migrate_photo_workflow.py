#!/usr/bin/env python3
"""
Database migration script for photo workflow feature.
Adds new tables and columns for photo processing.

Run this script to update existing database:
python migrate_photo_workflow.py
"""

import sqlite3
import os
from datetime import datetime

def migrate_database():
    """Add photo workflow tables and columns to existing database"""
    
    # Database path
    db_path = 'registrations.db'
    
    if not os.path.exists(db_path):
        print(f"❌ Database not found: {db_path}")
        print("Please run the application first to create the initial database.")
        return False
    
    print(f"🔄 Starting migration for {db_path}")
    
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # Backup existing data
        print("📦 Creating backup...")
        backup_path = f'registrations_backup_{datetime.now().strftime("%Y%m%d_%H%M%S")}.db'
        backup_conn = sqlite3.connect(backup_path)
        conn.backup(backup_conn)
        backup_conn.close()
        print(f"✅ Backup created: {backup_path}")
        
        # Check if migration is needed
        cursor.execute("PRAGMA table_info(registration)")
        columns = [col[1] for col in cursor.fetchall()]
        
        if 'qr_token' in columns:
            print("ℹ️  Migration appears to have been run already.")
            response = input("Do you want to continue anyway? (y/n): ")
            if response.lower() != 'y':
                print("Migration cancelled.")
                conn.close()
                return False
        
        print("\n📝 Adding columns to registration table...")
        
        # Add new columns to Registration table (without UNIQUE constraint initially)
        migrations = [
            ("qr_token", "ALTER TABLE registration ADD COLUMN qr_token VARCHAR(100)"),
            ("photo_count", "ALTER TABLE registration ADD COLUMN photo_count INTEGER DEFAULT 0"),
            ("drive_folder_id", "ALTER TABLE registration ADD COLUMN drive_folder_id VARCHAR(200)"),
            ("drive_share_link", "ALTER TABLE registration ADD COLUMN drive_share_link VARCHAR(500)"),
            ("photos_email_sent", "ALTER TABLE registration ADD COLUMN photos_email_sent BOOLEAN DEFAULT 0"),
            ("photos_email_sent_at", "ALTER TABLE registration ADD COLUMN photos_email_sent_at DATETIME"),
        ]
        
        for col_name, sql in migrations:
            try:
                cursor.execute(sql)
                print(f"  ✅ Added column: {col_name}")
            except sqlite3.OperationalError as e:
                if "duplicate column name" in str(e).lower():
                    print(f"  ⏭️  Column already exists: {col_name}")
                else:
                    raise
        
        print("\n📝 Creating photo_batch table...")
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS photo_batch (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                batch_name VARCHAR(200) NOT NULL,
                upload_time DATETIME DEFAULT CURRENT_TIMESTAMP,
                total_photos INTEGER DEFAULT 0,
                total_size_mb REAL DEFAULT 0.0,
                processed_photos INTEGER DEFAULT 0,
                status VARCHAR(50) DEFAULT 'uploading',
                current_action VARCHAR(500),
                people_found INTEGER DEFAULT 0,
                unmatched_photos INTEGER DEFAULT 0,
                processing_started_at DATETIME,
                processing_completed_at DATETIME,
                error_message TEXT
            )
        """)
        print("  ✅ photo_batch table created")
        
        print("\n📝 Creating photo table...")
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS photo (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                batch_id INTEGER NOT NULL,
                registration_id INTEGER,
                filename VARCHAR(500) NOT NULL,
                original_path VARCHAR(500) NOT NULL,
                file_size INTEGER DEFAULT 0,
                is_qr_code BOOLEAN DEFAULT 0,
                qr_data VARCHAR(500),
                processed BOOLEAN DEFAULT 0,
                uploaded_to_drive BOOLEAN DEFAULT 0,
                upload_time DATETIME DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (batch_id) REFERENCES photo_batch (id),
                FOREIGN KEY (registration_id) REFERENCES registration (id)
            )
        """)
        print("  ✅ photo table created")
        
        print("\n📝 Creating processing_log table...")
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS processing_log (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                batch_id INTEGER NOT NULL,
                timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
                action VARCHAR(100) NOT NULL,
                message TEXT NOT NULL,
                level VARCHAR(20) DEFAULT 'info',
                registration_id INTEGER,
                photo_id INTEGER,
                FOREIGN KEY (batch_id) REFERENCES photo_batch (id),
                FOREIGN KEY (registration_id) REFERENCES registration (id),
                FOREIGN KEY (photo_id) REFERENCES photo (id)
            )
        """)
        print("  ✅ processing_log table created")
        
        # Create indexes for better performance
        print("\n📝 Creating indexes...")
        indexes = [
            "CREATE INDEX IF NOT EXISTS idx_photo_batch_id ON photo(batch_id)",
            "CREATE INDEX IF NOT EXISTS idx_photo_registration_id ON photo(registration_id)",
            "CREATE INDEX IF NOT EXISTS idx_photo_filename ON photo(filename)",
            "CREATE INDEX IF NOT EXISTS idx_processing_log_batch_id ON processing_log(batch_id)",
        ]
        
        for idx_sql in indexes:
            cursor.execute(idx_sql)
            print(f"  ✅ Index created")
        
        # Generate QR tokens for existing registrations
        print("\n📝 Generating QR tokens for existing registrations...")
        cursor.execute("SELECT id FROM registration WHERE qr_token IS NULL")
        registrations_without_token = cursor.fetchall()
        
        if registrations_without_token:
            import uuid
            for (reg_id,) in registrations_without_token:
                qr_token = str(uuid.uuid4())
                cursor.execute("UPDATE registration SET qr_token = ? WHERE id = ?", (qr_token, reg_id))
            print(f"  ✅ Generated QR tokens for {len(registrations_without_token)} existing registrations")
        else:
            print("  ℹ️  All registrations already have QR tokens")
        
        # Create UNIQUE index on qr_token after all tokens are generated
        print("\n📝 Creating UNIQUE index on qr_token...")
        try:
            cursor.execute("CREATE UNIQUE INDEX IF NOT EXISTS idx_registration_qr_token_unique ON registration(qr_token) WHERE qr_token IS NOT NULL")
            print("  ✅ UNIQUE index created on qr_token")
        except Exception as e:
            print(f"  ⚠️  Could not create UNIQUE index: {e}")
            print("  ℹ️  This is not critical, continuing...")
        
        # Commit changes
        conn.commit()
        print("\n✅ Migration completed successfully!")
        print(f"📊 Backup saved at: {backup_path}")
        
        # Show table summary
        print("\n📊 Database Summary:")
        cursor.execute("SELECT COUNT(*) FROM registration")
        reg_count = cursor.fetchone()[0]
        print(f"  • Registrations: {reg_count}")
        
        cursor.execute("SELECT COUNT(*) FROM photo_batch")
        batch_count = cursor.fetchone()[0]
        print(f"  • Photo Batches: {batch_count}")
        
        cursor.execute("SELECT COUNT(*) FROM photo")
        photo_count = cursor.fetchone()[0]
        print(f"  • Photos: {photo_count}")
        
        cursor.execute("SELECT COUNT(*) FROM processing_log")
        log_count = cursor.fetchone()[0]
        print(f"  • Processing Logs: {log_count}")
        
        conn.close()
        return True
        
    except Exception as e:
        print(f"\n❌ Migration failed: {e}")
        print("The database has not been modified (except for the backup).")
        if 'conn' in locals():
            conn.close()
        return False

if __name__ == '__main__':
    print("=" * 60)
    print("Photo Workflow Database Migration")
    print("=" * 60)
    print()
    
    success = migrate_database()
    
    if success:
        print("\n✅ You can now restart your application to use the photo workflow features.")
    else:
        print("\n❌ Migration was not successful. Please check the errors above.")
    
    print()
    input("Press Enter to exit...")
