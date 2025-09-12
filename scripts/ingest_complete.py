"""
Complete ingestion script that works with the full schema including tag field
"""

import os, json, argparse, hashlib, re, backoff
from dotenv import load_dotenv
from supabase import create_client, Client
from openai import OpenAI
from tqdm import tqdm
from langdetect import detect

load_dotenv()
SUPABASE_URL=os.getenv("SUPABASE_URL")
SUPABASE_SERVICE_ROLE_KEY=os.getenv("SUPABASE_SERVICE_ROLE_KEY")
OPENAI_API_KEY=os.getenv("OPENAI_API_KEY")
EMBEDDING_MODEL=os.getenv("EMBEDDING_MODEL","text-embedding-3-small")
if not (SUPABASE_URL and SUPABASE_SERVICE_ROLE_KEY and OPENAI_API_KEY):
    raise SystemExit("Missing env vars")

sb:Client=create_client(SUPABASE_URL,SUPABASE_SERVICE_ROLE_KEY)
oa=OpenAI(api_key=OPENAI_API_KEY)

def norm(t:str)->str:
    t=t.strip()
    t=re.sub(r"\n{3,}","\n\n",t)
    return t

def generate_tags(text, type_val, author):
    """Generate tags based on content analysis"""
    tags = [type_val]
    
    text_lower = text.lower()
    
    # Theme-based tags
    if any(word in text_lower for word in ['love', 'heart', 'kiss', 'beloved', 'romance']):
        tags.append('love')
    if any(word in text_lower for word in ['death', 'die', 'grave', 'tomb', 'eternal', 'soul']):
        tags.append('death')
    if any(word in text_lower for word in ['nature', 'tree', 'flower', 'sky', 'mountain', 'river', 'ocean', 'wind', 'rain']):
        tags.append('nature')
    if any(word in text_lower for word in ['dream', 'dreams', 'sleep', 'night']):
        tags.append('dreams')
    if any(word in text_lower for word in ['time', 'moment', 'hour', 'day', 'night', 'year', 'past', 'future']):
        tags.append('time')
    if any(word in text_lower for word in ['sad', 'tear', 'cry', 'pain', 'sorrow', 'grief', 'lonely', 'empty', 'dark']):
        tags.append('melancholy')
    if any(word in text_lower for word in ['happy', 'joy', 'smile', 'laugh', 'bright', 'light', 'cheer', 'celebrate']):
        tags.append('joy')
    
    # Author-based tags
    if author:
        author_lower = author.lower()
        if 'frost' in author_lower:
            tags.append('robert-frost')
        elif 'dickinson' in author_lower:
            tags.append('emily-dickinson')
        elif 'wordsworth' in author_lower:
            tags.append('william-wordsworth')
        elif 'angelou' in author_lower:
            tags.append('maya-angelou')
        elif 'hughes' in author_lower:
            tags.append('langston-hughes')
    
    return ','.join(tags)

@backoff.on_exception(backoff.expo, Exception, max_time=60)
def embed(t:str):
    return oa.embeddings.create(model=EMBEDDING_MODEL, input=t).data[0].embedding

def main():
    ap=argparse.ArgumentParser()
    ap.add_argument("--input",required=True)
    ap.add_argument("--source",default="JSon poems.docx")
    ap.add_argument("--prefer_trailing_author",action="store_true",
                    help="If author is null/Unknown and text ends with -- Name, move Name to author.")
    args=ap.parse_args()

    with open(args.input,"r",encoding="utf-8") as f:
        lines=[ln for ln in f if ln.strip()]

    for ln in tqdm(lines, desc="Ingest"):
        obj=json.loads(ln)
        type_val=(obj.get("type") or "poem").lower()
        if type_val not in ("poem","quote"): type_val="poem"
        text=norm(obj.get("text",""))
        if not text: continue

        author=(obj.get("author") or None)
        if args.prefer_trailing_author and (not author or str(author).lower()=="unknown"):
            # pull trailing -- Name
            m=re.search(r"(?:^|\n)\s*[—–-]{1,2}\s*([A-Za-z\.\-'' ]+)(?:,.*)?\s*$", text)
            if m:
                author=m.group(1).strip()
                text=re.sub(r"(?:^|\n)\s*[—–-]{1,2}\s*([A-Za-z\.\-'' ]+)(?:,.*)?\s*$","",text).strip()

        # Generate tags
        tags = generate_tags(text, type_val, author)
        
        # Create title from first line of text
        lines = text.split('\n')
        title = lines[0][:100] + "..." if len(lines[0]) > 100 else lines[0] if lines[0] else f"{type_val.title()}"

        # Detect language
        try:
            lang = detect(text)
        except Exception:
            lang = "en"

        # Count lines
        lines_count = len([line for line in text.splitlines() if line.strip()])

        # Create embedding
        try:
            embedding = embed(text)
        except Exception as e:
            print(f"Error creating embedding: {e}")
            continue

        # Row structure matching the complete schema
        row={
            "title": title,
            "author": author,
            "text": text,
            "tag": tags,
            "lang": lang,
            "lines_count": lines_count,
            "embedding": embedding
        }
        
        try:
            sb.table("poems").insert(row).execute()
        except Exception as e:
            print(f"Error inserting poem: {e}")
            continue

    print("Done.")

if __name__=="__main__":
    main()
