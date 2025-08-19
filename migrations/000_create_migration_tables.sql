-- συστήματα καταγραφής migrations
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
