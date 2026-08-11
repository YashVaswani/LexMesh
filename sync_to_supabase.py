"""
Sync GDPR Atomic Chunks to Supabase Cloud
Uploads all 64 GDPR atomic requirement JSON chunks from gdpr_requirements_master.json
directly into your Supabase Cloud `gdpr_requirements` table.
"""

import json
import os
from db.supabase_client import supabase_db
from config import config

def create_supabase_table_instructions():
    sql_schema = """
-- =======================================================
-- 1. Enable Vector Extension (Run in Supabase SQL Editor)
-- =======================================================
CREATE EXTENSION IF NOT EXISTS vector;

-- =======================================================
-- 2. Create `gdpr_requirements` Table for GDPR Chunks
-- =======================================================
CREATE TABLE IF NOT EXISTS public.gdpr_requirements (
    id TEXT PRIMARY KEY,
    chapter_number TEXT NOT NULL,
    chapter_title TEXT NOT NULL,
    article_number TEXT NOT NULL,
    article_title TEXT NOT NULL,
    atomic_requirement TEXT NOT NULL,
    embedding VECTOR(384),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- =======================================================
-- 3. Create `compliance_reports` Table for Audit Reports
-- =======================================================
CREATE TABLE IF NOT EXISTS public.compliance_reports (
    id TEXT PRIMARY KEY,
    company_name TEXT NOT NULL,
    policy_name TEXT NOT NULL,
    overall_score INT NOT NULL,
    report_data JSONB NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);
"""
    return sql_schema

def sync_chunks():
    print("=====================================================")
    print(" Supabase GDPR Chunks Sync Tool")
    print("=====================================================")

    if not config.SUPABASE_URL or "teams.live.com" in config.SUPABASE_URL or not config.SUPABASE_URL.startswith("https://"):
        print("[WARNING] Invalid SUPABASE_URL in your .env file!")
        print(f"Current URL: {config.SUPABASE_URL}")
        print("\n👉 Please update SUPABASE_URL in your .env file with your actual Supabase URL.")
        print("   Example: SUPABASE_URL=https://xyz.supabase.co\n")
        return

    json_path = "gdpr_requirements_master.json"
    if not os.path.exists(json_path):
        print(f"[ERROR] {json_path} not found. Run python -m ingestion.gdpr_parser first.")
        return

    with open(json_path, 'r', encoding='utf-8') as f:
        chunks = json.load(f)

    print(f"[INFO] Loaded {len(chunks)} GDPR requirement chunks from {json_path}.")
    print("[INFO] Uploading chunks to Supabase `gdpr_requirements` table...")

    success_count = 0
    for chunk in chunks:
        if supabase_db.store_gdpr_requirement(chunk):
            success_count += 1
            print(f"  ✓ Uploaded [{chunk.get('id')}] {chunk.get('article_number')}: {chunk.get('atomic_requirement')[:50]}...")
        else:
            print(f"  ✗ Failed to upload [{chunk.get('id')}]")

    print(f"\n[SUMMARY] Successfully uploaded {success_count}/{len(chunks)} GDPR chunks to Supabase Cloud!")

if __name__ == "__main__":
    sync_chunks()
