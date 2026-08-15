"""
LexMesh — Streamlit Web Interface (Policy-Centric Multi-Framework Engine)
Interactive dashboard for document ingestion, simultaneous multi-framework parallel RAG analysis,
user-selected compliance filtering, policy-centric detailed gap accordions (EU GDPR, US HIPAA, RBI Cyber, SOC 2 Type II),
metric score cards, policy-grouped action plans, and targeted PDF/JSON export.
"""

import os
import json
import re
import pymupdf as fitz
import streamlit as st
from config import config
from db.supabase_client import supabase_db
from agents.adk_agent import adk_supervisor
from reporter.pdf_generator import generate_compliance_pdf
from ingestion.catalog_manager import catalog_manager, FRAMEWORKS, POLICY_DOMAINS

st.set_page_config(
    page_title="LexMesh — Multi-Framework Compliance RAG",
    page_icon="🛡️",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS for dark/modern styling
st.markdown("""
<style>
    .main-header { font-size: 2.3rem; font-weight: 800; color: #1E3A8A; margin-bottom: 0.5rem; }
    .sub-header { font-size: 1.05rem; color: #475569; margin-bottom: 1.2rem; }
    .stButton>button { background-color: #2563EB; color: white; border-radius: 6px; font-weight: 600; width: 100%; }
    .legend-box { background-color: #F8FAFC; border: 1px solid #E2E8F0; padding: 10px 15px; border-radius: 6px; font-size: 0.9rem; margin-bottom: 1rem; }
    .fw-card { background-color: #F8FAFC; border: 1px solid #CBD5E1; padding: 15px; border-radius: 8px; margin-bottom: 10px; }
    .status-met { color: #16A34A; font-weight: bold; }
    .status-partial { color: #D97706; font-weight: bold; }
    .status-not { color: #DC2626; font-weight: bold; }
    .status-conflict { color: #B45309; font-weight: bold; }
</style>
""", unsafe_allow_html=True)

st.markdown('<div class="main-header">🛡️ LexMesh</div>', unsafe_allow_html=True)
st.markdown('<div class="sub-header">Policy-Centric Compliance Engine (EU GDPR · US HIPAA · RBI Cyber · SOC 2 Type II)</div>', unsafe_allow_html=True)

def extract_metadata_from_pdf(pdf_bytes: bytes) -> tuple:
    """
    Extracts Company Name and Policy Version/Name automatically from the uploaded PDF document.
    """
    try:
        doc = fitz.open(stream=pdf_bytes, filetype="pdf")
        first_page_text = doc[0].get_text() if len(doc) > 0 else ""
        
        extracted_company = ""
        extracted_policy_name = ""

        # 1. Company Name Extraction
        comp_match = re.search(r"Company\s*[:\t]?\s*([^\n\r]+)", first_page_text, re.IGNORECASE)
        if comp_match:
            extracted_company = comp_match.group(1).strip()
        else:
            corp_match = re.search(r"([A-Za-z0-9\s&]+(?:Pvt Ltd|Ltd|Inc|Corp|Corporation|Technologies|Cloud|Systems|AI))", first_page_text)
            if corp_match:
                extracted_company = corp_match.group(1).strip()

        # 2. Policy Version / Title Extraction
        title_match = re.search(r"(PRIVACY POLICY|PRIVACY NOTICE|DATA PROTECTION POLICY|INFORMATION SECURITY POLICY|ACCESS CONTROL POLICY|INCIDENT RESPONSE PLAN|TERMS OF SERVICE)[^\n]*", first_page_text, re.IGNORECASE)
        ver_match = re.search(r"(v\d+\.\d+|\b\d+\.\d+\b)", first_page_text, re.IGNORECASE)

        if title_match and ver_match:
            extracted_policy_name = f"{title_match.group(0).strip().title()} {ver_match.group(0)}"
        elif title_match:
            extracted_policy_name = title_match.group(0).strip().title()
        elif ver_match:
            extracted_policy_name = f"Enterprise Policy {ver_match.group(0)}"

        return extracted_company, extracted_policy_name
    except Exception:
        return "", ""

def filter_report_payload(report_json: dict, target_fw_keys: list) -> dict:
    """
    Filters master report JSON payload to include only user-selected compliance frameworks.
    Dynamically recalculates overall compliance score and filters gap cards and action plan items.
    """
    if not target_fw_keys or set(target_fw_keys) == {"gdpr", "hipaa", "rbi", "soc2"}:
        return report_json

    filtered = json.loads(json.dumps(report_json))
    
    # 1. Filter Framework Summaries
    fw_summaries = filtered.get("summary", {}).get("framework_summaries", {})
    new_summaries = {k: v for k, v in fw_summaries.items() if k in target_fw_keys}
    filtered["summary"]["framework_summaries"] = new_summaries

    # 2. Recalculate Overall Score for Selected Frameworks
    if new_summaries:
        scores = [v.get("score", 0) for v in new_summaries.values()]
        new_overall = int(round(sum(scores) / len(scores)))
        filtered["summary"]["overall_score"] = new_overall
        if new_overall >= 80:
            filtered["summary"]["overall_risk"] = "LOW RISK — High Compliance Posture"
        elif new_overall >= 60:
            filtered["summary"]["overall_risk"] = "MEDIUM RISK — Operational Gaps Exist"
        else:
            filtered["summary"]["overall_risk"] = "HIGH RISK — Critical Compliance Omissions"

    # 3. Filter Policy Domain Breakdown
    new_breakdown = []
    for dom in filtered.get("policy_domain_breakdown", []):
        fw_sc = dom.get("framework_scores", {})
        new_fw_sc = {k: v for k, v in fw_sc.items() if k in target_fw_keys}
        dom_copy = dict(dom)
        dom_copy["framework_scores"] = new_fw_sc
        if new_fw_sc:
            dom_copy["score"] = f"{int(round(sum(new_fw_sc.values()) / len(new_fw_sc)))}%"
        new_breakdown.append(dom_copy)
    filtered["policy_domain_breakdown"] = new_breakdown

    # 4. Filter Detailed Policy Gaps
    new_detailed = {}
    for dom_id, dom_data in filtered.get("detailed_policy_gaps", {}).items():
        dom_data_copy = dict(dom_data)
        fw_gaps = dom_data.get("framework_gaps", {})
        new_fw_gaps = {k: v for k, v in fw_gaps.items() if k in target_fw_keys}
        dom_data_copy["framework_gaps"] = new_fw_gaps
        new_detailed[dom_id] = dom_data_copy
    filtered["detailed_policy_gaps"] = new_detailed

    # 5. Filter Flat Gap Cards
    all_gaps = filtered.get("all_gaps_flat", filtered.get("detailed_gaps", []))
    filtered["all_gaps_flat"] = [g for g in all_gaps if g.get("framework") in target_fw_keys]

    # 6. Filter Action Plan Items
    plan = filtered.get("priority_action_plan", {})
    def match_item(item):
        tag = (item.get("Framework Compliance") or item.get("Framework compliance") or item.get("Framework Standard") or item.get("framework_tag", "")).lower()
        for k in target_fw_keys:
            if k == "gdpr" and "gdpr" in tag: return True
            if k == "hipaa" and "hipaa" in tag: return True
            if k == "rbi" and "rbi" in tag: return True
            if k == "soc2" and "soc" in tag: return True
        return False

    filtered["priority_action_plan"] = {
        "p1_critical": [i for i in plan.get("p1_critical", []) if match_item(i)],
        "p2_high": [i for i in plan.get("p2_high", []) if match_item(i)],
        "p3_medium": [i for i in plan.get("p3_medium", []) if match_item(i)]
    }

    return filtered

# SIDEBAR CONFIGURATION & UPLOAD
with st.sidebar:
    st.header("⚙️ System Pipeline")
    
    # System Status
    st.subheader("System Health")
    st.write(f"🔹 Gemini API: {'✅ Connected' if config.GEMINI_API_KEY else '❌ Missing'}")
    st.write(f"🔹 Groq API: {'✅ Connected' if config.GROQ_API_KEY else '❌ Missing'}")
    st.write(f"🔹 Supabase DB: {'✅ Connected' if supabase_db.is_connected() else '⚠️ Offline / Local Mode'}")
    st.write(f"🔹 Orchestration: ✅ Google ADK Supervisor ")
    
    st.divider()
    st.subheader("🎯 Compliance  Selection")
    selected_framework_label = st.selectbox(
        "Select compliance  to analyze & view:",
        options=[
            "🌐 All Compliance ",
            " EU GDPR",
            "🏥 US HIPAA",
            "🏦 RBI Cyber Framework",
            "🛡️ SOC 2 Type II"
        ],
        index=0,
        help="Select which compliance  you want to inspect on the dashboard."
    )

    fw_map = {
        "🌐 All Compliances ": ["gdpr", "hipaa", "rbi", "soc2"],
        "   EU GDPR": ["gdpr"],
        "🏥 US HIPAA": ["hipaa"],
        "🏦 RBI Cyber Framework": ["rbi"],
        "🛡️ SOC 2 Type II": ["soc2"]
    }
    selected_fw_keys = fw_map.get(selected_framework_label, ["gdpr", "hipaa", "rbi", "soc2"])

    st.divider()
    st.subheader("Document Input")
    
    uploaded_file = st.file_uploader("Upload Company Policy PDF", type=["pdf"])
    
    auto_company = ""
    auto_policy = ""
    pdf_bytes = None

    if uploaded_file is not None:
        pdf_bytes = uploaded_file.read()
        extracted_company, extracted_policy = extract_metadata_from_pdf(pdf_bytes)
        
        # Check if file has changed
        current_file_id = f"{uploaded_file.name}_{uploaded_file.size}"
        if st.session_state.get("last_uploaded_file_id") != current_file_id:
            st.session_state["last_uploaded_file_id"] = current_file_id
            st.session_state["company_name_input"] = extracted_company or ""
            st.session_state["policy_name_input"] = extracted_policy or ""
            
        auto_company = st.session_state.get("company_name_input", extracted_company or "")
        auto_policy = st.session_state.get("policy_name_input", extracted_policy or "")
    else:
        st.session_state.pop("last_uploaded_file_id", None)
        st.session_state.pop("company_name_input", None)
        st.session_state.pop("policy_name_input", None)
        auto_company = ""
        auto_policy = ""

    company_name = st.text_input("Company Name", value=auto_company, placeholder="e.g. TechStartup Pvt Ltd")
    policy_name = st.text_input("Policy Version / Name", value=auto_policy, placeholder="e.g. Privacy Policy v2.1")
    
    run_btn = st.button("🚀 Run Unified Gap Analysis", disabled=(uploaded_file is None))

# MAIN CONTENT AREA
if uploaded_file and run_btn and pdf_bytes:
    final_company = company_name.strip() if company_name.strip() else "Uploaded Organization"
    final_policy = policy_name.strip() if policy_name.strip() else "Company Policy Document"

    # Extract PDF text
    doc = fitz.open(stream=pdf_bytes, filetype="pdf")
    policy_text = ""
    for page in doc:
        policy_text += page.get_text() + "\n"
    
    with st.spinner("🚀 Running Gap Analysis..."):
        report_json = adk_supervisor.run_adk_pipeline(final_company, final_policy, policy_text)
        st.session_state["active_report"] = report_json

# DISPLAY REPORT DASHBOARD IF AVAILABLE
if "active_report" in st.session_state:
    master_report = st.session_state["active_report"]
    
    # Apply user-selected compliance filter to dashboard view
    report = filter_report_payload(master_report, selected_fw_keys)
    meta = report.get("metadata", {})
    summary = report.get("summary", {})
    fw_summaries = summary.get("framework_summaries", {})
    policy_breakdown = report.get("policy_domain_breakdown", [])
    detailed_gaps_by_domain = report.get("detailed_policy_gaps", {})
    action_plan = report.get("priority_action_plan", {})
    
    st.divider()
    
    # Dashboard Tabs
    tab1, tab2, tab3, tab4, tab5 = st.tabs(
        [
            "📊 Score & Framework Breakdown", 
            "📑 Policy Posture", 
            "🔍 Detailed Policy Gaps", 
            "📋 Policy Action Plan", 
            "📥 Report Export"
        ]
    )
    
    # TAB 1: OVERVIEW METRICS & SIDE-BY-SIDE FRAMEWORK SCORE CARDS
    with tab1:
        st.subheader("Selected Compliance Score & Breakdown")
        
        # Overall Score Metric Banner
        m_col1, m_col2 = st.columns([1, 2])
        with m_col1:
            st.metric("Unified Score (Selected Scope)", f"{summary.get('overall_score', 0)}%")
        with m_col2:
            st.info(f"**Overall Posture:** {summary.get('overall_risk', 'MEDIUM RISK')}")

        st.divider()
        st.subheader("Compliance  Score Cards")
        
        # Side-by-Side Metric Cards for Selected Frameworks
        active_fw_cards = [
            ("gdpr", " EU GDPR"),
            ("hipaa", "🏥 US HIPAA"),
            ("rbi", "🏦 RBI Cyber"),
            ("soc2", "🛡️ SOC 2 Type II")
        ]
        active_fw_cards = [item for item in active_fw_cards if item[0] in selected_fw_keys]

        if active_fw_cards:
            cols = st.columns(len(active_fw_cards))
            for idx, (fw_key, label) in enumerate(active_fw_cards):
                s_data = fw_summaries.get(fw_key, {})
                with cols[idx]:
                    st.metric(label, f"{s_data.get('score', 0)}%")
                    st.caption(f"**Risk:** {s_data.get('risk_level', 'High Risk')}")
                    st.write(f"**Penalty Exposure:** {s_data.get('penalty_exposure', 'Statutory Penalty')}")

    # TAB 2: POLICY POSTURE
    with tab2:
        st.subheader("Policy-Centric Domain Readiness Posture")
        st.markdown("""
        <div class="legend-box">
            <b>📌 Status Legend:</b> &nbsp;&nbsp;
            <span>🟢 <b>Compliant</b> (Score ≥ 65%) — High policy alignment</span> &nbsp;|&nbsp;
            <span>🟡 <b>Partial</b> (Score 35%–64%) — Operational gaps exist</span> &nbsp;|&nbsp;
            <span>🔴 <b>Non-Compliant</b> (Score &lt; 35%) — Critical omissions</span>
        </div>
        """, unsafe_allow_html=True)
        
        # Format breakdown as visual clean table for selected frameworks
        rows = []
        for dom in policy_breakdown:
            fw_sc = dom.get("framework_scores", {})
            row = {
                "Policy Domain": f"{dom.get('icon')} {dom.get('domain_title')}",
                "Overall Readiness": dom.get("score"),
                "Status": dom.get("status")
            }
            if "gdpr" in selected_fw_keys: row["🇪🇺 GDPR"] = f"{fw_sc.get('gdpr', 0)}%"
            if "hipaa" in selected_fw_keys: row["🏥 HIPAA"] = f"{fw_sc.get('hipaa', 0)}%"
            if "rbi" in selected_fw_keys: row["🏦 RBI Cyber"] = f"{fw_sc.get('rbi', 0)}%"
            if "soc2" in selected_fw_keys: row["🛡️ SOC 2"] = f"{fw_sc.get('soc2', 0)}%"
            rows.append(row)
        st.table(rows)

    # TAB 3: DETAILED POLICY GAPS (POLICY-BY-POLICY EXPANDERS WITH FRAMEWORK TABS)
    with tab3:
        st.subheader("Detailed Gap Analysis — Grouped by Company Policy Domain")
        st.caption("Click any policy domain arrow below to view and analyze gaps comparing compliance  side-by-side right inside that policy section!")
        
        verdict_filter = st.multiselect(
            "Filter by Verdict", 
            ["Fully Met", "Partially Met", "Not Met", "Conflicting"], 
            default=["Not Met", "Partially Met", "Conflicting"],
            key="policy_gap_verdict_filter"
        )

        for dom_id, dom_data in detailed_gaps_by_domain.items():
            dom_info = dom_data.get("domain_info", {})
            fw_gaps = dom_data.get("framework_gaps", {})
            
            # Find score for this domain
            matched_dom = next((d for d in policy_breakdown if d.get("domain_id") == dom_id), {})
            dom_score_str = matched_dom.get("score", "0%")
            dom_status_str = matched_dom.get("status", "🔴 Non-Compliant")

            with st.expander(f"{dom_info.get('icon', '📄')} {dom_info.get('title')} — Readiness: {dom_score_str} ({dom_status_str})"):
                st.write(f"*{dom_info.get('description')}*")
                st.divider()

                # Inner tabs for user-selected Frameworks under this Policy Domain
                fw_tab_labels = {
                    "gdpr": " EU GDPR Gaps",
                    "hipaa": "🏥 US HIPAA Gaps",
                    "rbi": "🏦 RBI Cyber Framework Gaps",
                    "soc2": "🛡️ SOC 2 Type II Gaps"
                }
                
                active_fw_keys_present = [k for k in selected_fw_keys if k in fw_tab_labels]
                active_tab_names = [fw_tab_labels[k] for k in active_fw_keys_present]

                if active_tab_names:
                    inner_tabs = st.tabs(active_tab_names)
                    for idx, f_key in enumerate(active_fw_keys_present):
                        with inner_tabs[idx]:
                            gaps_list = fw_gaps.get(f_key, [])
                            filtered_gaps = [g for g in gaps_list if not verdict_filter or g.get("verdict") in verdict_filter]

                            if not filtered_gaps:
                                st.success(f"No matching gaps for {f_key.upper()} under this policy domain!")
                            else:
                                for gap in filtered_gaps:
                                    v_str = gap.get("verdict", "Not Met")
                                    v_badge = "🟢 Fully Met" if "fully" in v_str.lower() else ("🟡 Partially Met" if "partially" in v_str.lower() else ("⚡ Conflicting" if "conflict" in v_str.lower() else "🔴 Not Met"))
                                    
                                    with st.container():
                                        st.markdown(f"**[{gap.get('requirement_id')}] {gap.get('article')} — {v_badge}**")
                                        st.write(f"• **Regulatory Requirement Mandate:** {gap.get('requirement_mandate') or gap.get('gdpr_requires')}")
                                        st.write(f"• **Your Policy Citation:** *\"{gap.get('your_policy')}\"*")
                                        st.write(f"• **Audit Analysis & Reasoning:** {gap.get('analysis')}")
                                        st.info(f"💡 **Action Required Fix:** {gap.get('fix_required')}")
                                        st.divider()

    # TAB 4: POLICY-GROUPED ACTION PLAN
    with tab4:
        st.subheader("Priority Action Plan — Grouped by Policy Document & Domain")
        st.caption("Remediation items organized by priority tier for selected compliance.")
        
        st.error("🚨 P1 — Critical Priority (Immediate Action Required)")
        if action_plan.get("p1_critical"):
            st.table(action_plan.get("p1_critical"))
        else:
            st.write("No P1 critical items.")

        st.warning("⚠️ P2 — High Priority (Operational & Clause Revisions)")
        if action_plan.get("p2_high"):
            st.table(action_plan.get("p2_high"))
        else:
            st.write("No P2 high items.")

        st.info("ℹ️ P3 — Medium Priority (Annual Review & Maintenance)")
        if action_plan.get("p3_medium"):
            st.table(action_plan.get("p3_medium"))
        else:
            st.write("No P3 medium items.")

    # TAB 5: REPORT EXPORT (SELECT COMPLIANCE SCOPE FOR EXPORT)
    with tab5:
        st.subheader("Executive Summary")
        st.write(report.get("executive_summary", ""))
        
        st.divider()
        st.subheader("📥 Select Compliance Scope for Export")
        st.caption("Choose which compliance you want to include in your downloaded JSON and PDF report.")
        
        export_scope_label = st.selectbox(
            "Select Targeted Compliance for Export:",
            options=[
                "🌐 All Selected Frameworks (Master Audit Report)",
                " EU GDPR Only",
                "🏥 US HIPAA Only",
                "🏦 RBI Cyber Framework Only",
                "🛡️ SOC 2 Type II Only"
            ],
            key="export_compliance_scope_selector"
        )

        scope_key_map = {
            "🌐 All Selected Frameworks (Master Audit Report)": selected_fw_keys,
            " EU GDPR Only": ["gdpr"],
            "🏥 US HIPAA Only": ["hipaa"],
            "🏦 RBI Cyber Framework Only": ["rbi"],
            "🛡️ SOC 2 Type II Only": ["soc2"]
        }
        
        export_target_keys = scope_key_map.get(export_scope_label, selected_fw_keys)
        export_payload = filter_report_payload(master_report, export_target_keys)
        
        export_company = meta.get("company_name", "Organization").replace(" ", "_")
        export_tag = "_".join(export_target_keys).upper()
        
        st.divider()
        c_left, c_right = st.columns(2)
        
        with c_left:
            report_str = json.dumps(export_payload, indent=2)
            st.download_button(
                label=f"📥 Download JSON Report ({export_scope_label.split('(')[0].strip()})",
                data=report_str,
                file_name=f"LexMesh_GapAnalysis_{export_tag}_{export_company}.json",
                mime="application/json"
            )
            
        with c_right:
            pdf_path = f"LexMesh_Report_{export_tag}_{export_company}.pdf"
            if st.button(f"📄 Render PDF Report ({export_scope_label.split('(')[0].strip()})"):
                with st.spinner("Rendering Target Compliance PDF Report..."):
                    generate_compliance_pdf(export_payload, pdf_path)
                    with open(pdf_path, "rb") as pdf_file:
                        st.download_button(
                            label="⬇️ Click to Download PDF Report",
                            data=pdf_file.read(),
                            file_name=pdf_path,
                            mime="application/pdf"
                        )
else:
    st.info("👈 Upload a company policy PDF in the sidebar and click **🚀 Run Unified Gap Analysis** to evaluate against EU GDPR, US HIPAA, RBI Cyber, and SOC 2 Type II!")
