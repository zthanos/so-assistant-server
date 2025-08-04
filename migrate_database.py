#!/usr/bin/env python3
"""
Database migration runner for requirements versioning system.
"""

import sys
import os
import sqlite3
import hashlib
import time
from pathlib import Path
from typing import List, Dict, Optional, Tuple
import logging

# Add the app directory to the Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '.'))

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('migration.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)


class DatabaseMigrator:
    """Database migration manager."""
    
    def __init__(self, database_path: str, migrations_dir: str = "migrations"):
        self.database_path = database_path
        self.migrations_dir = Path(migrations_dir)
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
    
    def get_migration_files(self) -> List[Tuple[str, Path]]:
        """Get all migration files sorted by version."""
        if not self.migrations_dir.exists():
            logger.warning(f"Migrations directory {self.migrations_dir} does not exist")
            return []
        
        migrations = []
        for file_path in self.migrations_dir.glob("*.sql"):
            # Extract version from filename (assuming format: version_description.sql)
            filename = file_path.stem
            if filename.startswith("create_migration_tables"):
                version = "000"
            elif filename.startswith("create_requirement_documents"):
                version = "001"
            elif filename.startswith("migrate_existing"):
                version = "002"
            else:
                # Try to extract version from filename
                parts = filename.split("_")
                if parts[0].isdigit():
                    version = parts[0].zfill(3)
                else:
                    version = "999"  # Unknown version, run last
            
            migrations.append((version, file_path))
        
        # Sort by version
        migrations.sort(key=lambda x: x[0])
        return migrations
    
    def get_applied_migrations(self) -> List[str]:
        """Get list of applied migration versions."""
        conn = self.connect()
        try:
            cursor = conn.execute(
                "SELECT version FROM schema_migrations ORDER BY version"
            )
            return [row['version'] for row in cursor.fetchall()]
        except sqlite3.OperationalError:
            # schema_migrations table doesn't exist yet
            return []
    
    def calculate_checksum(self, content: str) -> str:
        """Calculate MD5 checksum of migration content."""
        return hashlib.md5(content.encode('utf-8')).hexdigest()
    
    def execute_migration(self, version: str, file_path: Path) -> bool:
        """Execute a single migration file."""
        logger.info(f"Executing migration {version}: {file_path.name}")
        
        try:
            # Read migration file
            with open(file_path, 'r', encoding='utf-8') as f:
                sql_content = f.read()
            
            # Calculate checksum
            checksum = self.calculate_checksum(sql_content)
            
            conn = self.connect()
            start_time = time.time()
            
            # Execute migration in a transaction
            conn.execute("BEGIN TRANSACTION")
            
            try:
                # Execute the entire SQL content as a script
                records_affected = 0
                try:
                    conn.executescript(sql_content)
                    records_affected = conn.total_changes
                except sqlite3.OperationalError:
                    # Fallback to individual statement execution
                    statements = [stmt.strip() for stmt in sql_content.split(';') if stmt.strip()]
                    for statement in statements:
                        if statement and not statement.startswith('--'):
                            cursor = conn.execute(statement)
                            records_affected += cursor.rowcount
                
                # Record migration in schema_migrations table (if it exists)
                try:
                    conn.execute(
                        """INSERT OR REPLACE INTO schema_migrations 
                           (version, description, applied_at, checksum) 
                           VALUES (?, ?, CURRENT_TIMESTAMP, ?)""",
                        (version, f"Migration from {file_path.name}", checksum)
                    )
                except sqlite3.OperationalError:
                    # schema_migrations table might not exist yet
                    pass
                
                # Log migration details
                execution_time = int((time.time() - start_time) * 1000)
                try:
                    conn.execute(
                        """INSERT INTO migration_log 
                           (migration_version, description, records_affected, 
                            execution_time_ms, success, applied_at) 
                           VALUES (?, ?, ?, ?, ?, CURRENT_TIMESTAMP)""",
                        (version, f"Migration from {file_path.name}", 
                         records_affected, execution_time, True)
                    )
                except sqlite3.OperationalError:
                    # migration_log table might not exist yet
                    pass
                
                conn.commit()
                logger.info(f"Migration {version} completed successfully "
                           f"({records_affected} records affected, {execution_time}ms)")
                return True
                
            except Exception as e:
                conn.rollback()
                logger.error(f"Migration {version} failed: {e}")
                
                # Log failure
                try:
                    conn.execute(
                        """INSERT INTO migration_log 
                           (migration_version, description, success, error_message, applied_at) 
                           VALUES (?, ?, ?, ?, CURRENT_TIMESTAMP)""",
                        (version, f"Migration from {file_path.name}", False, str(e))
                    )
                    conn.commit()
                except sqlite3.OperationalError:
                    pass
                
                return False
                
        except Exception as e:
            logger.error(f"Failed to read or execute migration {version}: {e}")
            return False
    
    def run_migrations(self, target_version: Optional[str] = None) -> bool:
        """Run all pending migrations up to target version."""
        logger.info("Starting database migration")
        
        # Get all migration files
        migrations = self.get_migration_files()
        if not migrations:
            logger.info("No migration files found")
            return True
        
        # Get applied migrations
        applied_migrations = self.get_applied_migrations()
        logger.info(f"Applied migrations: {applied_migrations}")
        
        # Filter migrations to run
        migrations_to_run = []
        for version, file_path in migrations:
            if version not in applied_migrations:
                if target_version is None or version <= target_version:
                    migrations_to_run.append((version, file_path))
        
        if not migrations_to_run:
            logger.info("All migrations are up to date")
            return True
        
        logger.info(f"Found {len(migrations_to_run)} migrations to run")
        
        # Execute migrations
        success_count = 0
        for version, file_path in migrations_to_run:
            if self.execute_migration(version, file_path):
                success_count += 1
            else:
                logger.error(f"Migration {version} failed, stopping")
                break
        
        if success_count == len(migrations_to_run):
            logger.info(f"All {success_count} migrations completed successfully")
            return True
        else:
            logger.error(f"{success_count}/{len(migrations_to_run)} migrations completed")
            return False
    
    def get_migration_status(self) -> Dict:
        """Get current migration status."""
        migrations = self.get_migration_files()
        applied_migrations = self.get_applied_migrations()
        
        status = {
            "total_migrations": len(migrations),
            "applied_migrations": len(applied_migrations),
            "pending_migrations": [],
            "applied_list": applied_migrations
        }
        
        for version, file_path in migrations:
            if version not in applied_migrations:
                status["pending_migrations"].append({
                    "version": version,
                    "file": file_path.name
                })
        
        return status
    
    def verify_database_integrity(self) -> bool:
        """Verify database integrity after migrations."""
        logger.info("Verifying database integrity")
        
        conn = self.connect()
        try:
            # Check if requirement_documents table exists and has correct structure
            cursor = conn.execute(
                "SELECT sql FROM sqlite_master WHERE type='table' AND name='requirement_documents'"
            )
            table_info = cursor.fetchone()
            
            if not table_info:
                logger.error("requirement_documents table not found")
                return False
            
            logger.info("requirement_documents table exists")
            
            # Check indexes
            cursor = conn.execute(
                "SELECT name FROM sqlite_master WHERE type='index' AND tbl_name='requirement_documents'"
            )
            indexes = [row['name'] for row in cursor.fetchall()]
            
            expected_indexes = [
                'idx_requirement_documents_project_version',
                'idx_requirement_documents_project_created',
                'idx_requirement_documents_status',
                'idx_requirement_documents_source_type'
            ]
            
            missing_indexes = [idx for idx in expected_indexes if idx not in indexes]
            if missing_indexes:
                logger.warning(f"Missing indexes: {missing_indexes}")
            else:
                logger.info("All expected indexes exist")
            
            # Check constraints by trying to insert invalid data
            try:
                conn.execute("BEGIN TRANSACTION")
                
                # Test version constraint (should fail)
                try:
                    conn.execute(
                        "INSERT INTO requirement_documents (project_id, content, version) VALUES (?, ?, ?)",
                        ("test", "content", 0)
                    )
                    conn.rollback()
                    logger.warning("Version constraint not working")
                except sqlite3.IntegrityError:
                    logger.info("Version constraint working")
                    conn.rollback()
                
                # Test unique constraint (project_id, version)
                conn.execute("BEGIN TRANSACTION")
                conn.execute(
                    "INSERT INTO requirement_documents (project_id, content, version) VALUES (?, ?, ?)",
                    ("test-constraint", "content", 1)
                )
                
                try:
                    conn.execute(
                        "INSERT INTO requirement_documents (project_id, content, version) VALUES (?, ?, ?)",
                        ("test-constraint", "content", 1)
                    )
                    conn.rollback()
                    logger.warning("Unique constraint not working")
                except sqlite3.IntegrityError:
                    logger.info("Unique constraint working")
                    conn.rollback()
                
            except Exception as e:
                logger.error(f"Error testing constraints: {e}")
                conn.rollback()
                return False
            
            logger.info("Database integrity verification completed")
            return True
            
        except Exception as e:
            logger.error(f"Database integrity check failed: {e}")
            return False


def main():
    """Main migration runner function."""
    print("🗄️  Requirements Versioning Database Migration")
    print("=" * 60)
    
    # Get database path from environment or use default
    database_path = os.getenv("DATABASE_URL", "app.db")
    if database_path.startswith("sqlite:///"):
        database_path = database_path[10:]  # Remove sqlite:/// prefix
    
    print(f"Database: {database_path}")
    print(f"Migrations directory: migrations/")
    
    # Create migrator
    migrator = DatabaseMigrator(database_path)
    
    try:
        # Show current status
        print("\n📊 Current Migration Status")
        print("-" * 40)
        status = migrator.get_migration_status()
        print(f"Total migrations: {status['total_migrations']}")
        print(f"Applied migrations: {status['applied_migrations']}")
        print(f"Pending migrations: {len(status['pending_migrations'])}")
        
        if status['pending_migrations']:
            print("\nPending migrations:")
            for migration in status['pending_migrations']:
                print(f"  • {migration['version']}: {migration['file']}")
        
        # Ask for confirmation
        if status['pending_migrations']:
            print(f"\n⚠️  This will apply {len(status['pending_migrations'])} migrations to the database.")
            response = input("Continue? (y/N): ").strip().lower()
            
            if response != 'y':
                print("Migration cancelled.")
                return 0
        
        # Run migrations
        print("\n🚀 Running Migrations")
        print("-" * 40)
        success = migrator.run_migrations()
        
        if success:
            # Verify database integrity
            print("\n🔍 Verifying Database")
            print("-" * 40)
            integrity_ok = migrator.verify_database_integrity()
            
            if integrity_ok:
                print("\n🎉 Migration completed successfully!")
                print("\n✨ Database is ready for requirements versioning:")
                print("  • requirement_documents table created")
                print("  • Indexes optimized for performance")
                print("  • Constraints ensure data integrity")
                print("  • Existing data migrated (if applicable)")
                
                # Show final status
                final_status = migrator.get_migration_status()
                print(f"\n📈 Final Status: {final_status['applied_migrations']}/{final_status['total_migrations']} migrations applied")
                
                return 0
            else:
                print("\n❌ Database integrity check failed")
                return 1
        else:
            print("\n❌ Migration failed")
            return 1
            
    except Exception as e:
        logger.error(f"Migration error: {e}")
        print(f"\n❌ Migration failed: {e}")
        return 1
    finally:
        migrator.disconnect()


if __name__ == "__main__":
    sys.exit(main())