CREATE TABLE IF NOT EXISTS articles (
  tenant TEXT NOT NULL, id TEXT NOT NULL, source_url TEXT NOT NULL, payload TEXT NOT NULL,
  revision INTEGER NOT NULL DEFAULT 1, state TEXT NOT NULL DEFAULT 'draft'
    CHECK (state IN ('draft','reviewed')),
  reviewed_by TEXT, review TEXT,
  PRIMARY KEY (tenant,id), UNIQUE (tenant,source_url)
);
CREATE TABLE IF NOT EXISTS issues (
  tenant TEXT NOT NULL, id TEXT NOT NULL, title TEXT NOT NULL, edition_date TEXT NOT NULL,
  state TEXT NOT NULL CHECK (state IN ('draft','approved','released')),
  checksum TEXT NOT NULL, page_count INTEGER NOT NULL, snapshot TEXT NOT NULL,
  created_by TEXT NOT NULL, approved_by TEXT, released_by TEXT,
  PRIMARY KEY (tenant,id)
);
CREATE TABLE IF NOT EXISTS evidence (
  tenant TEXT NOT NULL, urn TEXT NOT NULL, source_url TEXT NOT NULL,
  checksum TEXT NOT NULL, metadata TEXT NOT NULL, collected_at TEXT NOT NULL,
  PRIMARY KEY (tenant,urn)
);
CREATE TABLE IF NOT EXISTS audit_log (
  tenant TEXT NOT NULL, id TEXT NOT NULL, actor TEXT NOT NULL, action TEXT NOT NULL,
  entity TEXT NOT NULL, details TEXT NOT NULL, occurred_at TEXT NOT NULL,
  PRIMARY KEY (tenant,id)
);
CREATE TABLE IF NOT EXISTS vectors (
  tenant TEXT NOT NULL, article_id TEXT NOT NULL, revision INTEGER NOT NULL, model TEXT NOT NULL,
  dimensions INTEGER NOT NULL, values_json TEXT NOT NULL,
  PRIMARY KEY (tenant,article_id,model),
  FOREIGN KEY (tenant,article_id) REFERENCES articles(tenant,id) ON DELETE CASCADE
);
CREATE TABLE IF NOT EXISTS outbox (
  tenant TEXT NOT NULL, id TEXT NOT NULL, kind TEXT NOT NULL, payload TEXT NOT NULL,
  created_at TEXT NOT NULL, PRIMARY KEY(tenant,id)
);
CREATE INDEX IF NOT EXISTS issue_state_idx ON issues(tenant,state,edition_date);
CREATE INDEX IF NOT EXISTS audit_time_idx ON audit_log(tenant,occurred_at);
CREATE INDEX IF NOT EXISTS article_state_idx ON articles(tenant,state,id);
