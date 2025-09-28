-- Migration: Simplify vibe profiles schema
-- This eliminates the need for a junction table by storing item IDs directly in vibe_profiles

-- Step 1: Add seed_item_ids column to vibe_profiles table
ALTER TABLE vibe_profiles 
ADD COLUMN seed_item_ids JSONB DEFAULT '[]'::jsonb;

-- Step 2: Add index for better performance on JSON queries
CREATE INDEX idx_vibe_profiles_seed_item_ids ON vibe_profiles USING GIN (seed_item_ids);

-- Step 3: Drop the junction table (no longer needed)
DROP TABLE IF EXISTS vibe_profile_items;

-- Step 4: Update any existing vibe profiles to have empty seed_item_ids
UPDATE vibe_profiles 
SET seed_item_ids = '[]'::jsonb 
WHERE seed_item_ids IS NULL;

-- Verification queries:
-- SELECT id, name, size, seed_item_ids FROM vibe_profiles LIMIT 5;
-- SELECT jsonb_array_length(seed_item_ids) as item_count FROM vibe_profiles;
