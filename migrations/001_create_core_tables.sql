-- projects
CREATE TABLE IF NOT EXISTS projects (
  id         VARCHAR(255) PRIMARY KEY,
  name       VARCHAR(255) NOT NULL,
  code       VARCHAR(255),
  state      VARCHAR(50)  DEFAULT 'active',
  created_at DATETIME      DEFAULT CURRENT_TIMESTAMP,
  updated_at DATETIME      DEFAULT CURRENT_TIMESTAMP
);

-- teams (λίστες ως JSON TEXT για SQLite)
CREATE TABLE IF NOT EXISTS teams (
  id             INTEGER PRIMARY KEY AUTOINCREMENT,
  project_id     VARCHAR(255) NOT NULL,
  name           VARCHAR(255) NOT NULL,
  role           VARCHAR(255) NOT NULL,
  members        TEXT         DEFAULT '[]', -- JSON array
  responsibilities TEXT       DEFAULT '[]', -- JSON array
  created_at     DATETIME     DEFAULT CURRENT_TIMESTAMP,
  updated_at     DATETIME     DEFAULT CURRENT_TIMESTAMP,
  FOREIGN KEY (project_id) REFERENCES projects(id)
);

-- systems (μοναδικότητα ανά project + όνομα)
CREATE TABLE IF NOT EXISTS systems (
  id            INTEGER PRIMARY KEY AUTOINCREMENT,
  project_id    VARCHAR(255) NOT NULL,
  name          VARCHAR(255) NOT NULL,
  description   TEXT,
  type          VARCHAR(50)  CHECK (system_type IN ('internal','external','integration')) DEFAULT 'internal',
  dependencies  TEXT         DEFAULT '[]', -- JSON array of names/ids
  created_at    DATETIME     DEFAULT CURRENT_TIMESTAMP,
  updated_at    DATETIME     DEFAULT CURRENT_TIMESTAMP,
  FOREIGN KEY (project_id) REFERENCES projects(id),
  UNIQUE(project_id, name)
);

-- adrs
CREATE TABLE IF NOT EXISTS adrs (
  id            INTEGER PRIMARY KEY AUTOINCREMENT,
  project_id    VARCHAR(255) NOT NULL,
  title         VARCHAR(255) NOT NULL,
  content       TEXT         NOT NULL,
  status        VARCHAR(50)  DEFAULT 'proposed',
  context       TEXT,
  decision      TEXT,
  consequences  TEXT,
  alternatives  TEXT,
  author        VARCHAR(255),
  tags          TEXT         DEFAULT '[]', -- JSON array
  created_at    DATETIME     DEFAULT CURRENT_TIMESTAMP,
  updated_at    DATETIME     DEFAULT CURRENT_TIMESTAMP,
  FOREIGN KEY (project_id) REFERENCES projects(id),
  UNIQUE(project_id, title)
);




-- βοηθητικά indexes
CREATE INDEX IF NOT EXISTS idx_teams_project ON teams(project_id);
CREATE INDEX IF NOT EXISTS idx_systems_project ON systems(project_id);
CREATE INDEX IF NOT EXISTS idx_adrs_project   ON adrs(project_id);
CREATE INDEX IF NOT EXISTS idx_adrs_status    ON adrs(status);
