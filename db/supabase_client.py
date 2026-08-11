"""
Supabase Database Helper for ComplianceIQ
Manages requirements, vector similarity search via pgvector, and JSON report storage.
"""

import os
from supabase import create_client, Client
from config import config

class SupabaseManager:
    def __init__(self):
        self.url = config.SUPABASE_URL
        self.key = config.SUPABASE_KEY
        self.client: Client = None
        if self.url and self.key:
            try:
                self.client = create_client(self.url, self.key)
                print("[INFO] Supabase client initialized successfully.")
            except Exception as e:
                print(f"[ERROR] Failed to initialize Supabase client: {e}")

    def is_connected(self) -> bool:
        return self.client is not None

    def store_gdpr_requirement(self, req_data: dict) -> bool:
        """
        Stores an atomic GDPR requirement JSON into the `gdpr_requirements` table.
        """
        if not self.is_connected():
            return False
        try:
            res = self.client.table("gdpr_requirements").upsert(req_data).execute()
            return True
        except Exception as e:
            print(f"[ERROR] Failed to store requirement {req_data.get('id')}: {e}")
            return False

    def get_requirements_by_chapter(self, chapter: str) -> list:
        """
        Fetches atomic GDPR requirements for a specific chapter (e.g. 'III').
        """
        if not self.is_connected():
            return []
        try:
            res = self.client.table("gdpr_requirements").select("*").eq("chapter_number", chapter).execute()
            return res.data or []
        except Exception as e:
            print(f"[ERROR] Failed to fetch requirements for Chapter {chapter}: {e}")
            return []

    def save_compliance_report(self, report_id: str, company_name: str, policy_name: str, overall_score: int, report_json: dict) -> bool:
        """
        Saves a complete Gap Analysis Report JSON into `compliance_reports`.
        """
        if not self.is_connected():
            return False
        try:
            payload = {
                "id": report_id,
                "company_name": company_name,
                "policy_name": policy_name,
                "overall_score": overall_score,
                "report_data": report_json
            }
            res = self.client.table("compliance_reports").upsert(payload).execute()
            return True
        except Exception as e:
            print(f"[ERROR] Failed to save report {report_id}: {e}")
            return False

    def get_compliance_report(self, report_id: str) -> dict:
        """
        Retrieves a saved Gap Analysis Report JSON by ID.
        """
        if not self.is_connected():
            return {}
        try:
            res = self.client.table("compliance_reports").select("*").eq("id", report_id).execute()
            if res.data:
                return res.data[0].get("report_data", {})
            return {}
        except Exception as e:
            print(f"[ERROR] Failed to fetch report {report_id}: {e}")
            return {}

supabase_db = SupabaseManager()
