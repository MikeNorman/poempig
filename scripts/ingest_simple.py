"""
Simple ingestion script that works with current table structure
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

        # Create embedding
        try:
            embedding = embed(text)
        except Exception as e:
            print(f"Error creating embedding: {e}")
            continue

        # Row structure matching current table schema
        row={
            "type": type_val,
            "author": author,
            "text": text,
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
