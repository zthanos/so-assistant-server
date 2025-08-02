#!/usr/bin/env python3
"""Migration script to add missing columns to database tables."""

import sqlite3
import os
from pathlib import Path

def migrate_database():
    """Add missing columns to database tables."""
    
    # Find the database file
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
        
        # Migrate projects table
        print("\n=== Migrating projects table ===")
        cursor.execute("PRAGMA table_info(projects)")
        columns = [column[1] for column in cursor.fetchall()]
        print(f"Current columns in projects table: {columns}")
        
        # Add code column if it doesn't exist
        if 'code' not in columns:
            print("Adding 'code' column...")
            cursor.execute("ALTER TABLE projects ADD COLUMN code VARCHAR(255)")
            print("✓ Added 'code' column")
        else:
            print("✓ 'code' column already exists")
        
        # Add state column if it doesn't exist
        if 'state' not in columns:
            print("Adding 'state' column...")
            cursor.execute("ALTER TABLE projects ADD COLUMN state VARCHAR(50) DEFAULT 'active'")
            print("✓ Added 'state' column")
        else:
            print("✓ 'state' column already exists")
        
        # Migrate teams table
        print("\n=== Migrating teams table ===")
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='teams'")
        if cursor.fetchone():
            cursor.execute("PRAGMA table_info(teams)")
            team_columns = [column[1] for column in cursor.fetchall()]
            print(f"Current columns in teams table: {team_columns}")
            
            # Add created_at column if it doesn't exist
            if 'created_at' not in team_columns:
                print("Adding 'created_at' column to teams...")
                cursor.execute("ALTER TABLE teams ADD COLUMN created_at DATETIME DEFAULT CURRENT_TIMESTAMP")
                print("✓ Added 'created_at' column to teams")
            else:
                print("✓ 'created_at' column already exists in teams")
            
            # Add updated_at column if it doesn't exist
            if 'updated_at' not in team_columns:
                print("Adding 'updated_at' column to teams...")
                cursor.execute("ALTER TABLE teams ADD COLUMN updated_at DATETIME DEFAULT CURRENT_TIMESTAMP")
                print("✓ Added 'updated_at' column to teams")
            else:
                print("✓ 'updated_at' column already exists in teams")
        else:
            print("⚠️ Teams table does not exist")
        
        # Migrate tasks table
        print("\n=== Migrating tasks table ===")
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='tasks'")
        if cursor.fetchone():
            cursor.execute("PRAGMA table_info(tasks)")
            task_columns = [column[1] for column in cursor.fetchall()]
            print(f"Current columns in tasks table: {task_columns}")
            
            # Add created_at column if it doesn't exist
            if 'created_at' not in task_columns:
                print("Adding 'created_at' column to tasks...")
                cursor.execute("ALTER TABLE tasks ADD COLUMN created_at DATETIME DEFAULT CURRENT_TIMESTAMP")
                print("✓ Added 'created_at' column to tasks")
            else:
                print("✓ 'created_at' column already exists in tasks")
            
            # Add updated_at column if it doesn't exist
            if 'updated_at' not in task_columns:
                print("Adding 'updated_at' column to tasks...")
                cursor.execute("ALTER TABLE tasks ADD COLUMN updated_at DATETIME DEFAULT CURRENT_TIMESTAMP")
                print("✓ Added 'updated_at' column to tasks")
            else:
                print("✓ 'updated_at' column already exists in tasks")
        else:
            print("⚠️ Tasks table does not exist")
        
        # Check requirements table
        print("\n=== Checking requirements table ===")
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='requirements'")
        if cursor.fetchone():
            cursor.execute("PRAGMA table_info(requirements)")
            req_columns = [column[1] for column in cursor.fetchall()]
            print(f"Requirements table columns: {req_columns}")
        else:
            print("⚠️ Requirements table does not exist - will be created by SQLAlchemy")
        
        # Check diagrams table
        print("\n=== Checking diagrams table ===")
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='diagrams'")
        if cursor.fetchone():
            cursor.execute("PRAGMA table_info(diagrams)")
            diag_columns = [column[1] for column in cursor.fetchall()]
            print(f"Diagrams table columns: {diag_columns}")
        else:
            print("⚠️ Diagrams table does not exist - will be created by SQLAlchemy")
        
        conn.commit()
        conn.close()
        
        print("\n✅ Database migration completed successfully!")
        return True
        
    except Exception as e:
        print(f"❌ Error during migration: {e}")
        return False

if __name__ == "__main__":
    migrate_database()