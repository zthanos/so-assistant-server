-- Migration: Create requirement_documents table
-- Version: 001
-- Description: Create versioned requirements documents table with indexes
-- Date: 2025-08-03

-- Create requirement_documents table
CREATE TABLE IF NOT EXISTS requirement_documents (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    project_id VARCHAR(255) NOT NULL,
    content TEXT NOT NULL,
    version INTEGER NOT NULL,
    status VARCHAR(50) DEFAULT 'draft' CHECK (status IN ('draft', 'published', 'archived')),
    source_type VARCHAR(50) DEFAULT 'manual' CHECK (source_type IN ('manual', 'pdf_upload')),
    original_filename VARCHAR(255),
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    
    -- Constraints
    UNIQUE(project_id, version),
    CHECK (version > 0),
    CHECK (length(content) > 0)
);

-- Create indexes for efficient queries
CREATE INDEX IF NOT EXISTS idx_requirement_documents_project_version 
ON requirement_documents(project_id, version);

CREATE INDEX IF NOT EXISTS idx_requirement_documents_project_created 
ON requirement_documents(project_id, created_at DESC);

CREATE INDEX IF NOT EXISTS idx_requirement_documents_status 
ON requirement_documents(status);

CREATE INDEX IF NOT EXISTS idx_requirement_documents_source_type 
ON requirement_documents(source_type);

-- Create trigger to update updated_at timestamp
CREATE TRIGGER IF NOT EXISTS update_requirement_documents_updated_at
    AFTER UPDATE ON requirement_documents
    FOR EACH ROW
BEGIN
    UPDATE requirement_documents 
    SET updated_at = CURRENT_TIMESTAMP 
    WHERE id = NEW.id;
END;

-- Insert migration record
INSERT OR IGNORE INTO schema_migrations (version, description, applied_at) 
VALUES ('001', 'Create requirement_documents table', CURRENT_TIMESTAMP);