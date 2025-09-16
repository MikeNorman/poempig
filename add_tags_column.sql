-- Add tags column to poems table for semantic search
ALTER TABLE poems ADD COLUMN IF NOT EXISTS semantic_tags TEXT[];

-- Create index for faster tag searches
CREATE INDEX IF NOT EXISTS idx_poems_semantic_tags ON poems USING GIN (semantic_tags);
