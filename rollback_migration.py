#!/usr/bin/env python3
"""
Database migration rollback utility for requirements versioning system.
"""

import sys
import os
import sqlite3
import time
from pathlib import Path
from typing import List, Dict, Optional
import logging

# Add the app directory to the Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '.'))

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('rollback.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)


class MigrationRollback:
    """Database migration rollback manager."""
    
    def __init__(self, database_path: str):
        self.database_path = database_path
        self.connection: Optional[sqlite3.Connection] = None
        
    def connect(self) -> sqlite3.Connection:
        """Connect to the database."""
        if not self.connection:
            self.connection = sqlite3.connect(self.database_path)
            self.connection.row_factory = sqlite3.Row
            # Enable foreign key constraints
            self.connection.execute("PRAGMA foreign_keys = ON")
        return self.connection
    
    def disconnect(self):
        """Disconnect from the database."""
        if self.connection:
            self.connection.close()
            self.connection = None
    
    def get_applied_migrations(self) -> List[Dict]:
        """Get list of applied migrations with details."""
        conn = self.connect()
        try:
            cursor = conn.execute(
                """SELECT version, description, applied_at, checksum 
                   FROM schema_migrations 
                   ORDER BY version DESC"""
            )
            return [dict(row) for row in cursor.fetchall()]
        except sqlite3.OperationalError:
            logger.error("schema_migrations table not found")
            return []
    
    def backup_database(self) -> str:
        """Create a backup of the database before rollback."""
        timestamp = int(time.time())
        backup_path = f"{self.database_path}.backup.{timestamp}"
        
        logger.info(f"Creating database backup: {backup_path}")
        
        try:
            # Create backup using SQLite backup API
            source = sqlite3.connect(self.database_path)
            backup = sqlite3.connect(backup_path)
            
            source.backup(backup)
            
            source.close()
            backup.close()
            
            logger.info(f"✅ Database backup created: {backup_path}")
            return backup_path
            
        except Exception as e:
            logger.error(f"❌ Failed to create backup: {e}")
            raise
    
    def rollback_to_version(self, target_version: str) -> bool:
        """Rollback database to a specific migration version."""
        logger.info(f"🔄 Rolling back to version {target_version}")
        
        # Create backup first
        try:
            backup_path = self.backup_database()
        except Exception as e:
            logger.error(f"Cannot proceed without backup: {e}")
            return False
        
        conn = self.connect()
        
        try:
            # Get migrations to rollback (versions greater than target)
            cursor = conn.execute(
                """SELECT version, description FROM schema_migrations 
                   WHERE version > ? ORDER BY version DESC""",
                (target_version,)
            )
            migrations_to_rollback = cursor.fetchall()
            
            if not migrations_to_rollback:
                logger.info(f"✅ Already at or before version {target_version}")
                return True
            
            logger.info(f"Found {len(migrations_to_rollback)} migrations to rollback")
            
            # Perform rollback operations
            conn.execute("BEGIN TRANSACTION")
            
            try:
                for migration in migrations_to_rollback:
                    version = migration['version']
                    description = migration['description']
                    
                    logger.info(f"Rolling back migration {version}: {description}")
                    
                    # Perform version-specific rollback
                    if version == '002':  # Migrate existing requirements
                        self._rollback_requirements_migration(conn)
                    elif version == '001':  # Create requirement_documents table
                        self._rollback_table_creation(conn)
                    elif version == '000':  # Create migration tables
                        self._rollback_migration_tables(conn)
                    
                    # Remove migration record
                    conn.execute(
                        "DELETE FROM schema_migrations WHERE version = ?",
                        (version,)
                    )
                    
                    # Log rollback
                    try:
                        conn.execute(
                            """INSERT INTO migration_log 
                               (migration_version, description, success, applied_at) 
                               VALUES (?, ?, ?, CURRENT_TIMESTAMP)""",
                            (version, f"Rollback: {description}", True)
                        )
                    except sqlite3.OperationalError:
                        pass  # migration_log might not exist
                
                conn.commit()
                logger.info(f"✅ Rollback to version {target_version} completed")
                return True
                
            except Exception as e:
                conn.rollback()
                logger.error(f"❌ Rollback failed: {e}")
                logger.info(f"Database backup available at: {backup_path}")
                return False
                
        except Exception as e:
            logger.error(f"❌ Rollback preparation failed: {e}")
            return False
    
    def _rollback_requirements_migration(self, conn: sqlite3.Connection):
        """Rollback migration 002: existing requirements data migration."""
        logger.info("Rolling back requirements data migration")
        
        # Remove migrated data (version 1 documents that came from old requirements)
        conn.execute(
            "DELETE FROM requirement_documents WHERE version = 1 AND source_type = 'manual'"
        )
        
        # Restore original requirements table if backup exists
        try:
            cursor = conn.execute(
                "SELECT name FROM sqlite_master WHERE type='table' AND name='requirements_backup'"
            )
            if cursor.fetchone():
                # Restore from backup
                conn.execute("DROP TABLE IF EXISTS requirements")
                conn.execute("ALTER TABLE requirements_backup RENAME TO requirements")
                logger.info("✅ Original requirements table restored")
        except sqlite3.OperationalError:
            logger.warning("⚠️  Could not restore original requirements table")
    
    def _rollback_table_creation(self, conn: sqlite3.Connection):
        """Rollback migration 001: requirement_documents table creation."""
        logger.info("Rolling back requirement_documents table creation")
        
        # Drop indexes first
        indexes = [
            'idx_requirement_documents_project_version',
            'idx_requirement_documents_project_created',
            'idx_requirement_documents_status',
            'idx_requirement_documents_source_type'
        ]
        
        for index in indexes:
            try:
                conn.execute(f"DROP INDEX IF EXISTS {index}")
            except sqlite3.OperationalError:
                pass
        
        # Drop trigger
        try:
            conn.execute("DROP TRIGGER IF EXISTS update_requirement_documents_updated_at")
        except sqlite3.OperationalError:
            pass
        
        # Drop table
        conn.execute("DROP TABLE IF EXISTS requirement_documents")
        logger.info("✅ requirement_documents table and related objects dropped")
    
    def _rollback_migration_tables(self, conn: sqlite3.Connection):
        """Rollback migration 000: migration tracking tables."""
        logger.info("Rolling back migration tracking tables")
        
        # Drop indexes
        indexes = [
            'idx_schema_migrations_version',
            'idx_migration_log_version',
            'idx_migration_log_applied_at'
        ]
        
        for index in indexes:
            try:
                conn.execute(f"DROP INDEX IF EXISTS {index}")
            except sqlite3.OperationalError:
                pass
        
        # Drop tables (this will be the last operation)
        conn.execute("DROP TABLE IF EXISTS migration_log")
        conn.execute("DROP TABLE IF EXISTS schema_migrations")
        logger.info("✅ Migration tracking tables dropped")
    
    def show_rollback_options(self):
        """Show available rollback options."""
        migrations = self.get_applied_migrations()
        
        if not migrations:
            print("No migrations found to rollback")
            return
        
        print("\n📋 Available Rollback Options")
        print("-" * 50)
        print("Version | Description                    | Applied At")
        print("-" * 50)
        
        for migration in migrations:
            version = migration['version']
            description = migration['description'][:30]
            applied_at = migration['applied_at'][:19]  # Remove microseconds
            print(f"{version:7} | {description:30} | {applied_at}")
        
        print("-" * 50)
        print("\nTo rollback to a specific version, all migrations after that version will be undone.")
        print("Example: Rollback to version 001 will undo migrations 002, 003, etc.")


def main():
    """Main rollback function."""
    print("🔄 Requirements Versioning Database Rollback")
    print("=" * 60)
    
    # Get database path from environment or use default
    database_path = os.getenv("DATABASE_URL", "app.db")
    if database_path.startswith("sqlite:///"):
        database_path = database_path[10:]  # Remove sqlite:/// prefix
    
    print(f"Database: {database_path}")
    
    if not os.path.exists(database_path):
        print(f"❌ Database file not found: {database_path}")
        return 1
    
    # Create rollback manager
    rollback = MigrationRollback(database_path)
    
    try:
        # Show available rollback options
        rollback.show_rollback_options()
        
        migrations = rollback.get_applied_migrations()
        if not migrations:
            print("\n✅ No migrations to rollback")
            return 0
        
        # Get target version from user
        print(f"\n⚠️  WARNING: This will permanently modify your database!")
        print("A backup will be created before rollback.")
        
        target_version = input("\nEnter target version to rollback to (or 'cancel'): ").strip()
        
        if target_version.lower() == 'cancel':
            print("Rollback cancelled.")
            return 0
        
        # Validate target version
        valid_versions = [m['version'] for m in migrations]
        if target_version not in valid_versions and target_version != '':
            print(f"❌ Invalid version: {target_version}")
            print(f"Valid versions: {', '.join(valid_versions)}")
            return 1
        
        # Confirm rollback
        print(f"\n⚠️  This will rollback to version '{target_version}'")
        confirm = input("Are you sure? Type 'ROLLBACK' to confirm: ").strip()
        
        if confirm != 'ROLLBACK':
            print("Rollback cancelled.")
            return 0
        
        # Perform rollback
        print("\n🔄 Starting Rollback")
        print("-" * 40)
        success = rollback.rollback_to_version(target_version)
        
        if success:
            print("\n🎉 Rollback completed successfully!")
            print("\n✨ Database has been rolled back to the specified version.")
            print("Check rollback.log for detailed information.")
            return 0
        else:
            print("\n❌ Rollback failed!")
            print("Check rollback.log for error details.")
            print("Database backup should be available for manual recovery.")
            return 1
            
    except KeyboardInterrupt:
        print("\n\n⚠️  Rollback interrupted by user")
        return 1
    except Exception as e:
        logger.error(f"Rollback error: {e}")
        print(f"\n❌ Rollback failed: {e}")
        return 1
    finally:
        rollback.disconnect()


if __name__ == "__main__":
    sys.exit(main())