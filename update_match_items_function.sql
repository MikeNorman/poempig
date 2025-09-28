-- Update match_items function to use items table instead of poems table
-- This is needed after the schema migration from poems to items

CREATE OR REPLACE FUNCTION match_items(
    query_embedding vector(1536),
    match_threshold float DEFAULT 0.0,
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
        1 - (i.embedding_vector <=> query_embedding) as similarity
    FROM items i
    WHERE i.embedding_vector IS NOT NULL
    ORDER BY i.embedding_vector <=> query_embedding
    LIMIT match_count;
$$;

-- Also update the embedding conversion function
CREATE OR REPLACE FUNCTION update_embeddings_to_vector()
RETURNS void
LANGUAGE SQL
AS $$
    UPDATE items 
    SET embedding_vector = embedding::vector
    WHERE embedding IS NOT NULL 
    AND embedding_vector IS NULL;
$$;
