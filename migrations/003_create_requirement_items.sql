-- Ελάχιστη δομή για items συνδεδεμένα με document
CREATE TABLE IF NOT EXISTS requirement_items (
  id            INTEGER PRIMARY KEY AUTOINCREMENT,
  document_id   INTEGER NOT NULL,
  key           VARCHAR(255),     -- π.χ. "REQ-1"
  title         VARCHAR(255),
  status        VARCHAR(50)  DEFAULT 'pending',
  priority      VARCHAR(50),
  assignee      VARCHAR(255),
  tags          TEXT         DEFAULT '[]', -- JSON array
  metadata      TEXT,                      -- JSON blob
  created_at    DATETIME     DEFAULT CURRENT_TIMESTAMP,
  updated_at    DATETIME     DEFAULT CURRENT_TIMESTAMP,
  FOREIGN KEY (document_id) REFERENCES requirement_documents(id)
);

CREATE INDEX IF NOT EXISTS idx_reqitems_doc ON requirement_items(document_id);
CREATE INDEX IF NOT EXISTS idx_reqitems_status ON requirement_items(status);
