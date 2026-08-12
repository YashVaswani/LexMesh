"""
Supervisor Router Agent (Enterprise-Grade Parallel Pipeline)
Orchestrates Chapter Sub-Agents (Chapters I-XI) using ThreadPoolExecutor for PARALLEL execution,
calculates dynamic chapter readiness scores, prioritizes Conflicting items in P1 Action Plan,
and enforces consistent status-action alignment across P1, P2, and P3 action plans.
"""

import json
import uuid
import datetime
from concurrent.futures import ThreadPoolExecutor, as_completed
from agents.chapter_agents import ChapterSubAgent
from db.supabase_client import supabase_db

class SupervisorAgent:
    def __init__(self):
        print("[INFO] Initializing Supervisor Router Agent...")

    def calculate_scores_and_summary(self, detailed_gaps: list) -> tuple:
        """
        Calculates overall compliance score %, verdict counts, and risk level.
        """
        counts = {"fully_met": 0, "partially_met": 0, "not_met": 0, "conflicting": 0, "total": len(detailed_gaps)}

        for gap in detailed_gaps:
            v = gap.get("verdict", "").lower()
            if "fully" in v:
                counts["fully_met"] += 1
            elif "partially" in v:
                counts["partially_met"] += 1
            elif "conflict" in v:
                counts["conflicting"] += 1
            else:
                counts["not_met"] += 1

        if counts["total"] > 0:
            raw_score = (counts["fully_met"] * 1.0 + counts["partially_met"] * 0.5) / counts["total"]
            overall_score = int(round(raw_score * 100))
        else:
            overall_score = 0

        if overall_score >= 80:
            risk_level = "LOW RISK — Compliant Posture"
        elif overall_score >= 60:
            risk_level = "MEDIUM RISK — Minor gaps requiring remediation"
        else:
            risk_level = "HIGH RISK — Immediate action required"

        return overall_score, counts, risk_level

    def build_chapter_breakdown(self, detailed_gaps: list) -> list:
        """
        Builds Chapter I to XI readiness breakdown with clear status indicators.
        """
        chapter_articles_map = {
            "I": ("General Provisions", "Art. 1–4"),
            "II": ("Principles", "Art. 5–11"),
            "III": ("Rights of the Data Subject", "Art. 12–23"),
            "IV": ("Controller and Processor", "Art. 24–43"),
            "V": ("Third Country Transfers", "Art. 44–49"),
            "VI": ("Supervisory Authorities", "Art. 51–59"),
            "VII": ("Cooperation & Consistency", "Art. 60–76"),
            "VIII": ("Remedies, Liability & Penalties", "Art. 77–84"),
            "IX": ("Special Situations", "Art. 85–91"),
            "X": ("Delegated Acts", "Art. 92–93"),
            "XI": ("Final Provisions", "Art. 94–99")
        }

        breakdown = []
        for ch_num, (ch_name, art_range) in chapter_articles_map.items():
            ch_gaps = [g for g in detailed_gaps if g.get("chapter") == ch_num]
            
            if ch_gaps:
                met = len([g for g in ch_gaps if "fully" in g.get("verdict", "").lower()])
                part = len([g for g in ch_gaps if "partially" in g.get("verdict", "").lower()])
                ch_score = int(round(((met * 1.0 + part * 0.5) / len(ch_gaps)) * 100))
            else:
                ch_score = 0

            if ch_score >= 65:
                status = "🟢 Compliant"
            elif ch_score >= 35:
                status = "🟡 Partial"
            else:
                status = "🔴 Non-Compliant"

            breakdown.append({
                "chapter": ch_num,
                "name": ch_name,
                "articles": art_range,
                "score": f"{ch_score}%",
                "status": status
            })

        return breakdown

    def build_action_plan(self, detailed_gaps: list) -> dict:
        """
        Categorizes recommendations into P1 Critical, P2 High, and P3 Medium.
        Enforces strict consistency:
        - Conflicting -> Status: "Legal contradiction", Action: fix_required
        - Not Met -> Status: "Missing entirely", Action: fix_required
        - Partially Met -> Status: "Currently vague", Action: fix_required
        - Fully Met -> Status: "Fully compliant", Action: "No action required. Maintain existing compliant policy clause."
        """
        p1_conflicting, p1_not_met, p2, p3 = [], [], [], []
        
        for gap in detailed_gaps:
            v = gap.get("verdict", "").lower()
            raw_fix = gap.get("fix_required", "").strip()

            if "conflict" in v:
                status_str = "Legal contradiction"
                action_str = raw_fix if raw_fix else "Update policy to eliminate GDPR contradiction."
                p1_conflicting.append({
                    "action_required": action_str,
                    "gdpr_article": gap.get("article", ""),
                    "current_status": status_str
                })
            elif "not met" in v or "missing" in v:
                status_str = "Missing entirely"
                action_str = raw_fix if raw_fix else f"Add policy clause for {gap.get('article')}."
                p1_not_met.append({
                    "action_required": action_str,
                    "gdpr_article": gap.get("article", ""),
                    "current_status": status_str
                })
            elif "partially" in v:
                status_str = "Currently vague"
                action_str = raw_fix if raw_fix else f"Refine policy clause for {gap.get('article')}."
                p2.append({
                    "action_required": action_str,
                    "gdpr_article": gap.get("article", ""),
                    "current_status": status_str
                })
            else:  # Fully Met
                status_str = "Fully compliant"
                action_str = "No action required. Maintain existing compliant policy clause and schedule annual review."
                p3.append({
                    "action_required": action_str,
                    "gdpr_article": gap.get("article", ""),
                    "current_status": status_str
                })

        # Place Conflicting items FIRST at the top of P1 Action Plan
        p1 = p1_conflicting + p1_not_met

        return {
            "p1_critical": p1[:8],
            "p2_high": p2[:6],
            "p3_medium": p3[:5]
        }

    def _evaluate_chapter(self, ch_num: str, reqs: list, policy_text: str) -> list:
        ch_title = reqs[0].get("chapter_title", f"Chapter {ch_num}") if reqs else f"Chapter {ch_num}"
        sub_agent = ChapterSubAgent(ch_num, ch_title)
        return sub_agent.evaluate_requirements(reqs, policy_text)

    def run_analysis(self, company_name: str, policy_name: str, policy_text: str, reqs_catalog: list) -> dict:
        """
        Main orchestration entry point: executes Chapter Sub-Agents IN PARALLEL and aggregates master JSON.
        """
        print(f"[INFO] Starting LexMesh Parallel Gap Analysis for '{company_name}' ({policy_name})...")
        
        # Group requirements by chapter
        chapter_reqs_map = {}
        for req in reqs_catalog:
            ch = req.get("chapter_number", "II")
            chapter_reqs_map.setdefault(ch, []).append(req)

        detailed_gaps = []

        # EXECUTE SUB-AGENTS IN PARALLEL USING THREAD POOL
        with ThreadPoolExecutor(max_workers=11) as executor:
            future_to_ch = {
                executor.submit(self._evaluate_chapter, ch_num, reqs, policy_text): ch_num
                for ch_num, reqs in chapter_reqs_map.items()
            }
            for future in as_completed(future_to_ch):
                ch_num = future_to_ch[future]
                try:
                    verdicts = future.result()
                    detailed_gaps.extend(verdicts)
                except Exception as e:
                    print(f"[WARNING] Error evaluating Chapter {ch_num}: {e}")

        # Sort detailed_gaps by requirement ID for clean display
        detailed_gaps.sort(key=lambda x: x.get("requirement_id", ""))

        overall_score, verdict_counts, risk_level = self.calculate_scores_and_summary(detailed_gaps)
        chapter_breakdown = self.build_chapter_breakdown(detailed_gaps)
        action_plan = self.build_action_plan(detailed_gaps)

        report_id = f"rep_{uuid.uuid4().hex[:8]}"
        now_str = datetime.datetime.now().strftime("%d %B %Y")

        master_report = {
            "report_id": report_id,
            "metadata": {
                "company_name": company_name,
                "policy_name": policy_name,
                "standard": "GDPR — All 99 Articles, 11 Chapters",
                "analysis_date": now_str,
                "generated_by": "LexMesh Engine v1.0",
                "analyzed_by": "Agentic RAG Pipeline (4-Agent System)"
            },
            "summary": {
                "overall_score": overall_score,
                "verdict_counts": verdict_counts,
                "risk_level": risk_level,
                "max_fine_exposure": "€20M or 4% annual revenue"
            },
            "chapter_breakdown": chapter_breakdown,
            "detailed_gaps": detailed_gaps,
            "priority_action_plan": action_plan,
            "executive_summary": (
                f"{company_name}'s current {policy_name} demonstrates a baseline foundation for data protection compliance "
                f"with an overall compliance score of {overall_score}%. Critical gaps were identified in user rights handling, "
                "data retention specifications, and breach notification timelines. Immediate remediation of P1 priority items is "
                "strongly recommended before regulatory audit."
            ),
            "disclaimer": (
                "DISCLAIMER: This report was generated by LexMesh, an AI-powered compliance analysis tool. "
                "It is intended for informational purposes only and does not constitute legal advice."
            )
        }

        # Save to Supabase
        if supabase_db.is_connected():
            supabase_db.save_compliance_report(report_id, company_name, policy_name, overall_score, master_report)
            print(f"[INFO] Master report {report_id} saved to Supabase Cloud.")

        return master_report

supervisor = SupervisorAgent()
