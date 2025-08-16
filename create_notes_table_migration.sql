-- Migration to create notes table
-- Run this SQL script to create the notes table

-- Create notes table
CREATE TABLE notes (
    id INT AUTO_INCREMENT PRIMARY KEY,
    project_id VARCHAR(255) NOT NULL,
    title VARCHAR(255) NOT NULL,
    description TEXT,
    content TEXT,
    tags JSON,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    
    -- Foreign key constraint
    FOREIGN KEY (project_id) REFERENCES projects(id) ON DELETE CASCADE,
    
    -- Indexes for better performance
    INDEX idx_notes_project_id (project_id),
    INDEX idx_notes_title (title),
    INDEX idx_notes_created_at (created_at),
    INDEX idx_notes_updated_at (updated_at)
);

-- Add unique constraint for title within project (optional, uncomment if needed)
-- ALTER TABLE notes ADD CONSTRAINT unique_title_per_project UNIQUE (project_id, title);