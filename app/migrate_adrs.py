#!/usr/bin/env python3
"""Migration script to extend ADR table with new fields (status, context, etc.)."""

import sqlite3
import os

def migrate_adrs():
    """Add new ADR fields if missing."""
    db_path = None
    possible_paths = [
        "so_assistant.db",
        "app/so_assistant.db",
        "database.db",
        "app/database.db"
    ]

    for path in possible_paths:
        if os.path.exists(path):
            db_path = path
            break

    if not db_path:
        print("Database file not found. Please ensure the database exists.")
        return False

    print(f"Found database at: {db_path}")

    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()

        # Check if adrs table exists
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='adrs'")
        if not cursor.fetchone():
            print("❌ 'adrs' table not found. Migration aborted.")
            return False

        print("✅ 'adrs' table found")

        # Check current columns
        cursor.execute("PRAGMA table_info(adrs)")
        columns = [col[1] for col in cursor.fetchall()]
        print(f"Current columns: {columns}")

        # Expected new columns
        expected_columns = [
            ("status", "VARCHAR(50) DEFAULT 'proposed'"),
            ("context", "TEXT"),
            ("decision", "TEXT"),
            ("consequences", "TEXT"),
            ("alternatives", "TEXT"),
            ("author", "VARCHAR(255)"),
            ("tags", "TEXT DEFAULT '[]'")
        ]

        for col_name, col_def in expected_columns:
            if col_name not in columns:
                print(f"Adding missing column: {col_name}")
                cursor.execute(f"ALTER TABLE adrs ADD COLUMN {col_name} {col_def}")
                print(f"✓ Added column: {col_name}")
            else:
                print(f"✓ Column already exists: {col_name}")

        conn.commit()
        conn.close()
        print("\n✅ ADR migration completed successfully!")
        print("Next steps: update your SQLAlchemy model + Pydantic schemas.")

        return True

    except Exception as e:
        print(f"❌ Error during migration: {e}")
        if 'conn' in locals():
            conn.rollback()
            conn.close()
        return False


if __name__ == "__main__":
    migrate_adrs()
