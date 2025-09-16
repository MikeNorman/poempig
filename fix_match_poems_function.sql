-- Fix the match_poems function to use the items table instead of poems table
-- First, drop the old function
DROP FUNCTION IF EXISTS match_poems(vector(1536), float, int);

-- Create a new function that works with the items table
CREATE OR REPLACE FUNCTION match_poems(
    q text,  -- Changed from query_embedding vector(1536) to q text to match the current usage
    match_count int DEFAULT 5
)
RETURNS TABLE (
    id text,
    title text,
    author text,
    text text,
    year int,
    lang text,
    lines_count int,
    tags text,
    embedding text,
    created_at timestamptz,
    text_tsv text,
    tag text,
    type text,
    similarity float
)
LANGUAGE SQL
AS $$
    SELECT 
        i.id,
        i.title,
        i.author,
        i.text,
        i.year,
        i.lang,
        i.lines_count,
        i.tags,
        i.embedding,
        i.created_at,
        i.text_tsv,
        i.tag,
        i.type,
        1 - (i.embedding_vector <=> q::vector) as similarity
    FROM items i
    WHERE i.embedding_vector IS NOT NULL
    ORDER BY i.embedding_vector <=> q::vector
    LIMIT match_count;
$$;