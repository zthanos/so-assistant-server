-- Migration: Create migration tracking tables
-- Version: 000
-- Description: Create tables to track database migrations and changes
-- Date: 2025-08-03

-- Create schema_migrations table to track applied migrations
CREATE TABLE IF NOT EXISTS schema_migrations (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    version VARCHAR(10) NOT NULL UNIQUE,
    description TEXT NOT NULL,
    applied_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    rollback_sql TEXT,
    checksum VARCHAR(64)
);

-- Create migration_log table for detailed migration logging
CREATE TABLE IF NOT EXISTS migration_log (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    migration_version VARCHAR(10) NOT NULL,
    description TEXT NOT NULL,
    records_affected INTEGER DEFAULT 0,
    details TEXT,
    applied_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    execution_time_ms INTEGER,
    success BOOLEAN DEFAULT TRUE,
    error_message TEXT
);

-- Create index for efficient migration queries
CREATE INDEX IF NOT EXISTS idx_schema_migrations_version 
ON schema_migrations(version);

CREATE INDEX IF NOT EXISTS idx_migration_log_version 
ON migration_log(migration_version);

CREATE INDEX IF NOT EXISTS idx_migration_log_applied_at 
ON migration_log(applied_at DESC);

-- Insert initial migration record
INSERT OR IGNORE INTO schema_migrations (version, description, applied_at) 
VALUES ('000', 'Create migration tracking tables', CURRENT_TIMESTAMP);