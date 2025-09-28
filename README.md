# Poem Recommender

A Flask-based web application that recommends poems based on similarity using OpenAI embeddings and Supabase database.

## Project Structure

```
poem_recommender/
├── src/                          # Core application modules
│   ├── __init__.py
│   ├── poem_analyzer.py          # Poem analysis logic
│   └── recommendation_engine.py  # Recommendation algorithm
├── scripts/                      # Data processing scripts
│   ├── segment_unstructured.py   # Extract poems from documents
│   ├── ingest_poems.py          # Main ingestion script
│   ├── ingest_jsonl_loader.py   # JSONL ingestion
│   ├── ingest_complete.py       # Complete ingestion with embeddings
│   ├── ingest_proper.py         # Schema-compliant ingestion
│   ├── ingest_simple.py         # Simple ingestion
│   └── simple_ingest.py         # Minimal ingestion
├── utils/                        # Utility scripts
│   ├── check_schema.py          # Database schema checker
│   ├── check_tag_column.py      # Tag column verification
│   ├── check_type_column.py     # Type column verification
│   ├── add_tag_column.py        # Add tag column to database
│   ├── create_proper_schema.py  # Create proper database schema
│   ├── recreate_table.py        # Recreate database table
│   └── setup_database.py        # Database setup
├── data/                         # Data files
│   └── segments.jsonl           # Sample poem data
├── templates/                    # Flask templates
│   └── index.html               # Main web interface
├── static/                       # Static web assets
├── app.py                       # Main Flask application
├── requirements.txt             # Python dependencies
├── .env                         # Environment variables (not in git)
└── README.md                    # This file
```

## Setup

1. **Install dependencies:**
   ```bash
   python3 -m venv .venv
   source .venv/bin/activate  # Windows: .venv\Scripts\activate
   pip install -r requirements.txt
   ```

2. **Configure environment:**
   Create a `.env` file with:
   ```
   SUPABASE_URL=your_supabase_url
   SUPABASE_SERVICE_ROLE_KEY=your_service_role_key
   OPENAI_API_KEY=your_openai_api_key
   EMBEDDING_MODEL=text-embedding-3-small
   ```

3. **Set up database:**
   - Create a Supabase project
   - Run the SQL commands from `utils/setup_database.py` to create the poems table
   - The table should have columns: `id`, `title`, `author`, `text`, `tag`

## Usage

### Quick Start

```bash
# Start the app with full functionality
./run_backend.sh
```

This will:
- ✅ Automatically handle virtual environment
- ✅ Install all dependencies (including ML packages)
- ✅ Start with full recommendation engine functionality
- ✅ All features available

**Alternative Manual Setup:**
```bash
# Activate virtual environment
source venv/bin/activate

# Install dependencies (if not already installed)
pip install -r requirements.txt

# Start the app
python app.py
```

**Health Check:** Visit `http://localhost:5001/health` to verify all features are working.

Then visit `http://localhost:5001` in your browser.

### Processing Documents
```bash
# Extract poems from a document
python scripts/segment_unstructured.py --input "your_document.docx" --out "poems.jsonl"

# Ingest poems into database
python scripts/ingest_complete.py --input data/segments.jsonl --source "Document Name"
```

## Database Schema

The `poems` table contains:
- `id`: UUID primary key
- `title`: Poem title (auto-generated from first line if not provided)
- `author`: Author name
- `text`: Full poem text
- `tag`: Comma-separated tags (type, themes, author, etc.)
- `embedding`: OpenAI embedding vector for similarity search
- `created_at`: Timestamp
- `updated_at`: Timestamp

## Features

- **Document Processing**: Extract poems from .docx and .txt files
- **Smart Classification**: Automatically classify text as poem or quote
- **Tag Generation**: Generate relevant tags based on content analysis
- **Embedding Generation**: Create OpenAI embeddings for similarity search
- **Web Interface**: Simple Flask-based UI for poem recommendations
- **Database Storage**: Supabase for scalable data storage

## Troubleshooting

### Common Issues

**"Recommendation engine not available"**
- The app automatically tries to load all ML features
- If dependencies are missing, some features will be disabled
- Check `http://localhost:5001/health` to see which features are available

**Dependency installation fails**
- The app gracefully handles missing ML dependencies
- Basic web interface will work even if ML packages fail to install
- Check `http://localhost:5001/health` to see available features

**Port 5001 already in use**
```bash
# Kill any existing processes
lsof -ti:5001 | xargs kill -9 2>/dev/null || true
```

**Python 3.13 compatibility issues**
- All dependencies are now compatible with Python 3.13
- The app will automatically use full functionality when dependencies are available

## Development

- Core logic is in `src/` directory
- Data processing scripts are in `scripts/` directory
- Utility functions are in `utils/` directory
- Web interface uses Flask with HTML templates
