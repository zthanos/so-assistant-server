CREATE TABLE IF NOT EXISTS requirement_documents (
  id                INTEGER PRIMARY KEY AUTOINCREMENT,
  project_id        VARCHAR(255) NOT NULL,
  content           TEXT NOT NULL,
  version           INTEGER NOT NULL,
  status            VARCHAR(50)  DEFAULT 'draft',
  source_type       VARCHAR(50)  DEFAULT 'manual',
  original_filename VARCHAR(255),
  created_at        DATETIME     DEFAULT CURRENT_TIMESTAMP,
  updated_at        DATETIME     DEFAULT CURRENT_TIMESTAMP,
  FOREIGN KEY (project_id) REFERENCES projects(id),
  UNIQUE(project_id, version)
);

CREATE INDEX IF NOT EXISTS idx_reqdocs_project_version
  ON requirement_documents(project_id, version);

CREATE INDEX IF NOT EXISTS idx_reqdocs_project_created
  ON requirement_documents(project_id, created_at DESC);

CREATE INDEX IF NOT EXISTS idx_reqdocs_status
  ON requirement_documents(status);

CREATE INDEX IF NOT EXISTS idx_reqdocs_source_type
  ON requirement_documents(source_type);
