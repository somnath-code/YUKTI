CREATE TABLE IF NOT EXISTS evidence_quarantine (
  tenant TEXT NOT NULL, urn TEXT NOT NULL, reason TEXT NOT NULL,
  detected_at TEXT NOT NULL, source_url TEXT NOT NULL,
  PRIMARY KEY (tenant,urn),
  FOREIGN KEY (tenant,urn) REFERENCES evidence(tenant,urn) ON DELETE CASCADE
);
