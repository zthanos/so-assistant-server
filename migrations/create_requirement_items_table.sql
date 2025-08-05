-- Migration: Create requirement_items table
-- Version: 002
-- Description: Create individual requirement items table with status tracking and indexes
-- Date: 2025-08-04

-- Create requirement_items table
CREATE TABLE IF NOT EXISTS requirement_items (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    project_id VARCHAR(255) NOT NULL,
    title VARCHAR(500) NOT NULL,
    description TEXT NOT NULL,
    priority VARCHAR(20) DEFAULT 'medium' CHECK (priority IN ('low', 'medium', 'high', 'critical')),
    status VARCHAR(20) DEFAULT 'new' CHECK (status IN ('new', 'accepted', 'rejected')),
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    
    -- Foreign key constraint
    FOREIGN KEY (project_id) REFERENCES projects (id) ON DELETE CASCADE,
    
    -- Constraints
    CHECK (length(title) > 0 AND length(title) <= 500),
    CHECK (length(description) > 0)
);

-- Create indexes for efficient queries
CREATE INDEX IF NOT EXISTS idx_requirement_items_project_id 
ON requirement_items(project_id);

CREATE INDEX IF NOT EXISTS idx_requirement_items_status 
ON requirement_items(status);

CREATE INDEX IF NOT EXISTS idx_requirement_items_project_status 
ON requirement_items(project_id, status);

CREATE INDEX IF NOT EXISTS idx_requirement_items_priority 
ON requirement_items(priority);

CREATE INDEX IF NOT EXISTS idx_requirement_items_project_created 
ON requirement_items(project_id, created_at DESC);

-- Create trigger to update updated_at timestamp
CREATE TRIGGER IF NOT EXISTS update_requirement_items_updated_at
    AFTER UPDATE ON requirement_items
    FOR EACH ROW
BEGIN
    UPDATE requirement_items 
    SET updated_at = CURRENT_TIMESTAMP 
    WHERE id = NEW.id;
END;

-- Insert migration record
INSERT OR IGNORE INTO schema_migrations (version, description, applied_at) 
VALUES ('002', 'Create requirement_items table', CURRENT_TIMESTAMP);