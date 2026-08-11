"""
Sync GDPR Atomic Chunks to Supabase Cloud
Uploads all 64 GDPR atomic requirement JSON chunks from gdpr_requirements_master.json
directly into your Supabase Cloud `gdpr_requirements` table.
"""

import json
import os
from db.supabase_client import supabase_db
from config import config

def get_supabase_sql_script():
    return """
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

-- =======================================================
-- 4. Enable Public Read/Write Access (Disable RLS for API)
-- =======================================================
ALTER TABLE public.gdpr_requirements DISABLE ROW LEVEL SECURITY;
ALTER TABLE public.compliance_reports DISABLE ROW LEVEL SECURITY;
"""

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
    print("[INFO] Uploading chunks to Supabase `gdpr_requirements` table...\n")

    success_count = 0
    rls_error_detected = False

    for chunk in chunks:
        res = supabase_db.store_gdpr_requirement(chunk)
        if res:
            success_count += 1
            print(f"  ✓ Uploaded [{chunk.get('id')}] {chunk.get('article_number')}: {chunk.get('atomic_requirement')[:50]}...")
        else:
            rls_error_detected = True

    print(f"\n[SUMMARY] Successfully uploaded {success_count}/{len(chunks)} GDPR chunks to Supabase Cloud!")

    if rls_error_detected and success_count == 0:
        print("\n" + "="*60)
        print(" 🚨 ROW-LEVEL SECURITY (RLS) ERROR DETECTED!")
        print("="*60)
        print("Supabase blocked the write because RLS is enabled on the table.")
        print("\n👉 SOLUTION: Open Supabase SQL Editor and run this SQL snippet:\n")
        print(get_supabase_sql_script())

if __name__ == "__main__":
    sync_chunks()
