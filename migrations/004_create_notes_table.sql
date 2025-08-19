-- Migration: Create notes table
-- Version: 004
-- Description: Project notes with basic indexes and updated_at trigger

CREATE TABLE IF NOT EXISTS notes (
    id          INTEGER PRIMARY KEY AUTOINCREMENT,
    project_id  VARCHAR(255) NOT NULL,
    title       VARCHAR(255) NOT NULL,
    description TEXT,
    content     TEXT,
    tags        TEXT DEFAULT '[]',            -- store JSON as TEXT

    created_at  DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at  DATETIME DEFAULT CURRENT_TIMESTAMP,

    FOREIGN KEY (project_id) REFERENCES projects(id) ON DELETE CASCADE
);

-- Optional (αν έχεις το JSON1 extension): επιβολή έγκυρου JSON
-- ALTER TABLE notes ADD CONSTRAINT ck_notes_tags_json CHECK (json_valid(tags));

-- Indexes
CREATE INDEX IF NOT EXISTS idx_notes_project_id  ON notes(project_id);
CREATE INDEX IF NOT EXISTS idx_notes_title       ON notes(title);
CREATE INDEX IF NOT EXISTS idx_notes_created_at  ON notes(created_at);
CREATE INDEX IF NOT EXISTS idx_notes_updated_at  ON notes(updated_at);

-- Trigger για αυτόματο updated_at (SQLite: recursive triggers off by default)
CREATE TRIGGER IF NOT EXISTS trg_notes_updated_at
AFTER UPDATE ON notes
FOR EACH ROW
BEGIN
  UPDATE notes
     SET updated_at = CURRENT_TIMESTAMP
   WHERE id = NEW.id;
END;
