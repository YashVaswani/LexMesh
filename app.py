"""
LexMesh — Streamlit Web Interface
Interactive dashboard for document ingestion, parallel agentic RAG gap analysis,
automatic document metadata extraction (Company Name & Policy Version),
live sub-agent progress monitoring, requirement filtering, and PDF export.
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

st.set_page_config(
    page_title="LexMesh",
    page_icon="🛡️",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS for dark/modern styling
st.markdown("""
<style>
    .main-header { font-size: 2.5rem; font-weight: 800; color: #1E3A8A; margin-bottom: 1rem; }
    .stButton>button { background-color: #2563EB; color: white; border-radius: 6px; font-weight: 600; width: 100%; }
    .legend-box { background-color: #F8FAFC; border: 1px solid #E2E8F0; padding: 10px 15px; border-radius: 6px; font-size: 0.9rem; margin-bottom: 1rem; }
</style>
""", unsafe_allow_html=True)

st.markdown('<div class="main-header">🛡️ LexMesh</div>', unsafe_allow_html=True)

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
        title_match = re.search(r"(PRIVACY POLICY|PRIVACY NOTICE|DATA PROTECTION POLICY|TERMS OF SERVICE)[^\n]*", first_page_text, re.IGNORECASE)
        ver_match = re.search(r"(v\d+\.\d+|\b\d+\.\d+\b)", first_page_text, re.IGNORECASE)

        if title_match and ver_match:
            extracted_policy_name = f"{title_match.group(0).strip().title()} {ver_match.group(0)}"
        elif title_match:
            extracted_policy_name = title_match.group(0).strip().title()
        elif ver_match:
            extracted_policy_name = f"Privacy Policy {ver_match.group(0)}"

        return extracted_company, extracted_policy_name
    except Exception:
        return "", ""

from ingestion.catalog_manager import catalog_manager, FRAMEWORKS

# SIDEBAR CONFIGURATION & UPLOAD
with st.sidebar:
    st.header("⚙️ Configuration & Upload")
    
    # System Status
    st.subheader("System Health")
    st.write(f"🔹 Gemini API: {'✅ Connected' if config.GEMINI_API_KEY else '❌ Missing'}")
    st.write(f"🔹 Groq API: {'✅ Connected' if config.GROQ_API_KEY else '❌ Missing'}")
    st.write(f"🔹 Supabase DB: {'✅ Connected' if supabase_db.is_connected() else '⚠️ Offline / Local Mode'}")
    st.write(f"🔹 Orchestration: ✅ Google ADK Supervisor Active (Parallel Pool)")
    
    st.divider()
    st.subheader("1. Compliance Standard")
    
    fw_options = {
        "🇪🇺 EU GDPR": "gdpr",
        "🏥 US HIPAA": "hipaa",
        "🏦 RBI Cyber Framework": "rbi",
        "🛡️ SOC 2 Type II": "soc2"
    }
    selected_fw_label = st.selectbox("Select Target Framework", list(fw_options.keys()))
    selected_fw_id = fw_options[selected_fw_label]
    fw_info = catalog_manager.get_framework_info(selected_fw_id)

    st.caption(f"**Selected Standard:** {fw_info['full_name']}")

    st.divider()
    st.subheader("2. Document Input")
    
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
        # Clear all session state metadata when file is removed (cross button clicked)
        st.session_state.pop("last_uploaded_file_id", None)
        st.session_state.pop("company_name_input", None)
        st.session_state.pop("policy_name_input", None)
        auto_company = ""
        auto_policy = ""

    company_name = st.text_input("Company Name", value=auto_company, placeholder="e.g. TechStartup Pvt Ltd")
    policy_name = st.text_input("Policy Version / Name", value=auto_policy, placeholder="e.g. Privacy Policy v2.1")
    
    run_btn = st.button("🚀 Run Gap Analysis", disabled=(uploaded_file is None))

# MAIN CONTENT AREA
if uploaded_file and run_btn and pdf_bytes:
    # Use fallback company/policy name if user leaves text input blank
    final_company = company_name.strip() if company_name.strip() else "Uploaded Organization"
    final_policy = policy_name.strip() if policy_name.strip() else "Privacy Policy Document"

    st.info(f"Ingesting company policy PDF for **{fw_info['name']}** and initializing Parallel Sub-Agents...")
    
    # Extract PDF text
    doc = fitz.open(stream=pdf_bytes, filetype="pdf")
    policy_text = ""
    for page in doc:
        policy_text += page.get_text() + "\n"
        
    st.success(f"Successfully extracted {len(policy_text)} characters from '{uploaded_file.name}'.")
    
    # Load requirements catalog dynamically for selected framework
    reqs_catalog = catalog_manager.load_catalog(selected_fw_id)
    if not reqs_catalog:
        st.warning(f"Catalog for {fw_info['name']} was empty or missing. Loading default GDPR catalog.")
        reqs_catalog = catalog_manager.load_catalog("gdpr")
        
    with st.spinner(f"Running Parallel Gap Analysis under {fw_info['name']}..."):
        report_json = adk_supervisor.run_adk_pipeline(final_company, final_policy, policy_text, reqs_catalog, framework_id=selected_fw_id)
        st.session_state["active_report"] = report_json

# DISPLAY REPORT DASHBOARD IF AVAILABLE
if "active_report" in st.session_state:
    report = st.session_state["active_report"]
    meta = report.get("metadata", {})
    summary = report.get("summary", {})
    
    st.divider()
    
    # Dashboard Tabs with Key Persistence
    tab1, tab2, tab3, tab4, tab5 = st.tabs(
        [
            "📊 Score & Metrics", 
            "📑 Chapter Breakdown", 
            "🔍 Detailed Gaps", 
            "📋 Action Plan", 
            "📥 Report Export"
        ],
        key="active_dashboard_tab"
    )
    
    # TAB 1: OVERVIEW METRICS
    with tab1:
        col1, col2, col3, col4, col5 = st.columns(5)
        counts = summary.get("verdict_counts", {})
        col1.metric("Overall Score", f"{summary.get('overall_score', 0)}%")
        col2.metric("✓ Fully Met", counts.get("fully_met", 0))
        col3.metric("■ Partially Met", counts.get("partially_met", 0))
        col4.metric("✗ Not Met", counts.get("not_met", 0))
        col5.metric("■ Conflicting", counts.get("conflicting", 0))
        
        st.error(f"**RISK ASSESSMENT:** {summary.get('risk_level', 'HIGH RISK')}")
        st.warning(f"**FINE EXPOSURE:** {summary.get('max_fine_exposure', '€20M or 4% annual revenue')}")

    # TAB 2: CHAPTER BREAKDOWN
    with tab2:
        st.subheader("Chapter-by-Chapter Compliance Posture")
        
        # Legend Callout Box
        st.markdown("""
        <div class="legend-box">
            <b>📌 Status Legend:</b> &nbsp;&nbsp;
            <span>🟢 <b>Compliant</b> (Score ≥ 65%) — High policy alignment</span> &nbsp;|&nbsp;
            <span>🟡 <b>Partial</b> (Score 35%–64%) — Operational gaps exist</span> &nbsp;|&nbsp;
            <span>🔴 <b>Non-Compliant</b> (Score &lt; 35%) — Critical omissions</span>
        </div>
        """, unsafe_allow_html=True)
        
        st.table(report.get("chapter_breakdown", []))

    # TAB 3: DETAILED GAPS
    with tab3:
        st.subheader("Requirement-by-Requirement Analysis")
        filter_status = st.multiselect(
            "Filter by Verdict", 
            ["Fully Met", "Partially Met", "Not Met", "Conflicting"], 
            default=["Not Met", "Partially Met", "Conflicting"],
            key="gap_verdict_filter"
        )
        
        for gap in report.get("detailed_gaps", []):
            if filter_status and gap.get("verdict") not in filter_status:
                continue
                
            with st.expander(f"[{gap.get('requirement_id')}] {gap.get('article')} — {gap.get('verdict')}"):
                st.write(f"**GDPR Requirement:** {gap.get('gdpr_requires')}")
                st.write(f"**Your Policy Citation:** {gap.get('your_policy')}")
                st.write(f"**Analysis Reasoning:** {gap.get('analysis')}")
                st.info(f"**Fix Required:** {gap.get('fix_required')}")

    # TAB 4: ACTION PLAN
    with tab4:
        st.subheader("Priority Action Plan")
        action_plan = report.get("priority_action_plan", {})
        
        st.error("🚨 P1 — Critical Priority (Immediate Action Required)")
        st.table(action_plan.get("p1_critical", []))
        
        st.warning("⚠️ P2 — High Priority (Operational Fixes)")
        st.table(action_plan.get("p2_high", []))
        
        st.info("ℹ️ P3 — Medium Priority (Maintenance & Review)")
        st.table(action_plan.get("p3_medium", []))

    # TAB 5: REPORT EXPORT
    with tab5:
        st.subheader("Executive Summary")
        st.write(report.get("executive_summary", ""))
        
        st.divider()
        st.subheader("Export Formats")
        
        c_left, c_right = st.columns(2)
        
        with c_left:
            report_str = json.dumps(report, indent=2)
            st.download_button(
                label="📥 Download JSON Report",
                data=report_str,
                file_name=f"GapAnalysis_{company_name or 'Report'}.json",
                mime="application/json"
            )
            
        with c_right:
            pdf_path = f"GapAnalysisReport_{company_name or 'Report'}.pdf"
            if st.button("📄 Export to PDF"):
                with st.spinner("Rendering PDF..."):
                    generate_compliance_pdf(report, pdf_path)
                    with open(pdf_path, "rb") as pdf_file:
                        st.download_button(
                            label="⬇️ Click to Download PDF",
                            data=pdf_file.read(),
                            file_name=pdf_path,
                            mime="application/pdf"
                        )
else:
    st.info("👈 Upload a company policy PDF in the sidebar and click **Run Gap Analysis** to start!")
