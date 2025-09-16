-- Migration script to restructure database for unified items approach
-- Based on actual current schema which already has 'type' column and 'semantic_tags'

-- 1. Rename poems table to items (this is the only change needed)
ALTER TABLE poems RENAME TO items;

-- 2. Create indexes for better performance (if they don't exist)
CREATE INDEX IF NOT EXISTS idx_items_type ON items(type);
CREATE INDEX IF NOT EXISTS idx_items_author ON items(author);
CREATE INDEX IF NOT EXISTS idx_items_semantic_tags ON items USING GIN (semantic_tags);
