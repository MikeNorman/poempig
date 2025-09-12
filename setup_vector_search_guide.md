# Supabase Vector Similarity Search Setup

## Step 1: Enable pgvector Extension

Go to your Supabase dashboard → SQL Editor and run:

```sql
-- Enable pgvector extension
CREATE EXTENSION IF NOT EXISTS vector;
```

## Step 2: Add Vector Column

```sql
-- Add a vector column to store embeddings in proper vector format
ALTER TABLE poems ADD COLUMN IF NOT EXISTS embedding_vector vector(1536);
```

## Step 3: Convert Existing Embeddings

```sql
-- Convert JSON embeddings to vector format
UPDATE poems 
SET embedding_vector = embedding::vector
WHERE embedding IS NOT NULL 
AND embedding_vector IS NULL;
```

## Step 4: Create Vector Index

```sql
-- Create HNSW index for fast vector similarity search
CREATE INDEX IF NOT EXISTS poems_embedding_vector_hnsw_idx 
ON poems USING hnsw (embedding_vector vector_cosine_ops)
WITH (m = 16, ef_construction = 64);
```

## Step 5: Create Similarity Search Function

```sql
-- Create function for vector similarity search
CREATE OR REPLACE FUNCTION match_poems(
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
```

## Step 6: Test the Setup

```sql
-- Test the vector search function
SELECT * FROM match_poems(
    (SELECT embedding_vector FROM poems LIMIT 1),
    0.0,
    5
);
```

## Expected Performance
- **Before**: 3+ seconds (processing 1000+ poems)
- **After**: <100ms (using vector index)
