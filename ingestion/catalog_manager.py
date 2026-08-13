"""
Catalog Manager Registry (Multi-Framework Enterprise Compliance)
Provides metadata, taxonomy maps, and requirement loader for GDPR, HIPAA, RBI, and SOC 2.
"""

import os
import json

FRAMEWORKS = {
    "gdpr": {
        "id": "gdpr",
        "name": "EU GDPR",
        "full_name": "General Data Protection Regulation (EU) 2016/679",
        "icon": "🇪🇺",
        "catalog_file": "gdpr_requirements_master.json",
        "table_name": "gdpr_requirements",
        "penalty_type": "GDPR Statutory Fine Tiers (Art. 83)",
        "chapter_articles_map": {
            "I": ("General Provisions", "Art. 1–4"),
            "II": ("Principles", "Art. 5–11"),
            "III": ("Rights of Data Subject", "Art. 12–23"),
            "IV": ("Controller & Processor", "Art. 24–43"),
            "V": ("Third Country Transfers", "Art. 44–49"),
            "VI": ("Supervisory Authorities", "Art. 51–59"),
            "VII": ("Cooperation & Consistency", "Art. 60–76"),
            "VIII": ("Remedies & Penalties", "Art. 77–84"),
            "IX": ("Special Situations", "Art. 85–91"),
            "X": ("Delegated Acts", "Art. 92–93"),
            "XI": ("Final Provisions", "Art. 94–99")
        }
    },
    "hipaa": {
        "id": "hipaa",
        "name": "US HIPAA",
        "full_name": "Health Insurance Portability and Accountability Act",
        "icon": "🏥",
        "catalog_file": "hipaa_requirements_master.json",
        "table_name": "hipaa_requirements",
        "penalty_type": "HITECH / HIPAA Statutory Civil Monetary Penalties (CMP)",
        "chapter_articles_map": {
            "I": ("Security Rule — Administrative Safeguards", "§ 164.308"),
            "II": ("Security Rule — Physical & Technical Safeguards", "§ 164.310–312"),
            "III": ("Privacy Rule — PHI Standards", "§ 164.502–528"),
            "IV": ("Breach Notification Rule", "§ 164.400–414")
        }
    },
    "rbi": {
        "id": "rbi",
        "name": "RBI Cyber Framework",
        "full_name": "RBI Master Direction — Cyber Security Framework for Banks & Financial Entities",
        "icon": "🏦",
        "catalog_file": "rbi_requirements_master.json",
        "table_name": "rbi_requirements",
        "penalty_type": "Banking Regulation Act Statutory Penalties & Supervisory Enforcement",
        "chapter_articles_map": {
            "I": ("Cyber Governance & Incident Response Architecture", "Guidelines 2–3"),
            "II": ("Network Security, Encryption & SOC Monitoring", "Guidelines 4–6"),
            "III": ("Customer Protection & Digital Channel Security", "Guidelines 7–8"),
            "IV": ("Vendor & Third-Party Cyber Risk Management", "Guidelines 9–10")
        }
    },
    "soc2": {
        "id": "soc2",
        "name": "SOC 2 Type II",
        "full_name": "AICPA SOC 2 Type II — Trust Services Criteria",
        "icon": "🛡️",
        "catalog_file": "soc2_requirements_master.json",
        "table_name": "soc2_requirements",
        "penalty_type": "Audit Qualification Risk (Unqualified vs Qualified/Adverse Opinion)",
        "chapter_articles_map": {
            "CC": ("Common Criteria — Control Environment & Access", "CC1–CC8"),
            "A": ("Availability Criteria — DR & Capacity", "A1.1–A1.3"),
            "C": ("Confidentiality Criteria — Data Handling & Disposal", "C1.1–C1.2"),
            "P": ("Privacy Criteria — Notice & Consent Standards", "P1.1–P2.1")
        }
    }
}

class FrameworkCatalogManager:
    @staticmethod
    def get_framework_info(framework_id: str = "gdpr") -> dict:
        return FRAMEWORKS.get(framework_id.lower(), FRAMEWORKS["gdpr"])

    @staticmethod
    def load_catalog(framework_id: str = "gdpr") -> list:
        fw_info = FrameworkCatalogManager.get_framework_info(framework_id)
        file_path = fw_info["catalog_file"]
        if os.path.exists(file_path):
            try:
                with open(file_path, "r", encoding="utf-8") as f:
                    return json.load(f)
            except Exception as e:
                print(f"[ERROR] Failed to load catalog {file_path}: {e}")
        return []

catalog_manager = FrameworkCatalogManager()
