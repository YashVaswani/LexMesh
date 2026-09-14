"""
Supabase Database Helper for LexMesh Multi-Framework Engine
Manages requirements with rich metadata payload, pgvector similarity search,
policy domain pre-filtering, and JSON report storage.
"""

import os
from supabase import create_client, Client
from config import config

class SupabaseManager:
    def __init__(self):
        # Fix httpx NO_PROXY IPv6 parsing bug on Windows
        for k in ["NO_PROXY", "no_proxy", "HTTP_PROXY", "http_proxy", "HTTPS_PROXY", "https_proxy", "ALL_PROXY", "all_proxy"]:
            if k in os.environ:
                os.environ[k] = os.environ[k].replace("::1,", "").replace(",::1", "").replace("::1", "")
                
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

    def store_requirement(self, req_data: dict, framework_id: str = "gdpr") -> bool:
        """
        Stores atomic requirements into Supabase Cloud tables with multi-table fallback.
        """
        if not self.is_connected():
            return False
        
        fw = framework_id.lower()
        full_payload = {
            "id": req_data.get("id"),
            "framework": fw,
            "policy_domain": req_data.get("policy_domain", "data_governance"),
            "chapter_number": req_data.get("chapter_number"),
            "chapter_title": req_data.get("chapter_title"),
            "article_number": req_data.get("article_number"),
            "article_title": req_data.get("article_title"),
            "atomic_requirement": req_data.get("atomic_requirement"),
            "embedding": req_data.get("embedding")
        }

        success = False
        # 1. Upsert into unified compliance_requirements table (All 296 requirements)
        try:
            self.client.table("compliance_requirements").upsert(full_payload).execute()
            success = True
        except Exception:
            pass

        # 2. Upsert into framework-specific table (gdpr_requirements, hipaa_requirements, rbi_requirements, soc2_requirements)
        fw_table = f"{fw}_requirements"
        try:
            self.client.table(fw_table).upsert(full_payload).execute()
            success = True
        except Exception:
            # Fallback legacy format if custom columns are missing in framework table
            legacy_payload = {
                "id": req_data.get("id"),
                "chapter_number": req_data.get("chapter_number"),
                "chapter_title": req_data.get("chapter_title"),
                "article_number": req_data.get("article_number"),
                "article_title": req_data.get("article_title"),
                "atomic_requirement": req_data.get("atomic_requirement"),
                "embedding": req_data.get("embedding")
            }
            try:
                self.client.table(fw_table).upsert(legacy_payload).execute()
                success = True
            except Exception:
                pass

        return success

    def store_gdpr_requirement(self, req_data: dict, framework_id: str = "gdpr") -> bool:
        return self.store_requirement(req_data, framework_id=framework_id)

    def get_requirements_by_chapter(self, chapter_number: str) -> list:
        if not self.is_connected():
            return []
        try:
            res = (
                self.client.table("compliance_requirements")
                .select("*")
                .eq("chapter_number", chapter_number)
                .execute()
            )
            return res.data or []
        except Exception:
            try:
                res = (
                    self.client.table("gdpr_requirements")
                    .select("*")
                    .eq("chapter_number", chapter_number)
                    .execute()
                )
                return res.data or []
            except Exception:
                return []

    def save_compliance_report(self, report_id: str, company_name: str, policy_name: str, overall_score: int, report_json: dict, user_id: str = None) -> bool:
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
            if user_id:
                payload["user_id"] = user_id
            res = self.client.table("compliance_reports").upsert(payload).execute()
            return True
        except Exception as e:
            print(f"[ERROR] Failed to save report {report_id}: {e}")
            return False

    def save_report(self, master_report: dict, user_id: str = None) -> bool:
        meta = master_report.get("metadata", {})
        summary = master_report.get("summary", {})
        return self.save_compliance_report(
            report_id=master_report.get("report_id", "rep_001"),
            company_name=meta.get("company_name", "Organization"),
            policy_name=meta.get("policy_name", "Policy"),
            overall_score=summary.get("overall_score", 0),
            report_json=master_report,
            user_id=user_id
        )

    def get_compliance_report(self, report_id: str, user_id: str = None) -> dict:
        if not self.is_connected():
            return {}
        try:
            query = self.client.table("compliance_reports").select("*").eq("id", report_id)
            if user_id:
                query = query.eq("user_id", user_id)
            res = query.execute()
            if res.data:
                return res.data[0].get("report_data", {})
            return {}
        except Exception as e:
            print(f"[ERROR] Failed to fetch report {report_id}: {e}")
            return {}

    def get_cached_verdict(self, framework_id: str, requirement_id: str, policy_hash: str) -> dict:
        """Fetches SHA-256 cached audit verdict from Supabase Cloud table."""
        if not self.is_connected():
            return None
        try:
            cache_id = f"{framework_id}:{requirement_id}:{policy_hash}"
            res = self.client.table("audit_verdict_cache").select("verdict_data").eq("id", cache_id).execute()
            if res.data and len(res.data) > 0:
                return res.data[0].get("verdict_data")
        except Exception:
            pass
        return None

    def save_cached_verdict(self, framework_id: str, requirement_id: str, policy_hash: str, verdict_data: dict) -> bool:
        """Stores SHA-256 audit verdict into Supabase Cloud table for zero-cost repeat audits."""
        if not self.is_connected():
            return False
        try:
            cache_id = f"{framework_id}:{requirement_id}:{policy_hash}"
            payload = {
                "id": cache_id,
                "framework": framework_id,
                "requirement_id": requirement_id,
                "policy_hash": policy_hash,
                "verdict_data": verdict_data
            }
            self.client.table("audit_verdict_cache").upsert(payload).execute()
            return True
        except Exception:
            return False

supabase_db = SupabaseManager()
