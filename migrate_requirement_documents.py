#!/usr/bin/env python3
"""Migration script to create requirement_documents table with versioning support."""

import sqlite3
import os
from pathlib import Path

def migrate_requirement_documents():
    """Create requirement_documents table and add necessary indexes."""
    
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
        
        # Check if requirement_documents table exists
        print("\n=== Checking requirement_documents table ===")
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='requirement_documents'")
        table_exists = cursor.fetchone() is not None
        
        if not table_exists:
            print("Creating requirement_documents table...")
            
            # Create the requirement_documents table
            create_table_sql = """
            CREATE TABLE requirement_documents (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                project_id VARCHAR(255) NOT NULL,
                content TEXT NOT NULL,
                version INTEGER NOT NULL,
                status VARCHAR(50) DEFAULT 'draft',
                source_type VARCHAR(50) DEFAULT 'manual',
                original_filename VARCHAR(255),
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (project_id) REFERENCES projects(id),
                UNIQUE(project_id, version)
            )
            """
            
            cursor.execute(create_table_sql)
            print("✓ Created requirement_documents table")
            
            # Create indexes for efficient queries
            print("Creating indexes...")
            
            # Index for project_id and version queries
            cursor.execute("""
                CREATE INDEX idx_requirement_documents_project_version 
                ON requirement_documents(project_id, version)
            """)
            print("✓ Created index: idx_requirement_documents_project_version")
            
            # Index for latest version queries (project_id, created_at DESC)
            cursor.execute("""
                CREATE INDEX idx_requirement_documents_project_created 
                ON requirement_documents(project_id, created_at DESC)
            """)
            print("✓ Created index: idx_requirement_documents_project_created")
            
            # Index for status queries
            cursor.execute("""
                CREATE INDEX idx_requirement_documents_status 
                ON requirement_documents(status)
            """)
            print("✓ Created index: idx_requirement_documents_status")
            
            # Index for source_type queries
            cursor.execute("""
                CREATE INDEX idx_requirement_documents_source_type 
                ON requirement_documents(source_type)
            """)
            print("✓ Created index: idx_requirement_documents_source_type")
            
        else:
            print("✓ requirement_documents table already exists")
            
            # Check existing columns
            cursor.execute("PRAGMA table_info(requirement_documents)")
            columns = [column[1] for column in cursor.fetchall()]
            print(f"Current columns: {columns}")
            
            # Add missing columns if needed
            expected_columns = [
                ('content', 'TEXT NOT NULL'),
                ('version', 'INTEGER NOT NULL'),
                ('status', "VARCHAR(50) DEFAULT 'draft'"),
                ('source_type', "VARCHAR(50) DEFAULT 'manual'"),
                ('original_filename', 'VARCHAR(255)'),
                ('created_at', 'DATETIME DEFAULT CURRENT_TIMESTAMP'),
                ('updated_at', 'DATETIME DEFAULT CURRENT_TIMESTAMP')
            ]
            
            for column_name, column_def in expected_columns:
                if column_name not in columns:
                    print(f"Adding missing column: {column_name}")
                    cursor.execute(f"ALTER TABLE requirement_documents ADD COLUMN {column_name} {column_def}")
                    print(f"✓ Added column: {column_name}")
        
        # Verify indexes exist
        print("\n=== Verifying indexes ===")
        cursor.execute("SELECT name FROM sqlite_master WHERE type='index' AND tbl_name='requirement_documents'")
        existing_indexes = [row[0] for row in cursor.fetchall()]
        print(f"Existing indexes: {existing_indexes}")
        
        required_indexes = [
            ('idx_requirement_documents_project_version', 'project_id, version'),
            ('idx_requirement_documents_project_created', 'project_id, created_at DESC'),
            ('idx_requirement_documents_status', 'status'),
            ('idx_requirement_documents_source_type', 'source_type')
        ]
        
        for index_name, index_columns in required_indexes:
            if index_name not in existing_indexes:
                print(f"Creating missing index: {index_name}")
                cursor.execute(f"""
                    CREATE INDEX {index_name} 
                    ON requirement_documents({index_columns})
                """)
                print(f"✓ Created index: {index_name}")
        
        # Check if we need to migrate existing requirements data
        print("\n=== Checking for existing requirements to migrate ===")
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='requirements'")
        if cursor.fetchone():
            cursor.execute("SELECT COUNT(*) FROM requirements")
            req_count = cursor.fetchone()[0]
            print(f"Found {req_count} existing requirements")
            
            if req_count > 0:
                print("Note: Existing requirements in 'requirements' table detected.")
                print("These can be migrated to requirement_documents if needed.")
                print("Migration of existing data should be done separately to avoid data loss.")
        else:
            print("No existing requirements table found")
        
        conn.commit()
        conn.close()
        
        print("\n✅ Requirement documents migration completed successfully!")
        print("\nNext steps:")
        print("1. Update your models to use the new RequirementDocument class")
        print("2. Create repositories and services for versioned requirements")
        print("3. Implement API endpoints for requirement document management")
        
        return True
        
    except Exception as e:
        print(f"❌ Error during migration: {e}")
        if 'conn' in locals():
            conn.rollback()
            conn.close()
        return False

def rollback_migration():
    """Rollback the requirement_documents table migration."""
    
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
        print("Database file not found.")
        return False
    
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        print("⚠️ Rolling back requirement_documents migration...")
        print("This will DROP the requirement_documents table and all its data!")
        
        response = input("Are you sure you want to continue? (yes/no): ")
        if response.lower() != 'yes':
            print("Rollback cancelled.")
            return False
        
        # Drop indexes first
        indexes_to_drop = [
            'idx_requirement_documents_project_version',
            'idx_requirement_documents_project_created', 
            'idx_requirement_documents_status',
            'idx_requirement_documents_source_type'
        ]
        
        for index_name in indexes_to_drop:
            try:
                cursor.execute(f"DROP INDEX IF EXISTS {index_name}")
                print(f"✓ Dropped index: {index_name}")
            except Exception as e:
                print(f"⚠️ Could not drop index {index_name}: {e}")
        
        # Drop the table
        cursor.execute("DROP TABLE IF EXISTS requirement_documents")
        print("✓ Dropped requirement_documents table")
        
        conn.commit()
        conn.close()
        
        print("✅ Rollback completed successfully!")
        return True
        
    except Exception as e:
        print(f"❌ Error during rollback: {e}")
        return False

if __name__ == "__main__":
    import sys
    
    if len(sys.argv) > 1 and sys.argv[1] == "rollback":
        rollback_migration()
    else:
        migrate_requirement_documents()