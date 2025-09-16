-- Migration script to restructure database for unified items approach

-- 1. Rename poems table to items
ALTER TABLE poems RENAME TO items;

-- 2. Rename kind column to type for clarity
ALTER TABLE items RENAME COLUMN kind TO type;

-- 3. Add semantic_tags column for semantic search
ALTER TABLE items ADD COLUMN IF NOT EXISTS semantic_tags TEXT[];

-- 4. Create indexes for better performance
CREATE INDEX IF NOT EXISTS idx_items_type ON items(type);
CREATE INDEX IF NOT EXISTS idx_items_author ON items(author);
CREATE INDEX IF NOT EXISTS idx_items_semantic_tags ON items USING GIN (semantic_tags);

-- 5. Update any existing constraints to use new column name
-- (This might need to be done manually if there are existing constraints)
