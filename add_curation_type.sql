-- Add curation_type column to items table
-- This allows filtering by curation status independent of source

-- Step 1: Add curation_type column with default value
ALTER TABLE items ADD COLUMN curation_type text DEFAULT 'scraped';

-- Step 2: Add check constraint to ensure valid values
ALTER TABLE items ADD CONSTRAINT check_curation_type 
CHECK (curation_type IN ('scraped', 'user_curated', 'auto_curated'));

-- Step 3: Create index for efficient filtering
CREATE INDEX idx_items_curation_type ON items (curation_type);

-- Step 4: Update existing items based on source patterns
-- Mark items from allpoetry.com as scraped (they already are by default)
UPDATE items 
SET curation_type = 'scraped' 
WHERE source LIKE '%allpoetry.com%';

-- Mark items with other sources as user_curated (your original imports)
UPDATE items 
SET curation_type = 'user_curated' 
WHERE source IS NOT NULL 
AND source != '' 
AND source NOT LIKE '%allpoetry.com%';

-- Mark items with no source as user_curated (likely your original imports)
UPDATE items 
SET curation_type = 'user_curated' 
WHERE source IS NULL OR source = '';

-- Step 5: Verify the migration
SELECT 
    curation_type,
    COUNT(*) as count,
    ROUND(COUNT(*) * 100.0 / (SELECT COUNT(*) FROM items), 2) as percentage
FROM items 
GROUP BY curation_type 
ORDER BY count DESC;
