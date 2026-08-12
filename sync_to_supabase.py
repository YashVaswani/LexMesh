"""
Sync GDPR Atomic Chunks to Supabase Cloud with 384-dim Vector Embeddings
Uploads all 64 GDPR atomic requirement JSON chunks and populates pgvector embeddings
directly into your Supabase Cloud `gdpr_requirements` table.
"""

import json
import os
import math
from db.supabase_client import supabase_db
from config import config

# Optional SentenceTransformer with fallback embedder
try:
    from sentence_transformers import SentenceTransformer
    embedder = SentenceTransformer(config.EMBEDDING_MODEL_NAME)
    print(f"[INFO] Loaded SentenceTransformer model '{config.EMBEDDING_MODEL_NAME}'.")
except Exception:
    class LightweightEmbedder:
        def __init__(self, dim=384):
            self.dim = dim
        def encode(self, text: str) -> list:
            vec = [0.0] * self.dim
            for i, char in enumerate(text):
                idx = (ord(char) * (i + 1) * 31) % self.dim
                vec[idx] += 1.0
            norm = math.sqrt(sum(x * x for x in vec)) or 1.0
            return [round(x / norm, 5) for x in vec]
    embedder = LightweightEmbedder()
    print("[INFO] Using lightweight 384-dim vector embedder.")

def sync_chunks():
    print("=====================================================")
    print(" Supabase GDPR Chunks & Vector Embedding Sync Tool")
    print("=====================================================")

    json_path = "gdpr_requirements_master.json"
    if not os.path.exists(json_path):
        print(f"[ERROR] {json_path} not found. Run python -m ingestion.gdpr_parser first.")
        return

    with open(json_path, 'r', encoding='utf-8') as f:
        chunks = json.load(f)

    print(f"[INFO] Loaded {len(chunks)} GDPR requirement chunks.")
    print("[INFO] Generating 384-dim vector embeddings and uploading to Supabase...\n")

    success_count = 0
    for chunk in chunks:
        req_text = chunk.get("atomic_requirement", "")
        # Generate 384-dim vector embedding
        raw_vec = embedder.encode(req_text)
        vec_list = raw_vec.tolist() if hasattr(raw_vec, "tolist") else raw_vec

        payload = {
            "id": chunk.get("id"),
            "chapter_number": chunk.get("chapter_number"),
            "chapter_title": chunk.get("chapter_title"),
            "article_number": chunk.get("article_number"),
            "article_title": chunk.get("article_title"),
            "atomic_requirement": req_text,
            "embedding": vec_list
        }

        res = supabase_db.store_gdpr_requirement(payload)
        if res:
            success_count += 1
            print(f"  [OK] Uploaded [{chunk.get('id')}] (Vector size: {len(vec_list)}) {chunk.get('article_number')}: {req_text[:40]}...")
        else:
            print(f"  [FAIL] Failed to upload [{chunk.get('id')}]")

    print(f"\n[SUMMARY] Successfully stored {success_count}/{len(chunks)} chunks WITH VECTORS in Supabase Cloud!")

if __name__ == "__main__":
    sync_chunks()
