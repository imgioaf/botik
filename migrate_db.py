"""
🔧 Database Migration - Add Security Columns to Users Table
Adds 7 new security columns for 2FA and advanced security features
"""

import sqlite3
import sys
from pathlib import Path

DB_PATH = Path(__file__).parent / "switzerbot.db"

# New columns to add
MIGRATIONS = [
    ("two_fa_enabled", "BOOLEAN DEFAULT 0"),
    ("two_fa_secret", "TEXT"),
    ("backup_codes", "TEXT"),
    ("trusted_devices", "TEXT"),
    ("whitelisted_ips", "TEXT"),
    ("failed_login_attempts", "INTEGER DEFAULT 0"),
    ("locked_until", "TEXT"),
]

def migrate():
    """Execute migration"""
    try:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        
        print(f"📁 Database: {DB_PATH}")
        print(f"⏳ Starting migration...\n")
        
        # Get existing columns
        cursor.execute("PRAGMA table_info(users)")
        existing_columns = {row[1] for row in cursor.fetchall()}
        print(f"✅ Found {len(existing_columns)} existing columns\n")
        
        added = 0
        skipped = 0
        
        # Add each missing column
        for col_name, col_type in MIGRATIONS:
            if col_name in existing_columns:
                print(f"⏭️  {col_name:25} - Already exists (skipped)")
                skipped += 1
            else:
                try:
                    sql = f"ALTER TABLE users ADD COLUMN {col_name} {col_type}"
                    cursor.execute(sql)
                    print(f"✅ {col_name:25} - Added ({col_type})")
                    added += 1
                except sqlite3.OperationalError as e:
                    print(f"❌ {col_name:25} - ERROR: {str(e)[:50]}")
                    return False
        
        # Commit changes
        conn.commit()
        conn.close()
        
        print(f"\n{'='*60}")
        print(f"✅ Migration Complete!")
        print(f"   Added:   {added} columns")
        print(f"   Skipped: {skipped} columns (already exist)")
        print(f"{'='*60}")
        
        return True
        
    except sqlite3.Error as e:
        print(f"❌ Database error: {e}")
        return False
    except Exception as e:
        print(f"❌ Unexpected error: {e}")
        return False

if __name__ == "__main__":
    success = migrate()
    sys.exit(0 if success else 1)
