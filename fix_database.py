"""
Database Migration - Add Missing Security Columns
Fixes: sqlite3.OperationalError: no such column: users.two_fa_enabled
"""

import sqlite3
import sys
from pathlib import Path

DB_PATH = Path(__file__).parent / "switzerbot.db"

MISSING_COLUMNS = [
    ("two_fa_enabled", "BOOLEAN DEFAULT 0"),
    ("two_fa_secret", "TEXT"),
    ("backup_codes", "TEXT"),
    ("trusted_devices", "TEXT"),
    ("whitelisted_ips", "TEXT"),
    ("failed_login_attempts", "INTEGER DEFAULT 0"),
    ("locked_until", "TEXT"),
]

def check_column_exists(cursor, table, column):
    """Check if column exists in table"""
    cursor.execute(f"PRAGMA table_info({table})")
    columns = [row[1] for row in cursor.fetchall()]
    return column in columns

def migrate_database():
    """Add missing security columns to users table"""
    try:
        conn = sqlite3.connect(str(DB_PATH))
        cursor = conn.cursor()
        
        print("🔄 Database Migration Started...")
        print(f"📁 Database: {DB_PATH}")
        
        # Check existing columns
        cursor.execute("PRAGMA table_info(users)")
        existing = {row[1]: row[2] for row in cursor.fetchall()}
        print(f"\n✅ Found {len(existing)} existing columns in users table")
        print(f"   Columns: {', '.join(list(existing.keys())[:5])}...")
        
        # Add missing columns
        added = 0
        for col_name, col_type in MISSING_COLUMNS:
            if not check_column_exists(cursor, "users", col_name):
                try:
                    cursor.execute(f"ALTER TABLE users ADD COLUMN {col_name} {col_type}")
                    print(f"✅ Added column: {col_name}")
                    added += 1
                except sqlite3.OperationalError as e:
                    print(f"⚠️  Column {col_name} already exists: {e}")
            else:
                print(f"⏭️  Column {col_name} already exists")
        
        conn.commit()
        
        # Verify all columns now exist
        print("\n🔍 Verification...")
        cursor.execute("PRAGMA table_info(users)")
        final = [row[1] for row in cursor.fetchall()]
        
        required = {col[0] for col in MISSING_COLUMNS}
        found = set(final)
        
        if required.issubset(found):
            print("✅ All required columns present!")
            for col in sorted(required):
                print(f"   ✅ {col}")
        else:
            missing = required - found
            print(f"❌ Still missing: {missing}")
            return False
        
        print(f"\n📊 Total columns in users table: {len(final)}")
        print("✅ Migration completed successfully!\n")
        
        conn.close()
        return True
        
    except Exception as e:
        print(f"❌ Migration failed: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = migrate_database()
    sys.exit(0 if success else 1)
