-- Migration script to convert semantic_tags from TEXT[] to JSONB
-- This allows us to store structured tags with relevance scores

-- First, let's see what we have
SELECT column_name, data_type 
FROM information_schema.columns 
WHERE table_name = 'items' AND column_name = 'semantic_tags';

-- Add a new column for structured tags
ALTER TABLE items ADD COLUMN semantic_tags_structured JSONB;

-- Create an index on the new JSONB column for efficient searching
CREATE INDEX idx_items_semantic_tags_structured ON items USING GIN (semantic_tags_structured);

-- Note: We'll populate the new column with the retagging script
-- The old semantic_tags column will remain for now as a backup
