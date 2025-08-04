-- Migration: Migrate existing requirements data
-- Version: 002
-- Description: Migrate existing requirements to versioned requirement_documents table
-- Date: 2025-08-03

-- Create temporary backup of existing requirements (if table exists)
CREATE TABLE IF NOT EXISTS requirements_backup AS 
SELECT * FROM requirements WHERE 1=0;

-- Only proceed if requirements table exists
INSERT OR IGNORE INTO requirements_backup 
SELECT * FROM requirements WHERE EXISTS (SELECT name FROM sqlite_master WHERE type='table' AND name='requirements');

-- Migrate existing requirements to requirement_documents
-- Each existing requirement becomes version 1 of a requirements document
INSERT OR IGNORE INTO requirement_documents (
    project_id,
    content,
    version,
    status,
    source_type,
    original_filename,
    created_at,
    updated_at
)
SELECT 
    project_id,
    CASE 
        WHEN description IS NOT NULL AND description != '' THEN 
            '# Requirements Document' || CHAR(10) || CHAR(10) || 
            '## Requirements' || CHAR(10) || CHAR(10) || 
            '1. ' || description
        ELSE 
            '# Requirements Document' || CHAR(10) || CHAR(10) || 
            '## Requirements' || CHAR(10) || CHAR(10) || 
            '1. No description provided'
    END as content,
    1 as version,
    CASE 
        WHEN status = 'approved' THEN 'published'
        WHEN status = 'implemented' THEN 'published'
        ELSE 'draft'
    END as status,
    'manual' as source_type,
    NULL as original_filename,
    COALESCE(created_at, CURRENT_TIMESTAMP) as created_at,
    COALESCE(updated_at, CURRENT_TIMESTAMP) as updated_at
FROM requirements 
WHERE EXISTS (SELECT name FROM sqlite_master WHERE type='table' AND name='requirements')
AND project_id IS NOT NULL;

-- Create summary of migration
CREATE TEMPORARY TABLE migration_summary AS
SELECT 
    COUNT(*) as total_migrated,
    COUNT(DISTINCT project_id) as projects_affected,
    MIN(created_at) as earliest_requirement,
    MAX(created_at) as latest_requirement
FROM requirement_documents 
WHERE version = 1;

-- Log migration results
INSERT OR IGNORE INTO migration_log (
    migration_version,
    description,
    records_affected,
    details,
    applied_at
) 
SELECT 
    '002',
    'Migrate existing requirements to versioned documents',
    total_migrated,
    'Projects affected: ' || projects_affected || 
    ', Date range: ' || COALESCE(earliest_requirement, 'N/A') || 
    ' to ' || COALESCE(latest_requirement, 'N/A'),
    CURRENT_TIMESTAMP
FROM migration_summary;

-- Insert migration record
INSERT OR IGNORE INTO schema_migrations (version, description, applied_at) 
VALUES ('002', 'Migrate existing requirements data', CURRENT_TIMESTAMP);