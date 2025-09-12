# segment_unstructured.py
import os, re, json, argparse
try:
    from docx import Document
except:
    Document = None

def read_text(path:str)->str:
    ext = os.path.splitext(path)[1].lower()
    if ext==".docx":
        if Document is None: raise SystemExit("pip install python-docx")
        d = Document(path); return "\n".join(p.text for p in d.paragraphs)
    elif ext==".txt":
        return open(path,"r",encoding="utf-8",errors="ignore").read()
    else:
        raise SystemExit("Use .docx or .txt")

def normalize(s:str)->str:
    s=s.replace("\r\n","\n").replace("\r","\n")
    s=re.sub(r"\n{3,}","\n\n",s)
    return s

def blocks(lines):
    cur=[]; out=[]
    def push():
        if cur and any(x.strip() for x in cur): out.append(cur[:])
        cur.clear()
    prev_blank=True
    for ln in lines:
        blank = (ln.strip()=="")
        if blank and not prev_blank: push()
        else: cur.append(ln.rstrip())
        prev_blank=blank
    push()
    return out

def classify(text:str)->str:
    L=[ln for ln in text.splitlines() if ln.strip()]
    if not L: return "poem"
    short=sum(1 for ln in L if len(ln)<=60)
    return "poem" if (len(L)>=3 and short/len(L)>=0.6) else "quote"

def main():
    ap=argparse.ArgumentParser()
    ap.add_argument("--input",required=True)
    ap.add_argument("--out",required=True)
    args=ap.parse_args()

    raw=normalize(read_text(args.input))
    out=[]
    for blk in blocks(raw.split("\n")):
        body="\n".join([x for x in blk if x.strip()]).strip()
        if len(body.split())<4: continue
        out.append({"type": classify(body), "author": None, "title": None, "text": body})
    with open(args.out,"w",encoding="utf-8") as w:
        for it in out: w.write(json.dumps(it,ensure_ascii=False)+"\n")
    print(f"Wrote {len(out)} items → {args.out}")

if __name__=="__main__":
    main()
