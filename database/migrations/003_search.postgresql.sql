CREATE INDEX IF NOT EXISTS articles_fulltext_idx ON articles USING gin (
  to_tsvector('english', ((payload::jsonb)->>'title') || ' ' ||
  ((payload::jsonb)->>'summary') || ' ' || (((payload::jsonb)->'source')->>'venue'))
) WHERE state='reviewed';
