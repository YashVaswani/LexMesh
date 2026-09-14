"""
Supervisor Router Agent (Enterprise Multi-Framework Parallel RAG Pipeline)
Orchestrates parallel RAG evaluation across all 4 compliance standards (GDPR, HIPAA, RBI, SOC 2)
using ThreadPoolExecutor, maps requirements to 6 Core Enterprise Policy Domains,
calculates framework-specific statutory fine exposure and policy domain readiness scores.
"""

import json
import re
import time
import uuid
import datetime
from concurrent.futures import ThreadPoolExecutor, as_completed
from agents.chapter_agents import ChapterSubAgent
from db.supabase_client import supabase_db
from ingestion.catalog_manager import catalog_manager, FRAMEWORKS, POLICY_DOMAINS

class SupervisorAgent:
    def __init__(self):
        print("[INFO] Initializing Supervisor Router Agent (Multi-Framework Engine)...")

    def _evaluate_batch(self, framework_id: str, section_num: str, reqs: list, policy_text: str) -> list:
        section_title = reqs[0].get("chapter_title", f"Section {section_num}") if reqs else f"Section {section_num}"
        sub_agent = ChapterSubAgent(section_num, section_title, framework_id=framework_id)
        return sub_agent.evaluate_requirements(reqs, policy_text)

    def calculate_framework_summary(self, framework_id: str, gaps: list) -> dict:
        """
        Calculates score %, verdict counts, risk level, and penalty exposure for a single framework.
        """
        counts = {"fully_met": 0, "partially_met": 0, "not_met": 0, "conflicting": 0, "total": len(gaps)}
        failing_chapters = set()

        for gap in gaps:
            v = gap.get("verdict", "").lower()
            ch = gap.get("chapter", "")
            if "fully" in v:
                counts["fully_met"] += 1
            elif "partially" in v:
                counts["partially_met"] += 1
                failing_chapters.add(ch)
            elif "conflict" in v:
                counts["conflicting"] += 1
                failing_chapters.add(ch)
            else:
                counts["not_met"] += 1
                failing_chapters.add(ch)

        # Fix scoring model: Weight each article by coverage depth & set partially_met weight to 0.7
        article_gaps = {}
        for gap in gaps:
            art = gap.get("article", "General")
            article_gaps.setdefault(art, []).append(gap)

        article_scores = []
        for art, art_gaps in article_gaps.items():
            art_counts = {"fully": 0, "partially": 0, "not": 0}
            for g in art_gaps:
                v = g.get("verdict", "").lower()
                if "fully" in v:
                    art_counts["fully"] += 1
                elif "partially" in v:
                    art_counts["partially"] += 1
                else:
                    art_counts["not"] += 1
            # Weighting: Fully Met = 1.0, Partially Met = 0.70, Not Met/Conflict = 0.0
            art_score = (art_counts["fully"] * 1.0 + art_counts["partially"] * 0.7) / len(art_gaps)
            article_scores.append(art_score)

        if article_scores:
            score = int(round((sum(article_scores) / len(article_scores)) * 100))
        else:
            score = 0

        # Risk level
        if score >= 80:
            risk_level = "LOW RISK — Compliant Posture"
        elif score >= 60:
            risk_level = "MEDIUM RISK — Minor gaps requiring remediation"
        else:
            risk_level = "HIGH RISK — Immediate action required"

        # Fine / Penalty Exposure calculation based on framework statutory rules
        fw_info = catalog_manager.get_framework_info(framework_id)
        if framework_id == "gdpr":
            tier2 = {"II", "III", "V", "VIII"}
            if failing_chapters.intersection(tier2):
                exposure = "€20M or 4% global annual revenue (GDPR Art. 83(5) Tier 2)"
            elif failing_chapters:
                exposure = "€10M or 2% global annual revenue (GDPR Art. 83(4) Tier 1)"
            else:
                exposure = "Low Exposure — Compliance Maintenance"
        elif framework_id == "hipaa":
            if counts["not_met"] > 0 or counts["conflicting"] > 0:
                exposure = "$1.9M+ Statutory Civil Monetary Penalty per year (45 CFR § 160)"
            elif counts["partially_met"] > 0:
                exposure = "$100k–$500k Potential HITECH Audit Penalty"
            else:
                exposure = "Low Exposure — Compliant HIPAA Security/Privacy Posture"
        elif framework_id == "rbi":
            if counts["not_met"] > 0 or counts["conflicting"] > 0:
                exposure = "Banking Regulation Act Statutory Penalty & RBI Enforcement Directions"
            elif counts["partially_met"] > 0:
                exposure = "RBI Supervisory Warning & mandatory 30-day remediation mandate"
            else:
                exposure = "Low Risk — Satisfies RBI Cyber Framework Direction"
        elif framework_id == "soc2":
            if counts["not_met"] > 0 or counts["conflicting"] > 0:
                exposure = "High Audit Risk — Potential Qualified or Adverse SOC 2 Audit Opinion"
            elif counts["partially_met"] > 0:
                exposure = "Medium Audit Risk — CPA Exception noted in SOC 2 Type II report"
            else:
                exposure = "Clean Audit Posture — Unqualified SOC 2 Type II Opinion"
        else:
            exposure = "Compliance Statutory Penalty"

        return {
            "framework_id": framework_id,
            "framework_name": fw_info["name"],
            "full_name": fw_info["full_name"],
            "icon": fw_info["icon"],
            "score": score,
            "verdict_counts": counts,
            "risk_level": risk_level,
            "penalty_exposure": exposure
        }

    def build_policy_domain_breakdown(self, all_gaps: list, active_frameworks: list = None) -> list:
        """
        Calculates readiness score and status for each of the 6 Enterprise Policy Domains across active frameworks.
        """
        active_fws = active_frameworks
        if not active_fws:
            active_fws = list(set(g.get("framework") for g in all_gaps if g.get("framework")))
        if not active_fws:
            active_fws = ["gdpr", "hipaa", "rbi", "soc2"]

        breakdown = []
        for dom_id, dom_info in POLICY_DOMAINS.items():
            dom_gaps = [g for g in all_gaps if g.get("policy_domain") == dom_id]
            if dom_gaps:
                met = len([g for g in dom_gaps if "fully" in g.get("verdict", "").lower()])
                part = len([g for g in dom_gaps if "partially" in g.get("verdict", "").lower()])
                dom_score = int(round(((met * 1.0 + part * 0.7) / len(dom_gaps)) * 100))
            else:
                dom_score = 0

            if dom_score >= 65:
                status = "🟢 Compliant"
            elif dom_score >= 35:
                status = "🟡 Partial"
            else:
                status = "🔴 Non-Compliant"

            # Per framework score in this domain
            fw_scores = {}
            for fw_id in active_fws:
                fw_dom_gaps = [g for g in dom_gaps if g.get("framework") == fw_id]
                if fw_dom_gaps:
                    f_met = len([g for g in fw_dom_gaps if "fully" in g.get("verdict", "").lower()])
                    f_part = len([g for g in fw_dom_gaps if "partially" in g.get("verdict", "").lower()])
                    fw_scores[fw_id] = int(round(((f_met * 1.0 + f_part * 0.7) / len(fw_dom_gaps)) * 100))
                else:
                    fw_scores[fw_id] = 0

            breakdown.append({
                "domain_id": dom_id,
                "domain_title": dom_info["title"],
                "icon": dom_info["icon"],
                "description": dom_info["description"],
                "score": f"{dom_score}%",
                "score_raw": dom_score,
                "status": status,
                "framework_scores": fw_scores,
                "total_requirements": len(dom_gaps)
            })

        return breakdown

    def build_policy_grouped_action_plan(self, all_gaps: list) -> dict:
        """
        Categorizes remediation items into P1 Critical, P2 High, and P3 Medium grouped by Policy Domain across all 4 frameworks.
        Excludes Fully Met items completely.
        """
        by_fw_p1 = {"gdpr": [], "hipaa": [], "rbi": [], "soc2": []}
        by_fw_p2 = {"gdpr": [], "hipaa": [], "rbi": [], "soc2": []}
        by_fw_p3 = {"gdpr": [], "hipaa": [], "rbi": [], "soc2": []}

        for gap in all_gaps:
            v = gap.get("verdict", "").lower()
            if "fully" in v:
                continue  # Fully Met requirements do not belong in the remediation plan

            raw_fix = gap.get("fix_required", "").strip()
            fw = gap.get("framework", "gdpr").lower()
            fw_info = catalog_manager.get_framework_info(fw)
            dom_info = POLICY_DOMAINS.get(gap.get("policy_domain", "data_governance"), {})

            item = {
                "Policy Domain": dom_info.get("title", "Data Governance"),
                "Framework Compliance": fw_info['name'],
                "Framework Standard": fw_info['name'],
                "framework_tag": fw,
                "Requirement Citation": gap.get("article", ""),
                "Current Status": "Legal contradiction" if "conflict" in v else ("Missing entirely" if ("not met" in v or "missing" in v) else ("Currently vague" if "partially" in v else "Fully met")),
                "Action Required": raw_fix if raw_fix else f"Update policy clause for {gap.get('article')} under {fw_info['name']}."
            }

            if fw not in by_fw_p1:
                by_fw_p1[fw] = []
                by_fw_p2[fw] = []
                by_fw_p3[fw] = []

            if "conflict" in v or "not met" in v or "missing" in v:
                by_fw_p1[fw].append(item)
            elif "partially" in v:
                # Distribute partially met items: high-risk domains go to P2 High, others to P3 Medium
                dom_id = gap.get("policy_domain", "")
                if dom_id in ["data_governance", "access_control", "incident_response"]:
                    by_fw_p2[fw].append(item)
                else:
                    by_fw_p3[fw].append(item)

        p1_critical, p2_high, p3_medium = [], [], []

        # Interleave items across all 4 frameworks
        for f_id in ["gdpr", "hipaa", "rbi", "soc2"]:
            p1_critical.extend(by_fw_p1.get(f_id, [])[:6])
            p2_high.extend(by_fw_p2.get(f_id, [])[:5])
            p3_medium.extend(by_fw_p3.get(f_id, [])[:4])

        return {
            "p1_critical": p1_critical,
            "p2_high": p2_high,
            "p3_medium": p3_medium
        }

    def run_multi_framework_analysis(self, company_name: str, policy_name: str, policy_text: str, active_frameworks: list = None, **kwargs) -> dict:
        """
        Main multi-framework orchestration entry point:
        Executes Parallel Sub-Agents across all selected catalogs simultaneously.
        """
        print(f"[INFO] Starting LexMesh Multi-Framework Parallel Analysis for '{company_name}' ({policy_name})...")
        all_catalogs = catalog_manager.load_all_catalogs()

        # Default to all frameworks if none specified
        active_fws = active_frameworks or ["gdpr", "hipaa", "rbi", "soc2"]
        all_catalogs = {k: v for k, v in all_catalogs.items() if k in active_fws}

        # Build list of tasks for ThreadPoolExecutor
        tasks = []

        # GDPR articles 51-76 govern supervisory authorities/EDPB — not company obligations.
        # GDPR articles 85-99 govern Member State laws, repeal, and Commission procedures.
        # These cannot be evaluated against a company's internal policy.
        GDPR_REGULATOR_ARTICLES = {str(n) for n in range(51, 77)} | {str(n) for n in range(85, 100)}

        for fw_id, cat in all_catalogs.items():
            # Filter out regulator-only requirements
            company_reqs = []
            for req in cat:
                article_raw = str(req.get("article_number", "")).strip()
                # Extract numeric part: "Art. 51" -> "51", "45 CFR § 164.308" -> keep
                article_num = re.sub(r'[^\d]', '', article_raw.split()[1] if len(article_raw.split()) > 1 else article_raw)[:3]
                if fw_id == "gdpr" and article_num in GDPR_REGULATOR_ARTICLES:
                    continue  # Skip regulator-only GDPR articles
                company_reqs.append(req)

            # Group requirements by chapter/section within framework
            sec_map = {}
            for req in company_reqs:
                ch = req.get("chapter_number", "I")
                sec_map.setdefault(ch, []).append(req)

            for ch_num, reqs in sec_map.items():
                tasks.append((fw_id, ch_num, reqs))

        all_gaps = []

        workers = min(8, max(4, len(tasks)))
        if workers > 0:
            with ThreadPoolExecutor(max_workers=workers) as executor:
                future_to_task = {}
                for fw_id, ch_num, reqs in tasks:
                    future = executor.submit(self._evaluate_batch, fw_id, ch_num, reqs, policy_text)
                    future_to_task[future] = (fw_id, ch_num)
                    time.sleep(0.005)  # Ultra-fast 5ms pacing delay

                for future in as_completed(future_to_task):
                    fw_id, ch_num = future_to_task[future]
                    try:
                        results = future.result()
                        all_gaps.extend(results)
                    except Exception as e:
                        print(f"[WARNING] Error evaluating Framework '{fw_id}' Section '{ch_num}': {e}")

        # Compute Framework Summaries for each active compliance
        framework_summaries = {}
        total_score_sum = 0
        fw_count = 0

        for fw_id in FRAMEWORKS.keys():
            if fw_id not in active_fws:
                continue
            fw_gaps = [g for g in all_gaps if g.get("framework") == fw_id]
            summary_dict = self.calculate_framework_summary(fw_id, fw_gaps)
            framework_summaries[fw_id] = summary_dict
            total_score_sum += summary_dict["score"]
            fw_count += 1

        overall_score = int(round(total_score_sum / fw_count)) if fw_count > 0 else 0

        # Overall risk level
        if overall_score >= 80:
            overall_risk = "LOW RISK — Strong Multi-Framework Compliance Posture"
        elif overall_score >= 60:
            overall_risk = "MEDIUM RISK — Operational & Statutory Gaps Identified"
        else:
            overall_risk = "HIGH RISK — Critical Compliance Omissions Across Standards"

        # Build Policy Domain Breakdown
        policy_breakdown = self.build_policy_domain_breakdown(all_gaps, active_frameworks=active_fws)

        # Structure detailed gaps by Policy Domain -> Framework
        gaps_by_domain = {}
        for dom_id, dom_info in POLICY_DOMAINS.items():
            dom_gaps = [g for g in all_gaps if g.get("policy_domain") == dom_id]
            fw_grouped = {}
            for fw_id, fw_info in FRAMEWORKS.items():
                fw_grouped[fw_id] = [g for g in dom_gaps if g.get("framework") == fw_id]
            
            gaps_by_domain[dom_id] = {
                "domain_info": dom_info,
                "framework_gaps": fw_grouped
            }

        # Build Policy-Grouped Action Plan
        action_plan = self.build_policy_grouped_action_plan(all_gaps)

        # Build Compliant Areas List
        compliant_areas = []
        for gap in all_gaps:
            v = gap.get("verdict", "").lower()
            if "fully" in v:
                fw = gap.get("framework", "gdpr").lower()
                fw_info = catalog_manager.get_framework_info(fw)
                dom_info = POLICY_DOMAINS.get(gap.get("policy_domain", "data_governance"), {})
                compliant_areas.append({
                    "Policy Domain": dom_info.get("title", "Data Governance"),
                    "Framework Standard": fw_info['name'],
                    "framework_tag": fw,
                    "Requirement Citation": gap.get("article", ""),
                    "Current Status": "Fully Compliant",
                    "Verification Quote": gap.get("your_policy", "")
                })

        report_id = f"rep_{uuid.uuid4().hex[:8]}"
        now_str = datetime.datetime.now().strftime("%d %B %Y")

        master_report = {
            "report_id": report_id,
            "metadata": {
                "company_name": company_name,
                "policy_name": policy_name,
                "compliances_analyzed": [FRAMEWORKS[fw]["name"] for fw in active_fws if fw in FRAMEWORKS],
                "analysis_date": now_str,
                "generated_by": "LexMesh Engine v2.0 (Multi-Framework)",
                "analyzed_by": "Parallel Agentic RAG Pipeline"
            },
            "summary": {
                "overall_score": overall_score,
                "overall_risk": overall_risk,
                "framework_summaries": framework_summaries,
                "total_gaps_analyzed": len(all_gaps)
            },
            "policy_domain_breakdown": policy_breakdown,
            "detailed_policy_gaps": gaps_by_domain,
            "all_gaps_flat": all_gaps,
            "priority_action_plan": action_plan,
            "compliant_areas": compliant_areas,
            "executive_summary": (
                f"{company_name}'s uploaded document ('{policy_name}') was evaluated against selected enterprise compliance standards "
                f"across core policy domains. "
                f"The organization achieved a Unified Multi-Framework Compliance Score of {overall_score}%. "
                "Framework-specific posture assessments and prioritized remediation plans are detailed below."
            ),
            "disclaimer": (
                "DISCLAIMER: This report was generated by LexMesh, an AI-powered compliance analysis engine. "
                "It is intended for informational and audit-readiness purposes only and does not constitute formal legal advice."
            )
        }

        # Save report to Supabase if connected
        if supabase_db.is_connected():
            try:
                supabase_db.save_report(master_report, user_id=kwargs.get('user_id'))
            except Exception as e:
                print(f"[WARNING] Could not persist report to Supabase: {e}")

        return master_report

    def run_analysis(self, company_name: str, policy_name: str, policy_text: str, reqs_catalog: list = None, framework_id: str = "gdpr", **kwargs) -> dict:
        """
        Primary execution entry point. Always runs full multi-framework analysis.
        """
        return self.run_multi_framework_analysis(company_name, policy_name, policy_text, **kwargs)

supervisor = SupervisorAgent()
