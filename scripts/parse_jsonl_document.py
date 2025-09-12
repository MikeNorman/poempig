#!/usr/bin/env python3
"""
Parse JSONL content from a .docx document
"""

import os, json, argparse
try:
    from docx import Document
except:
    Document = None

def read_text(path: str) -> str:
    ext = os.path.splitext(path)[1].lower()
    if ext == ".docx":
        if Document is None: 
            raise SystemExit("pip install python-docx")
        d = Document(path)
        return "\n".join(p.text for p in d.paragraphs)
    elif ext == ".txt":
        return open(path, "r", encoding="utf-8", errors="ignore").read()
    else:
        raise SystemExit("Use .docx or .txt")

def parse_jsonl_content(text: str):
    """Parse JSONL content from text"""
    items = []
    lines = text.split('\n')
    
    for line in lines:
        line = line.strip()
        if not line:
            continue
            
        try:
            # Try to parse as JSON
            item = json.loads(line)
            items.append(item)
        except json.JSONDecodeError:
            # If it's not valid JSON, skip this line
            continue
    
    return items

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--input", required=True)
    ap.add_argument("--out", required=True)
    args = ap.parse_args()

    # Read the document
    raw_text = read_text(args.input)
    
    # Parse JSONL content
    items = parse_jsonl_content(raw_text)
    
    # Write to output file
    with open(args.out, "w", encoding="utf-8") as w:
        for item in items:
            w.write(json.dumps(item, ensure_ascii=False) + "\n")
    
    print(f"Parsed {len(items)} JSONL items → {args.out}")

if __name__ == "__main__":
    main()
