DO $migration$
DECLARE table_name text;
BEGIN
  FOREACH table_name IN ARRAY ARRAY['articles', 'issues', 'evidence', 'audit_log', 'vectors', 'outbox']
  LOOP
    EXECUTE format('ALTER TABLE %I ENABLE ROW LEVEL SECURITY', table_name);
    EXECUTE format('ALTER TABLE %I FORCE ROW LEVEL SECURITY', table_name);
    IF NOT EXISTS (SELECT FROM pg_policies WHERE schemaname=current_schema()
                  AND tablename=table_name AND policyname='tenant_boundary') THEN
      EXECUTE format($p$CREATE POLICY tenant_boundary ON %I
          USING (tenant = current_setting('app.tenant_id', true))
          WITH CHECK (tenant = current_setting('app.tenant_id', true))$p$, table_name);
    END IF;
  END LOOP;
END
$migration$;
