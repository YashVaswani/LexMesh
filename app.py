"""
ComplianceIQ — Streamlit Web Interface
Interactive dashboard for document ingestion, Google ADK agentic RAG gap analysis,
live sub-agent progress monitoring, requirement filtering, and PDF export.
"""

import os
import json
import pymupdf as fitz
import streamlit as st
from config import config
from db.supabase_client import supabase_db
from agents.adk_agent import adk_supervisor
from reporter.pdf_generator import generate_compliance_pdf

st.set_page_config(
    page_title="ComplianceIQ — Google ADK Agentic RAG Gap Analysis",
    page_icon="🛡️",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS for dark/modern styling
st.markdown("""
<style>
    .main-header { font-size: 2.2rem; font-weight: 800; color: #1E3A8A; margin-bottom: 0rem; }
    .sub-header { font-size: 1rem; color: #0D9488; margin-bottom: 1.5rem; }
    .stButton>button { background-color: #2563EB; color: white; border-radius: 6px; font-weight: 600; width: 100%; }
</style>
""", unsafe_allow_html=True)

st.markdown('<div class="main-header">🛡️ ComplianceIQ</div>', unsafe_allow_html=True)
st.markdown('<div class="sub-header">Agentic RAG Engine | Google ADK Orchestration & GDPR Audit</div>', unsafe_allow_html=True)

# SIDEBAR CONFIGURATION & UPLOAD
with st.sidebar:
    st.header("⚙️ Configuration & Upload")
    
    # System Status
    st.subheader("System Health")
    st.write(f"🔹 Gemini API: {'✅ Connected' if config.GEMINI_API_KEY else '❌ Missing'}")
    st.write(f"🔹 Groq API: {'✅ Connected' if config.GROQ_API_KEY else '❌ Missing'}")
    st.write(f"🔹 Supabase DB: {'✅ Connected' if supabase_db.is_connected() else '⚠️ Offline / Local Mode'}")
    st.write(f"🔹 Orchestration: ✅ Google ADK Supervisor Active")
    
    st.divider()
    st.subheader("Document Input")
    company_name = st.text_input("Company Name", value="TechStartup Pvt Ltd")
    policy_name = st.text_input("Policy Version / Name", value="Privacy Policy v2.1")
    
    uploaded_file = st.file_uploader("Upload Company Policy PDF", type=["pdf"])
    
    run_btn = st.button("🚀 Run Google ADK Gap Analysis", disabled=(uploaded_file is None))

# MAIN CONTENT AREA
if uploaded_file and run_btn:
    st.info("Ingesting company policy PDF and initializing Google ADK Supervisor Agent...")
    
    # Extract PDF text
    pdf_bytes = uploaded_file.read()
    doc = fitz.open(stream=pdf_bytes, filetype="pdf")
    policy_text = ""
    for page in doc:
        policy_text += page.get_text() + "\n"
        
    st.success(f"Successfully extracted {len(policy_text)} characters from '{uploaded_file.name}'.")
    
    # Load requirements catalog
    sample_reqs_path = "gdpr_requirements_master.json"
    if os.path.exists(sample_reqs_path):
        with open(sample_reqs_path, 'r', encoding='utf-8') as f:
            reqs_catalog = json.load(f)
    else:
        reqs_catalog = [
            {"id": "REQ-001", "chapter_number": "II", "chapter_title": "Principles", "article_number": "Art. 5(1)(a)", "article_title": "Lawfulness, fairness & transparency", "atomic_requirement": "Personal data must be processed lawfully, fairly, and transparently"},
            {"id": "REQ-002", "chapter_number": "II", "chapter_title": "Principles", "article_number": "Art. 7(3)", "article_title": "Consent withdrawal", "atomic_requirement": "Data subject must be able to withdraw consent at any time as easily as giving consent"},
            {"id": "REQ-003", "chapter_number": "III", "chapter_title": "Rights of data subject", "article_number": "Art. 12(1)", "article_title": "Transparent communication", "atomic_requirement": "Information must be provided in concise, transparent, intelligible form"},
            {"id": "REQ-004", "chapter_number": "III", "chapter_title": "Rights of data subject", "article_number": "Art. 13(1)(e)", "article_title": "Recipient disclosure", "atomic_requirement": "Recipients or categories of recipients of data must be disclosed"},
            {"id": "REQ-005", "chapter_number": "III", "chapter_title": "Rights of data subject", "article_number": "Art. 17(1)", "article_title": "Right to erasure", "atomic_requirement": "Data subject has the right to erasure without undue delay"}
        ]
        
    with st.spinner("Google ADK Supervisor delegating policy chunks to Chapter Sub-Agents (Chapters I–XI)..."):
        report_json = adk_supervisor.run_adk_pipeline(company_name, policy_name, policy_text, reqs_catalog)
        st.session_state["active_report"] = report_json

# DISPLAY REPORT DASHBOARD IF AVAILABLE
if "active_report" in st.session_state:
    report = st.session_state["active_report"]
    meta = report.get("metadata", {})
    summary = report.get("summary", {})
    
    st.divider()
    
    # Dashboard Tabs
    tab1, tab2, tab3, tab4, tab5 = st.tabs([
        "📊 Score & Metrics", 
        "📑 Chapter Breakdown", 
        "🔍 Detailed Gaps", 
        "📋 Action Plan", 
        "📥 Report Export"
    ])
    
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
        st.table(report.get("chapter_breakdown", []))

    # TAB 3: DETAILED GAPS
    with tab3:
        st.subheader("Requirement-by-Requirement Analysis")
        filter_status = st.multiselect("Filter by Verdict", ["Fully Met", "Partially Met", "Not Met", "Conflicting"], default=["Not Met", "Partially Met"])
        
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
        
        st.error("🚨 P1 — Critical Priority")
        st.table(action_plan.get("p1_critical", []))
        
        st.warning("⚠️ P2 — High Priority")
        st.table(action_plan.get("p2_high", []))
        
        st.info("ℹ️ P3 — Medium Priority")
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
                file_name=f"GapAnalysis_{company_name}.json",
                mime="application/json"
            )
            
        with c_right:
            pdf_path = f"GapAnalysisReport_{company_name}.pdf"
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
    st.info("👈 Upload a company policy PDF in the sidebar and click **Run Google ADK Gap Analysis** to start!")
