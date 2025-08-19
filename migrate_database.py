#!/usr/bin/env python3
"""
Database migration runner (SQLite).
- Reads migrations from a directory, expecting filenames: NNN_description.sql
- Applies pending migrations in numeric order
- Logs to schema_migrations & migration_log (created automatically if missing)
"""

import sys
import os
import sqlite3
import hashlib
import time
from pathlib import Path
from typing import List, Dict, Optional, Tuple
import logging

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
    handlers=[logging.FileHandler("migration.log"), logging.StreamHandler()],
)
logger = logging.getLogger(__name__)


def _sqlite_path_from_url(db_url: str) -> str:
    """Convert sqlite URL to filesystem path (sqlite:///file.db -> file.db)."""
    if db_url.startswith("sqlite:///"):
        return db_url.replace("sqlite:///", "", 1)
    if db_url.startswith("sqlite://"):
        return db_url.replace("sqlite://", "", 1)
    return db_url


class DatabaseMigrator:
    """Database migration manager."""

    def __init__(self, database_path: str, migrations_dir: str | Path = "migrations"):
        self.database_path = str(database_path)
        self.migrations_dir = Path(migrations_dir)
        self.connection: Optional[sqlite3.Connection] = None

    def connect(self) -> sqlite3.Connection:
        """Connect to the database and enable foreign keys."""
        if not self.connection:
            self.connection = sqlite3.connect(self.database_path)
            self.connection.row_factory = sqlite3.Row
            self.connection.execute("PRAGMA foreign_keys = ON")
        return self.connection

    def disconnect(self):
        """Disconnect from the database."""
        if self.connection:
            self.connection.close()
            self.connection = None

    # ---------- MIGRATIONS DISCOVERY ----------

    def get_migration_files(self) -> List[Tuple[int, Path]]:
        """
        Return [(version_int, file_path), ...] sorted by version.
        Expects filenames like: 000_create_tables.sql, 001_add_notes.sql, ...
        """
        if not self.migrations_dir.exists():
            logger.warning("Migrations directory %s does not exist", self.migrations_dir)
            return []

        migrations: List[Tuple[int, Path]] = []
        for file_path in self.migrations_dir.glob("*.sql"):
            stem = file_path.stem  # "000_create_tables"
            parts = stem.split("_", 1)
            if parts and parts[0].isdigit():
                version = int(parts[0])
                migrations.append((version, file_path))
            else:
                logger.warning("Skipping file without numeric prefix: %s", file_path.name)

        migrations.sort(key=lambda x: x[0])
        return migrations

    # ---------- STATE ----------

    def _ensure_migration_tables(self, conn: sqlite3.Connection) -> None:
        """Create schema_migrations & migration_log if missing (idempotent)."""
        conn.executescript(
            """
            CREATE TABLE IF NOT EXISTS schema_migrations (
              version     TEXT PRIMARY KEY,
              description TEXT,
              applied_at  DATETIME DEFAULT CURRENT_TIMESTAMP,
              checksum    TEXT
            );
            CREATE TABLE IF NOT EXISTS migration_log (
              id                INTEGER PRIMARY KEY AUTOINCREMENT,
              migration_version TEXT,
              description       TEXT,
              records_affected  INTEGER,
              execution_time_ms INTEGER,
              success           BOOLEAN,
              error_message     TEXT,
              applied_at        DATETIME DEFAULT CURRENT_TIMESTAMP
            );
            """
        )

    def get_applied_migrations(self) -> List[int]:
        """Return applied versions as integers; empty if table missing."""
        conn = self.connect()
        try:
            self._ensure_migration_tables(conn)
            rows = conn.execute("SELECT version FROM schema_migrations ORDER BY version").fetchall()
            out: List[int] = []
            for r in rows:
                v = str(r["version"]).strip()
                if v.isdigit():
                    out.append(int(v))
            return out
        except sqlite3.OperationalError:
            # Shouldn't happen due to ensure above, but keep safe fallback
            return []

    # ---------- EXECUTION ----------

    @staticmethod
    def _checksum(content: str) -> str:
        return hashlib.md5(content.encode("utf-8")).hexdigest()

    def execute_migration(self, version: int, file_path: Path) -> bool:
        """Execute one migration inside a transaction and log result."""
        logger.info("Executing migration %03d: %s", version, file_path.name)

        try:
            sql_content = file_path.read_text(encoding="utf-8")
        except Exception as e:
            logger.error("Failed to read migration %s: %s", file_path.name, e)
            return False

        conn = self.connect()
        self._ensure_migration_tables(conn)

        start_time = time.time()
        checksum = self._checksum(sql_content)

        try:
            conn.execute("BEGIN IMMEDIATE")  # IMMEDIATE to avoid write conflicts
            before_changes = conn.total_changes

            try:
                conn.executescript(sql_content)
            except sqlite3.OperationalError as e:
                # try per statement fallback
                logger.warning("executescript failed, falling back to per-statement: %s", e)
                statements = [s.strip() for s in sql_content.split(";") if s.strip()]
                for stmt in statements:
                    if stmt and not stmt.startswith("--"):
                        conn.execute(stmt)

            records_affected = conn.total_changes - before_changes
            exec_ms = int((time.time() - start_time) * 1000)

            # log success into schema_migrations + migration_log
            conn.execute(
                """
                INSERT OR REPLACE INTO schema_migrations (version, description, applied_at, checksum)
                VALUES (?, ?, CURRENT_TIMESTAMP, ?)
                """,
                (f"{version:03d}", f"Migration from {file_path.name}", checksum),
            )
            conn.execute(
                """
                INSERT INTO migration_log (migration_version, description, records_affected,
                                           execution_time_ms, success, applied_at)
                VALUES (?, ?, ?, ?, 1, CURRENT_TIMESTAMP)
                """,
                (f"{version:03d}", f"Migration from {file_path.name}", records_affected, exec_ms),
            )

            conn.commit()
            logger.info(
                "Migration %03d completed (%d changes, %dms)",
                version, records_affected, exec_ms
            )
            return True

        except Exception as e:
            conn.rollback()
            logger.error("Migration %03d failed: %s", version, e)
            try:
                # best-effort failure log
                conn.execute(
                    """
                    INSERT INTO migration_log (migration_version, description, success, error_message, applied_at)
                    VALUES (?, ?, 0, ?, CURRENT_TIMESTAMP)
                    """,
                    (f"{version:03d}", f"Migration from {file_path.name}", str(e)),
                )
                conn.commit()
            except Exception:
                pass
            return False

    # ---------- PUBLIC API ----------

    def run_migrations(self, target_version: Optional[int] = None) -> bool:
        """Run all pending migrations up to target_version (inclusive)."""
        logger.info("Starting database migration")
        migrations = self.get_migration_files()
        if not migrations:
            logger.info("No migration files found")
            return True

        applied = set(self.get_applied_migrations())
        logger.info("Applied migrations: %s", sorted(applied))

        to_run: List[Tuple[int, Path]] = []
        for version, path in migrations:
            if version not in applied and (target_version is None or version <= target_version):
                to_run.append((version, path))

        if not to_run:
            logger.info("All migrations are up to date")
            return True

        logger.info("Found %d migrations to run", len(to_run))

        for version, path in to_run:
            if not self.execute_migration(version, path):
                logger.error("Stopping on failure at %03d", version)
                return False

        logger.info("All migrations ran successfully")
        return True

    def get_migration_status(self) -> Dict:
        """Return current migration status summary."""
        migrations = self.get_migration_files()
        applied = set(self.get_applied_migrations())

        pending = [{"version": f"{v:03d}", "file": p.name}
                   for v, p in migrations if v not in applied]

        return {
            "total_migrations": len(migrations),
            "applied_migrations": len(applied),
            "pending_migrations": pending,
            "applied_list": [f"{v:03d}" for v in sorted(applied)],
        }

    def verify_database_integrity(self) -> bool:
        """
        Basic integrity check (customize as needed).
        By default, verify requirement_documents exists if it's part of your baseline.
        """
        logger.info("Verifying database integrity")
        conn = self.connect()
        try:
            row = conn.execute(
                "SELECT name FROM sqlite_master WHERE type='table' AND name='requirement_documents'"
            ).fetchone()
            if not row:
                logger.error("requirement_documents table not found")
                return False
            logger.info("requirement_documents table exists")
            return True
        except Exception as e:
            logger.error("Integrity check failed: %s", e)
            return False


def main() -> int:
    print("🗄️  Database Migration")
    print("=" * 60)

    # Resolve database path
    db_url = os.getenv("DATABASE_URL", "sqlite:///./so_assistant.db")
    database_path = _sqlite_path_from_url(db_url)

    # Resolve migrations directory (default: ./migrations next to this file)
    default_dir = (Path(__file__).resolve().parent / "migrations").resolve()
    migrations_dir = Path(os.getenv("MIGRATIONS_DIR", str(default_dir)))

    print(f"Database: {database_path}")
    print(f"Migrations directory: {migrations_dir}")

    migrator = DatabaseMigrator(database_path, migrations_dir)

    try:
        status = migrator.get_migration_status()
        print("\n📊 Current Migration Status")
        print("-" * 40)
        print(f"Total migrations:   {status['total_migrations']}")
        print(f"Applied migrations: {status['applied_migrations']}")
        print(f"Pending migrations: {len(status['pending_migrations'])}")
        if status["pending_migrations"]:
            print("\nPending migrations:")
            for m in status["pending_migrations"]:
                print(f"  • {m['version']}: {m['file']}")

        # Prompt unless auto-approved
        auto = os.getenv("MIGRATIONS_AUTO_APPROVE", "0") == "1"
        if status["pending_migrations"] and not auto:
            print(f"\n⚠️  This will apply {len(status['pending_migrations'])} migration(s).")
            resp = input("Continue? (y/N): ").strip().lower()
            if resp != "y":
                print("Migration cancelled.")
                return 0

        print("\n🚀 Running Migrations")
        print("-" * 40)
        ok = migrator.run_migrations()
        if not ok:
            print("\n❌ Migration failed")
            return 1

        print("\n🔍 Verifying Database")
        print("-" * 40)
        if migrator.verify_database_integrity():
            print("\n🎉 Migration completed successfully!")
            final = migrator.get_migration_status()
            print(f"\n📈 Final Status: {final['applied_migrations']}/{final['total_migrations']} applied")
            return 0
        else:
            print("\n❌ Database integrity check failed")
            return 1

    except Exception as e:
        logger.exception("Migration error")
        print(f"\n❌ Migration failed: {e}")
        return 1
    finally:
        migrator.disconnect()


if __name__ == "__main__":
    sys.exit(main())
