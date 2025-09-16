-- Enable pgvector extension
CREATE EXTENSION IF NOT EXISTS vector;

-- Create a new column for vector embeddings (if it doesn't exist)
-- We'll convert the JSON embeddings to proper vector format
ALTER TABLE poems ADD COLUMN IF NOT EXISTS embedding_vector vector(1536);

-- Create an index for vector similarity search
CREATE INDEX IF NOT EXISTS poems_embedding_vector_idx ON poems USING ivfflat (embedding_vector vector_cosine_ops);

-- Create a function to find similar poems using vector similarity
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
        p.id,
        p.title,
        p.author,
        p.text,
        p.year,
        p.lang,
        p.lines_count,
        p.tags,
        p.embedding,
        p.created_at,
        p.text_tsv,
        p.tag,
        p.type,
        1 - (p.embedding_vector <=> query_embedding) as similarity
    FROM poems p
    WHERE p.embedding_vector IS NOT NULL
    ORDER BY p.embedding_vector <=> query_embedding
    LIMIT match_count;
$$;

-- Create a function to update embeddings from JSON to vector format
CREATE OR REPLACE FUNCTION update_embeddings_to_vector()
RETURNS void
LANGUAGE SQL
AS $$
    UPDATE poems 
    SET embedding_vector = embedding::vector
    WHERE embedding IS NOT NULL 
    AND embedding_vector IS NULL;
$$;
