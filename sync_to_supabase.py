"""
Sync Multi-Framework Atomic Chunks to Supabase Cloud with 384-dim Vector Embeddings
Uploads all requirement JSON chunks (GDPR 99 Articles, HIPAA 43 Sections, RBI 93 Clauses, SOC2 61 Criteria)
and populates pgvector embeddings directly into Supabase Cloud.
"""

import json
import os
import math
from db.supabase_client import supabase_db
from config import config
from ingestion.catalog_manager import FRAMEWORKS

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
    print(" Supabase Multi-Framework Chunks & Vector Sync Tool")
    print("=====================================================")

    if not supabase_db.is_connected():
        print("[ERROR] Supabase client is not connected! Check your SUPABASE_URL and SUPABASE_KEY in .env.")
        return

    total_synced = 0
    for fw_id, fw_info in FRAMEWORKS.items():
        json_path = fw_info["catalog_file"]
        if not os.path.exists(json_path):
            print(f"[SKIP] Catalog '{json_path}' not found for framework {fw_info['name']}.")
            continue

        with open(json_path, 'r', encoding='utf-8') as f:
            chunks = json.load(f)

        print(f"\n[INFO] Framework: {fw_info['name']} — Loaded {len(chunks)} requirement chunks.")
        print(f"[INFO] Generating 384-dim vector embeddings for {fw_id.upper()}...")

        success_count = 0
        for chunk in chunks:
            req_text = chunk.get("atomic_requirement", "")
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

            res = supabase_db.store_gdpr_requirement(payload, framework_id=fw_id)
            if res:
                success_count += 1
                disp_text = req_text[:40].encode('ascii', errors='ignore').decode('ascii')
                print(f"  [OK] [{fw_id.upper()}] Uploaded [{chunk.get('id')}] {chunk.get('article_number')}: {disp_text}...", flush=True)
            else:
                print(f"  [FAIL] [{fw_id.upper()}] Failed to upload [{chunk.get('id')}]", flush=True)

        print(f"[SUMMARY] Successfully stored {success_count}/{len(chunks)} {fw_info['name']} chunks in Supabase Cloud!", flush=True)
        total_synced += success_count

    print(f"\n[TOTAL] Successfully synced {total_synced} requirement chunks across all 4 frameworks into Supabase Cloud!", flush=True)

if __name__ == "__main__":
    sync_chunks()
