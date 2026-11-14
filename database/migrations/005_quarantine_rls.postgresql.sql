ALTER TABLE evidence_quarantine ENABLE ROW LEVEL SECURITY;
ALTER TABLE evidence_quarantine FORCE ROW LEVEL SECURITY;
CREATE POLICY tenant_boundary ON evidence_quarantine
  USING (tenant = current_setting('app.tenant_id', true))
  WITH CHECK (tenant = current_setting('app.tenant_id', true));
