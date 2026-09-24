"""
Debug script — run this from your backend folder to see:
1. Exactly which sections got parsed from college_knowledge.txt
2. What the top matches are for a test question
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from app.rag import (
    parse_sections,
    load_college_knowledge,
    collection,
    model,
)

DATA_DIR = Path(__file__).resolve().parent / "data"
text = (DATA_DIR / "college_knowledge.txt").read_text(encoding="utf-8")

print("=" * 60)
print("PARSED SECTIONS")
print("=" * 60)
sections = parse_sections(text)
for i, (title, content) in enumerate(sections):
    print(f"[{i}] TITLE: {title!r}")
    print(f"     CONTENT (first 80 chars): {content[:80]!r}")
    print()

print("=" * 60)
print("REBUILDING INDEX")
print("=" * 60)
load_college_knowledge()

print("=" * 60)
print("TEST QUERY: 'what are the facilities are available'")
print("=" * 60)
q = "what are the facilities are available"
emb = model().encode(q).tolist()
result = collection.query(query_embeddings=[emb], n_results=5)

docs = result["documents"][0]
metas = result["metadatas"][0]
dists = result["distances"][0]

for doc, meta, dist in zip(docs, metas, dists):
    print(f"SECTION: {meta.get('section')!r}  DISTANCE: {dist:.4f}")
    print(f"  -> {doc[:100]!r}")
    print()
    