import json
import re
import warnings
from pathlib import Path

# Suppress SDK deprecation warnings in application output logs
warnings.filterwarnings("ignore")

import pymupdf as fitz
from nicegui import app, ui

from config import config
from db.supabase_client import supabase_db
from agents.adk_agent import adk_supervisor
from logger import get_logger

logger = get_logger("app")

from ui.components.header import create_header
from ui.components.sidebar import create_sidebar
from ui.components.score_cards import create_score_cards
from ui.components.policy_posture import create_policy_posture
from ui.components.gap_analysis import create_gap_analysis
from ui.components.action_plan import create_action_plan
from ui.components.compliant_areas import create_compliant_areas
from ui.components.report_export import create_report_export
from ui.components.lucide import lucide_icon

# Load Custom Enterprise Theme CSS & Lucide Icons CDN
theme_css_path = Path(__file__).parent / "ui" / "styles" / "theme.css"
if theme_css_path.exists():
    ui.add_head_html(f"<style>{theme_css_path.read_text(encoding='utf-8')}</style>", shared=True)

ui.add_head_html('''
<script src="https://unpkg.com/lucide@latest"></script>
<script>
    document.addEventListener("DOMContentLoaded", () => {
        if (window.lucide) lucide.createIcons();
    });
</script>
''', shared=True)

# OpenGraph & SEO Meta Tags — rich link previews when shared on Slack/WhatsApp/LinkedIn
ui.add_head_html('''
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<meta name="description" content="LexMesh — AI-powered multi-framework compliance engine for GDPR, HIPAA, RBI, and SOC 2. Upload your policy PDF and get instant gap analysis with a prioritised action plan.">
<meta name="keywords" content="compliance, GDPR, HIPAA, SOC2, RBI, AI compliance, policy analysis, LexMesh">
<meta name="author" content="LexMesh">

<!-- OpenGraph -->
<meta property="og:type" content="website">
<meta property="og:title" content="LexMesh — AI-Powered Compliance Engine">
<meta property="og:description" content="Instantly audit your company policy PDF against GDPR, HIPAA, RBI &amp; SOC 2 with AI-powered multi-framework gap analysis and a prioritised action plan.">
<meta property="og:image" content="https://placehold.co/1200x630/101713/eae3d2?text=LexMesh+Compliance+Engine">
<meta property="og:site_name" content="LexMesh">

<!-- Twitter Card -->
<meta name="twitter:card" content="summary_large_image">
<meta name="twitter:title" content="LexMesh — AI-Powered Compliance Engine">
<meta name="twitter:description" content="Upload your policy PDF. Get instant GDPR, HIPAA, RBI &amp; SOC 2 compliance scores, gap analysis, and a prioritised action plan.">
<meta name="twitter:image" content="https://placehold.co/1200x630/101713/eae3d2?text=LexMesh+Compliance+Engine">
''', shared=True)


# ============================================================
# FRAMEWORKS
# ============================================================

FRAMEWORKS = {
    "All Standards (Full Scope)": [
        "gdpr",
        "hipaa",
        "rbi",
        "soc2",
    ],

    "EU GDPR": [
        "gdpr",
    ],

    "US HIPAA": [
        "hipaa",
    ],

    "RBI Cyber Framework": [
        "rbi",
    ],

    "SOC 2 Type II": [
        "soc2",
    ],
}


# ============================================================
# LOAD CUSTOM CSS
# ============================================================

theme_path = Path("ui/styles/theme.css")

if theme_path.exists():

    theme_css = theme_path.read_text(
        encoding="utf-8"
    )

    ui.add_head_html(
        f"<style>{theme_css}</style>",
        shared=True,
    )


@ui.page("/login")
def login_page():
    if auth.get_current_user():
        ui.navigate.to('/')
        return
        
    ui.colors(primary='#558b63', secondary='#34d399', accent='#059669', positive='#558b63')

    # Main wrapper with gradient background to mimic the design
    with ui.column().classes("w-full h-screen items-center justify-center relative overflow-hidden").style("background: linear-gradient(135deg, #f3f8f4 0%, #e8f2ea 100%);"):
        
        # Decorative circles (optional, just for background vibe)
        ui.element('div').classes('absolute top-[-10%] left-[-10%] w-[40%] h-[40%] rounded-full opacity-30 blur-3xl bg-[#d1e8d6]')
        ui.element('div').classes('absolute bottom-[-10%] right-[-10%] w-[50%] h-[50%] rounded-full opacity-30 blur-3xl bg-[#cce3d2]')

        with ui.card().classes("w-96 p-10 items-center shadow-[0_15px_40px_-5px_rgba(78,121,93,0.4)] border-2 border-[#4e795d]/60 rounded-3xl bg-[#f8f6f0]/95 backdrop-blur-sm z-10 gap-0"):
            
            # Shield Icon in a circle
            with ui.element('div').classes('w-16 h-16 rounded-full bg-emerald-50 flex items-center justify-center mb-4'):
                from ui.components.lucide import lucide_icon
                lucide_icon("shield", size=32, class_name="text-emerald-500")
            
            # Titles
            ui.label("LexMesh").classes("text-3xl font-bold text-slate-800 tracking-tight mb-1")
            ui.label("Sign in to your account").classes("text-sm text-slate-500 font-medium mb-8")
            
            # Form Container
            with ui.column().classes("w-full gap-4"):
                # Email Input
                email = ui.input("Email").classes("w-full text-md").props('outlined rounded bg-color="white" color="emerald"')
                with email.add_slot('prepend'):
                    ui.icon('mail_outline').classes('text-slate-400')
                
                # Password Input
                password = ui.input("Password", password=True, password_toggle_button=True).classes("w-full text-md").props('outlined rounded bg-color="white" color="emerald"')
                with password.add_slot('prepend'):
                    ui.icon('lock_outline').classes('text-slate-400')
                
                # Login Action
                def do_login():
                    if not email.value or not password.value:
                        ui.notify("Please enter both email and password.", type="warning")
                        return
                    success, msg = auth.sign_in(email.value, password.value)
                    if success:
                        ui.notify("Logged in successfully!", type="positive")
                        ui.navigate.to('/')
                    else:
                        ui.notify(msg, type="negative")

                ui.button("LOG IN", on_click=do_login).classes("w-full mt-2 h-12 rounded-lg font-bold text-white shadow-lg shadow-emerald-500/30 tracking-wider").props("color=primary unelevated icon-right=arrow_forward")
            
            # Footer Divider
            with ui.row().classes("w-full items-center justify-center mt-8 gap-3"):
                ui.element('div').classes("h-px bg-slate-200 flex-grow")
                with ui.row().classes("items-center gap-1 text-sm font-medium"):
                    ui.label("Don't have an account?").classes("text-slate-500")
                    ui.link("Sign Up", "/signup").classes("text-emerald-600 hover:text-emerald-700 transition-colors")
                ui.element('div').classes("h-px bg-slate-200 flex-grow")

@ui.page("/signup")
def signup_page():
    if auth.get_current_user():
        ui.navigate.to('/')
        return
        
    ui.colors(primary='#558b63', secondary='#34d399', accent='#059669', positive='#558b63')

    # Main wrapper with gradient background
    with ui.column().classes("w-full h-screen items-center justify-center relative overflow-hidden").style("background: linear-gradient(135deg, #f3f8f4 0%, #e8f2ea 100%);"):
        
        ui.element('div').classes('absolute top-[-10%] left-[-10%] w-[40%] h-[40%] rounded-full opacity-30 blur-3xl bg-[#d1e8d6]')
        ui.element('div').classes('absolute bottom-[-10%] right-[-10%] w-[50%] h-[50%] rounded-full opacity-30 blur-3xl bg-[#cce3d2]')

        with ui.card().classes("w-96 p-10 items-center shadow-[0_15px_40px_-5px_rgba(78,121,93,0.4)] border-2 border-[#4e795d]/60 rounded-3xl bg-[#f8f6f0]/95 backdrop-blur-sm z-10 gap-0"):
            
            with ui.element('div').classes('w-16 h-16 rounded-full bg-emerald-50 flex items-center justify-center mb-4'):
                from ui.components.lucide import lucide_icon
                lucide_icon("shield", size=32, class_name="text-emerald-500")
            
            ui.label("LexMesh").classes("text-3xl font-bold text-slate-800 tracking-tight mb-1")
            ui.label("Create a new account").classes("text-sm text-slate-500 font-medium mb-8")
            
            with ui.column().classes("w-full gap-4"):
                email = ui.input("Email").classes("w-full text-md").props('outlined rounded bg-color="white" color="emerald"')
                with email.add_slot('prepend'):
                    ui.icon('mail_outline').classes('text-slate-400')
                
                password = ui.input("Password", password=True, password_toggle_button=True).classes("w-full text-md").props('outlined rounded bg-color="white" color="emerald"')
                with password.add_slot('prepend'):
                    ui.icon('lock_outline').classes('text-slate-400')
                
                def do_signup():
                    if not email.value or not password.value:
                        ui.notify("Please enter both email and password.", type="warning")
                        return
                    if len(password.value) < 6:
                        ui.notify("Password must be at least 6 characters.", type="warning")
                        return
                    success, msg = auth.sign_up(email.value, password.value)
                    if success:
                        ui.notify("Signed up successfully! Welcome to LexMesh.", type="positive")
                        ui.navigate.to('/')
                    else:
                        ui.notify(msg, type="negative")

                ui.button("SIGN UP", on_click=do_signup).classes("w-full mt-2 h-12 rounded-lg font-bold text-white shadow-lg shadow-emerald-500/30 tracking-wider").props("color=primary unelevated icon-right=person_add")
            
            with ui.row().classes("w-full items-center justify-center mt-8 gap-3"):
                ui.element('div').classes("h-px bg-slate-200 flex-grow")
                with ui.row().classes("items-center gap-1 text-sm font-medium"):
                    ui.label("Already have an account?").classes("text-slate-500")
                    ui.link("Log In", "/login").classes("text-emerald-600 hover:text-emerald-700 transition-colors")
                ui.element('div').classes("h-px bg-slate-200 flex-grow")

# ============================================================
# DASHBOARD
# ============================================================

@ui.page("/")
def dashboard():
    if not auth.get_current_user():
        ui.navigate.to('/login')
        return


    # Set Quasar Brand Colors for this page
    ui.colors(
        primary='#4e795d',
        secondary='#eae3d2',
        accent='#8a7642',
        dark='#101713',
        positive='#3b6349',
        negative='#9e3232',
        info='#3b6b78',
        warning='#b45339',
    )

    # ========================================================
    # PAGE STATE
    #
    # IMPORTANT:
    # This state belongs to THIS browser page/session.
    # ========================================================

    page_state = {
        "pdf_bytes": None,
        "pdf_name": "",
        "master_report": None,
        "selected_frameworks": [
            "gdpr",
            "hipaa",
            "rbi",
            "soc2",
        ],
    }

    # ========================================================
    # HEADER
    # ========================================================

    create_header()

    # ========================================================
    # SIDEBAR
    # ========================================================

    sidebar = create_sidebar(

        gemini_connected=bool(
            config.GEMINI_API_KEY
        ),

        groq_connected=bool(
            config.GROQ_API_KEY
        ),

        supabase_connected=bool(
            supabase_db.is_connected()
        ),
    )

    # ========================================================
    # MAIN CONTENT
    # ========================================================

    with ui.column().classes(
        "w-full p-6 gap-5"
    ):

        # ----------------------------------------------------
        # TITLE
        # ----------------------------------------------------

        with ui.column().classes(
            "gap-1"
        ):

            ui.label(
                "LexMesh Compliance Dashboard"
            ).classes(
                "text-3xl font-bold lex-page-title"
            )

            ui.label(
                "Policy-Centric Multi-Framework Compliance Engine"
            ).classes(
                "text-sm lex-page-subtitle"
            )

        # ----------------------------------------------------
        # STATUS
        # ----------------------------------------------------

        status = ui.label(
            "Upload a company policy PDF to begin."
        ).classes(
            "lex-analysis-status"
        )

        # ====================================================
        # HORIZONTAL TABS
        # ====================================================

        with ui.tabs().classes(
            "w-full lex-dashboard-tabs"
        ) as tabs:

            with ui.tab("score", label="").classes("lex-tab-item"):
                with ui.row().classes("items-center gap-2"):
                    lucide_icon("bar-chart-3", size=18)
                    ui.label("Score & Framework")

            with ui.tab("posture", label="").classes("lex-tab-item"):
                with ui.row().classes("items-center gap-2"):
                    lucide_icon("file-check", size=18)
                    ui.label("Executive Posture")

            with ui.tab("gaps", label="").classes("lex-tab-item"):
                with ui.row().classes("items-center gap-2"):
                    lucide_icon("shield-alert", size=18)
                    ui.label("Detailed Policy Gaps")

            with ui.tab("action", label="").classes("lex-tab-item"):
                with ui.row().classes("items-center gap-2"):
                    lucide_icon("clipboard-list", size=18)
                    ui.label("Priority Action Plan")

            with ui.tab("compliant", label="").classes("lex-tab-item"):
                with ui.row().classes("items-center gap-2"):
                    lucide_icon("check-circle", size=18)
                    ui.label("Compliant Areas")

            with ui.tab("export", label="").classes("lex-tab-item"):
                with ui.row().classes("items-center gap-2"):
                    lucide_icon("file-down", size=18)
                    ui.label("Report Export")

        # ====================================================
        # TAB PANELS
        # ====================================================

        with ui.tab_panels(
            tabs,
            value="score",
        ).classes(
            "w-full"
        ):

            # =================================================
            # SCORE TAB
            # =================================================

            with ui.tab_panel(
                "score"
            ):

                with ui.column().classes("w-full") as score_container:

                    ui.label(
                        "Upload a company policy PDF and click Run Analysis to view compliance scores."
                    ).classes(
                        "lex-empty-state"
                    )

            # =================================================
            # POLICY POSTURE
            # =================================================

            with ui.tab_panel(
                "posture"
            ):

                with ui.column().classes("w-full") as posture_container:

                    ui.label(
                        "Run an analysis to view policy posture."
                    ).classes(
                        "lex-empty-state"
                    )

            # =================================================
            # DETAILED GAPS
            # =================================================

            with ui.tab_panel(
                "gaps"
            ):

                with ui.column().classes("w-full") as gap_container:

                    ui.label(
                        "Run an analysis to view detailed gaps."
                    ).classes(
                        "lex-empty-state"
                    )

            # =================================================
            # ACTION PLAN
            # =================================================

            with ui.tab_panel(
                "action"
            ):

                with ui.column().classes("w-full") as action_container:

                    ui.label(
                        "Run an analysis to view the action plan."
                    ).classes(
                        "lex-empty-state"
                    )

            with ui.tab_panel(
                "compliant"
            ):

                with ui.column().classes("w-full") as compliant_container:

                    ui.label(
                        "Run an analysis to view compliant areas."
                    ).classes(
                        "lex-empty-state"
                    )

            # =================================================
            # EXPORT
            # =================================================

            with ui.tab_panel(
                "export"
            ):

                with ui.column().classes("w-full") as export_container:

                    ui.label(
                        "Run an analysis to enable exports."
                    ).classes(
                        "lex-empty-state"
                    )

    # ========================================================
    # PDF METADATA EXTRACTION
    # ========================================================

    def extract_metadata_from_pdf(
        pdf_bytes: bytes,
    ):

        try:

            doc = fitz.open(
                stream=pdf_bytes,
                filetype="pdf",
            )

            if len(doc) == 0:
                return "", ""

            first_page_text = (
                doc[0].get_text()
            )

            company = ""
            policy = ""

            # ------------------------------------------------
            # COMPANY
            # ------------------------------------------------

            company_match = re.search(
                r"Company\s*[:\t]?\s*([^\n\r]+)",
                first_page_text,
                re.IGNORECASE,
            )

            if company_match:

                company = (
                    company_match
                    .group(1)
                    .strip()
                )

            else:

                company_match = re.search(
                    r"([A-Za-z0-9\s&]+"
                    r"(?:Pvt Ltd|Ltd|Inc|Corp|"
                    r"Corporation|Technologies|"
                    r"Systems|AI))",
                    first_page_text,
                )

                if company_match:

                    company = (
                        company_match
                        .group(1)
                        .strip()
                    )

            # ------------------------------------------------
            # POLICY NAME
            # ------------------------------------------------

            title_match = re.search(
                r"(PRIVACY POLICY|PRIVACY NOTICE|"
                r"DATA PROTECTION POLICY|"
                r"INFORMATION SECURITY POLICY|"
                r"ACCESS CONTROL POLICY|"
                r"INCIDENT RESPONSE PLAN|"
                r"TERMS OF SERVICE)[^\n]*",
                first_page_text,
                re.IGNORECASE,
            )

            # ------------------------------------------------
            # VERSION
            # ------------------------------------------------

            version_match = re.search(
                r"(v\d+\.\d+|\b\d+\.\d+\b)",
                first_page_text,
                re.IGNORECASE,
            )

            if (
                title_match
                and version_match
            ):

                policy = (
                    f"{title_match.group(0).strip().title()} "
                    f"{version_match.group(0)}"
                )

            elif title_match:

                policy = (
                    title_match
                    .group(0)
                    .strip()
                    .title()
                )

            elif version_match:

                policy = (
                    f"Enterprise Policy "
                    f"{version_match.group(0)}"
                )

            return company, policy

        except Exception as e:

            print(
                "[LexMesh] Metadata extraction error:",
                e,
            )

            return "", ""

    # ========================================================
    # REPORT FILTER
    # ========================================================

    def filter_report_payload(
        report_json,
        target_fw_keys,
    ):

        # All frameworks selected
        if (
            not target_fw_keys
            or set(target_fw_keys)
            == {
                "gdpr",
                "hipaa",
                "rbi",
                "soc2",
            }
        ):

            return report_json

        filtered = json.loads(
            json.dumps(report_json)
        )

        # ----------------------------------------------------
        # SUMMARY
        # ----------------------------------------------------

        summary = filtered.setdefault(
            "summary",
            {},
        )

        framework_summaries = (
            summary.get(
                "framework_summaries",
                {},
            )
        )

        selected_summaries = {
            key: value
            for key, value in framework_summaries.items()
            if key in target_fw_keys
        }

        summary[
            "framework_summaries"
        ] = selected_summaries

        # ----------------------------------------------------
        # OVERALL SCORE
        # ----------------------------------------------------

        scores = []

        for value in selected_summaries.values():

            try:

                score = float(
                    str(
                        value.get(
                            "score",
                            0,
                        )
                    ).replace(
                        "%",
                        "",
                    )
                )

                scores.append(score)

            except Exception:
                pass

        if scores:

            overall_score = int(
                round(
                    sum(scores)
                    / len(scores)
                )
            )

            summary[
                "overall_score"
            ] = overall_score

            if overall_score >= 80:

                summary[
                    "overall_risk"
                ] = (
                    "LOW RISK — "
                    "High Compliance Posture"
                )

            elif overall_score >= 60:

                summary[
                    "overall_risk"
                ] = (
                    "MEDIUM RISK — "
                    "Operational Gaps Exist"
                )

            else:

                summary[
                    "overall_risk"
                ] = (
                    "HIGH RISK — "
                    "Critical Compliance Omissions"
                )

        # ----------------------------------------------------
        # POLICY DOMAIN BREAKDOWN
        # ----------------------------------------------------

        domains = filtered.get(
            "policy_domain_breakdown",
            [],
        )

        for domain in domains:

            framework_scores = (
                domain.get(
                    "framework_scores",
                    {},
                )
            )

            selected_scores = {
                key: value
                for key, value in framework_scores.items()
                if key in target_fw_keys
            }

            domain[
                "framework_scores"
            ] = selected_scores

            if selected_scores:

                values = []

                for value in selected_scores.values():

                    try:

                        values.append(
                            float(
                                str(value)
                                .replace(
                                    "%",
                                    "",
                                )
                            )
                        )

                    except Exception:
                        pass

                if values:

                    domain[
                        "score"
                    ] = (
                        f"{int(round(sum(values) / len(values)))}%"
                    )

        # ----------------------------------------------------
        # DETAILED GAPS
        # ----------------------------------------------------

        detailed_gaps = (
            filtered.get(
                "detailed_policy_gaps",
                {},
            )
        )

        for domain_data in detailed_gaps.values():

            framework_gaps = (
                domain_data.get(
                    "framework_gaps",
                    {},
                )
            )

            domain_data[
                "framework_gaps"
            ] = {
                key: value
                for key, value in framework_gaps.items()
                if key in target_fw_keys
            }

        # ----------------------------------------------------
        # FLAT GAPS
        # ----------------------------------------------------

        all_gaps = filtered.get(
            "all_gaps_flat",
            filtered.get(
                "detailed_gaps",
                [],
            ),
        )

        filtered[
            "all_gaps_flat"
        ] = [
            gap
            for gap in all_gaps
            if gap.get(
                "framework"
            ) in target_fw_keys
        ]

        # ----------------------------------------------------
        # ACTION PLAN
        # ----------------------------------------------------

        plan = filtered.get(
            "priority_action_plan",
            {},
        )

        def matches_framework(item):

            tag = str(
                item.get(
                    "Framework Standard",
                    item.get(
                        "framework_tag",
                        "",
                    ),
                )
            ).lower()

            for framework in target_fw_keys:

                if (
                    framework == "gdpr"
                    and "gdpr" in tag
                ):
                    return True

                if (
                    framework == "hipaa"
                    and "hipaa" in tag
                ):
                    return True

                if (
                    framework == "rbi"
                    and "rbi" in tag
                ):
                    return True

                if (
                    framework == "soc2"
                    and (
                        "soc2" in tag
                        or "soc" in tag
                    )
                ):
                    return True

            return False

        filtered[
            "priority_action_plan"
        ] = {

            "p1_critical": [
                item
                for item in plan.get(
                    "p1_critical",
                    [],
                )
                if matches_framework(item)
            ],

            "p2_high": [
                item
                for item in plan.get(
                    "p2_high",
                    [],
                )
                if matches_framework(item)
            ],

            "p3_medium": [
                item
                for item in plan.get(
                    "p3_medium",
                    [],
                )
                if matches_framework(item)
            ],
        }

        # ----------------------------------------------------
        # COMPLIANT AREAS
        # ----------------------------------------------------
        comp_areas = filtered.get("compliant_areas", [])
        filtered["compliant_areas"] = [
            item
            for item in comp_areas
            if matches_framework(item)
        ]

        return filtered

    # ========================================================
    # UPLOAD CALLBACK
    #
    # IMPORTANT:
    # Use NiceGUI's dedicated .on_upload().
    # ========================================================

    async def handle_upload(event):

        try:

            print()
            print(
                "=========================================="
            )
            print(
                "[LexMesh] UPLOAD EVENT RECEIVED"
            )
            print(
                "=========================================="
            )

            uploaded_file = event.file

            if uploaded_file is None:

                raise ValueError(
                    "NiceGUI did not provide an uploaded file."
                )

            print(
                "[LexMesh] File:",
                uploaded_file.name,
            )

            # ------------------------------------------------
            # READ FILE
            # ------------------------------------------------

            pdf_data = await uploaded_file.read()

            if pdf_data is None:

                raise ValueError(
                    "Uploaded file returned no data."
                )

            pdf_data = bytes(
                pdf_data
            )

            if len(pdf_data) == 0:

                raise ValueError(
                    "Uploaded PDF is empty."
                )

            # ------------------------------------------------
            # SAVE TO PAGE STATE
            # ------------------------------------------------

            page_state[
                "pdf_bytes"
            ] = pdf_data

            page_state[
                "pdf_name"
            ] = uploaded_file.name

            print(
                "[LexMesh] PDF bytes:",
                len(pdf_data),
            )

            # ------------------------------------------------
            # TRY METADATA EXTRACTION
            # ------------------------------------------------

            company, policy = (
                extract_metadata_from_pdf(
                    pdf_data
                )
            )

            print(
                "[LexMesh] Extracted company:",
                company,
            )

            print(
                "[LexMesh] Extracted policy:",
                policy,
            )

            # ------------------------------------------------
            # POPULATE INPUTS
            # ------------------------------------------------

            if company:

                sidebar[
                    "company_name"
                ].value = company

            if policy:

                sidebar[
                    "policy_name"
                ].value = policy

            # ------------------------------------------------
            # SUCCESS
            # ------------------------------------------------

            status.set_text(
                f"Document {uploaded_file.name} uploaded and ready for analysis."
            )

            ui.notify(
                "PDF uploaded successfully. "
                "Click Run Unified Gap Analysis.",
                type="positive",
            )

            logger.info("PDF ready for analysis: %s (%d bytes)", page_state['pdf_name'], len(pdf_bytes))

        except Exception as e:

            page_state["pdf_bytes"] = None
            page_state["pdf_name"] = ""

            status.set_text(f"❌ Upload failed: {e}")

            ui.notify(
                f"Upload failed: {e}",
                type="negative",
            )

            logger.error("PDF upload error: %s", e, exc_info=True)

    # --------------------------------------------------------
    # THIS IS THE IMPORTANT CHANGE
    # --------------------------------------------------------

    sidebar[
        "uploaded_file"
    ].on_upload(
        handle_upload
    )

    # ========================================================
    # RUN ANALYSIS
    # ========================================================

    async def run_analysis():

        logger.info("=== RUN ANALYSIS TRIGGERED ===")

        # ----------------------------------------------------
        # GET CURRENT PAGE PDF
        # ----------------------------------------------------

        pdf_bytes = page_state.get(
            "pdf_bytes"
        )

        logger.debug(
            "PDF state: %s (%d bytes)",
            "AVAILABLE" if pdf_bytes else "EMPTY",
            len(pdf_bytes) if pdf_bytes else 0,
        )

        # ----------------------------------------------------
        # CHECK PDF
        # ----------------------------------------------------

        if (
            pdf_bytes is None
            or len(pdf_bytes) == 0
        ):

            status.set_text(
                "Please upload a company policy PDF document first."
            )

            ui.notify(
                "Please upload a PDF first.",
                type="warning",
            )

            return

        button = sidebar[
            "run_button"
        ]

        button.disable()

        try:

            # =================================================
            # COMPANY
            # =================================================

            company = (
                sidebar[
                    "company_name"
                ].value
                or "Uploaded Organization"
            ).strip()

            # =================================================
            # POLICY
            # =================================================

            policy = (
                sidebar[
                    "policy_name"
                ].value
                or "Company Policy Document"
            ).strip()

            # =================================================
            # FRAMEWORK
            # =================================================

            selected_fw_keys = []
            if sidebar["gdpr_checkbox"].value:
                selected_fw_keys.append("gdpr")
            if sidebar["hipaa_checkbox"].value:
                selected_fw_keys.append("hipaa")
            if sidebar["rbi_checkbox"].value:
                selected_fw_keys.append("rbi")
            if sidebar["soc2_checkbox"].value:
                selected_fw_keys.append("soc2")

            if not selected_fw_keys:
                status.set_text("Please select at least one evaluation framework in the sidebar.")
                ui.notify("Please select at least one framework.", type="warning")
                button.enable()
                return

            page_state[
                "selected_frameworks"
            ] = selected_fw_keys

            logger.info(
                "Analysis requested — Company: %s | Policy: %s | Frameworks: %s",
                company, policy, selected_fw_keys,
            )

            # =================================================
            # EXTRACT POLICY TEXT
            # =================================================

            status.set_text(
                "📖 Reading policy PDF..."
            )

            logger.info("Opening PDF for text extraction...")

            doc = fitz.open(
                stream=pdf_bytes,
                filetype="pdf",
            )

            policy_pages = []

            for page in doc:

                text = page.get_text()

                if text:

                    policy_pages.append(
                        text
                    )

            doc.close()

            policy_text = "\n".join(
                policy_pages
            )

            logger.info("Extracted %d characters from policy PDF.", len(policy_text))

            if not policy_text.strip():

                raise ValueError(
                    "No readable text was found "
                    "inside the uploaded PDF."
                )

            # =================================================
            # RUN REAL ADK PIPELINE
            # =================================================

            status.set_text(
                "Running LexMesh compliance analysis..."
            )

            logger.info("Calling ADK pipeline...")
            import asyncio
            import functools
            func = functools.partial(
                adk_supervisor.run_adk_pipeline,
                company,
                policy,
                policy_text,
                active_frameworks=selected_fw_keys,
                user_id=auth.get_current_user()
            )
            master_report = await asyncio.get_event_loop().run_in_executor(None, func)

            # =================================================
            # VALIDATE REPORT
            # =================================================

            if master_report is None:

                raise ValueError(
                    "ADK pipeline returned None."
                )

            if not isinstance(
                master_report,
                dict,
            ):

                raise TypeError(
                    "ADK pipeline returned "
                    f"{type(master_report).__name__}, "
                    "expected dict."
                )

            page_state[
                "master_report"
            ] = master_report

            logger.info(
                "ADK pipeline completed. Report keys: %s",
                list(master_report.keys()),
            )

            # =================================================
            # APPLY FRAMEWORK FILTER
            # =================================================

            report = filter_report_payload(
                master_report,
                selected_fw_keys,
            )

            # =================================================
            # CLEAR OLD UI (Safely handle client disconnects)
            # =================================================

            try:
                score_container.clear()
                posture_container.clear()
                gap_container.clear()
                action_container.clear()
                compliant_container.clear()
                export_container.clear()
            except RuntimeError as e:
                if "client this element belongs to has been deleted" in str(e):
                    logger.warning("Client session ended during analysis. Skipping UI update.")
                    return
                raise e

            # =================================================
            # SCORE TAB
            # =================================================

            with score_container:

                summary = report.get(
                    "summary",
                    {},
                )

                framework_summaries = (
                    summary.get(
                        "framework_summaries",
                        {},
                    )
                )

                create_score_cards(
                    summary=summary,
                    framework_summaries=framework_summaries,
                    selected_fw_keys=selected_fw_keys,
                )

            # =================================================
            # POLICY POSTURE
            # =================================================

            with posture_container:

                create_policy_posture(
                    report
                )

            # =================================================
            # DETAILED GAPS
            # =================================================

            with gap_container:

                create_gap_analysis(
                    report
                )

            # =================================================
            # ACTION PLAN
            # =================================================

            with action_container:

                create_action_plan(
                    report
                )

            # =================================================
            # COMPLIANT AREAS
            # =================================================

            with compliant_container:

                create_compliant_areas(
                    report
                )

            # =================================================
            # EXPORT
            # =================================================

            with export_container:

                create_report_export(
                    report=report,
                    company=company,
                )

            # =================================================
            # SUCCESS
            # =================================================

            # Trace overall score
            _summary_obj = report.get("summary", {})
            logger.debug(
                "Summary keys: %s | overall_score: %s | framework scores: %s",
                list(_summary_obj.keys()) if isinstance(_summary_obj, dict) else type(_summary_obj),
                repr(_summary_obj.get("overall_score")) if isinstance(_summary_obj, dict) else "N/A",
                {
                    k: v.get("score") if isinstance(v, dict) else v
                    for k, v in _summary_obj.get("framework_summaries", {}).items()
                } if isinstance(_summary_obj, dict) else "N/A",
            )

            score = (
                report
                .get(
                    "summary",
                    {},
                )
                .get(
                    "overall_score",
                    0,
                )
            )

            status.set_text(
                f"Analysis completed successfully. "
                f"Overall Score: {score}%"
            )

            ui.notify(
                "Compliance analysis completed successfully.",
                type="positive",
            )

            logger.info("=== ANALYSIS SUCCESS | Overall Score: %s%% ===", score)

        except Exception as e:

            if "client this element belongs to has been deleted" in str(e):
                logger.warning("Client session disconnected during analysis pipeline.")
                return

            logger.error("Analysis pipeline error: %s", e, exc_info=True)

            try:
                status.set_text(f"Analysis failed: {e}")
                ui.notify(f"Analysis failed: {e}", type="negative")
            except Exception:
                pass

        finally:

            button.enable()

    # ========================================================
    # CONNECT RUN BUTTON
    # ========================================================

    sidebar[
        "run_button"
    ].on_click(
        run_analysis
    )

    # ========================================================
    # FRAMEWORK CHANGE CALLBACK
    # ========================================================
    
    def handle_framework_change():
        if page_state.get("master_report"):
            selected_fw_keys = []
            if sidebar["gdpr_checkbox"].value:
                selected_fw_keys.append("gdpr")
            if sidebar["hipaa_checkbox"].value:
                selected_fw_keys.append("hipaa")
            if sidebar["rbi_checkbox"].value:
                selected_fw_keys.append("rbi")
            if sidebar["soc2_checkbox"].value:
                selected_fw_keys.append("soc2")

            page_state["selected_frameworks"] = selected_fw_keys
            
            report = filter_report_payload(
                page_state["master_report"],
                selected_fw_keys,
            )
            
            score_container.clear()
            posture_container.clear()
            gap_container.clear()
            action_container.clear()
            compliant_container.clear()
            export_container.clear()
            
            with score_container:
                summary = report.get("summary", {})
                framework_summaries = summary.get("framework_summaries", {})
                create_score_cards(
                    summary=summary,
                    framework_summaries=framework_summaries,
                    selected_fw_keys=selected_fw_keys,
                )
                
            with posture_container:
                create_policy_posture(report)
                
            with gap_container:
                create_gap_analysis(report)
                
            with action_container:
                create_action_plan(report)

            with compliant_container:
                create_compliant_areas(report)
                
            with export_container:
                create_report_export(
                    report=report,
                    company=sidebar["company_name"].value or "Uploaded Organization",
                )

    for cb_key in ["gdpr_checkbox", "hipaa_checkbox", "rbi_checkbox", "soc2_checkbox"]:
        sidebar[cb_key].on_value_change(handle_framework_change)


# ============================================================
# CUSTOM 404 PAGE
# ============================================================

@ui.page("/404")
def not_found_page():
    ui.colors(
        primary='#4e795d',
        dark='#101713',
    )
    with ui.column().classes("w-full min-h-screen items-center justify-center gap-6").style(
        "background: linear-gradient(135deg, #101713 0%, #1a2e20 50%, #101713 100%); "
        "min-height: 100vh; display: flex; flex-direction: column; "
        "align-items: center; justify-content: center; padding: 2rem;"
    ):
        # Shield icon
        ui.html('''
        <div style="
            width: 100px; height: 100px;
            background: linear-gradient(135deg, #4e795d, #3b6349);
            border-radius: 50%; display: flex; align-items: center;
            justify-content: center; font-size: 48px;
            box-shadow: 0 0 40px rgba(78,121,93,0.4);
            margin-bottom: 8px;
        ">🛡️</div>
        ''')

        ui.label("404").style(
            "font-size: 6rem; font-weight: 900; "
            "background: linear-gradient(135deg, #4e795d, #eae3d2); "
            "-webkit-background-clip: text; -webkit-text-fill-color: transparent; "
            "background-clip: text; line-height: 1; margin: 0;"
        )

        ui.label("Page Not Found").style(
            "font-size: 1.5rem; font-weight: 600; color: #eae3d2; margin-top: 4px;"
        )

        ui.label(
            "The page you're looking for doesn't exist or has been moved."
        ).style(
            "color: #8a9e8f; font-size: 1rem; text-align: center; max-width: 400px;"
        )

        ui.button(
            "← Return to LexMesh Dashboard",
            on_click=lambda: ui.navigate.to("/")
        ).style(
            "margin-top: 1rem; "
            "background: linear-gradient(135deg, #4e795d, #3b6349); "
            "color: #eae3d2; border: none; padding: 12px 28px; "
            "border-radius: 8px; font-size: 1rem; font-weight: 600; "
            "cursor: pointer; box-shadow: 0 4px 20px rgba(78,121,93,0.35); "
            "transition: all 0.2s ease;"
        )


if __name__ == "__main__":
    import os
    port = int(os.environ.get("PORT", 8080))
    ui.run(
        title="LexMesh — AI Compliance Engine",
        favicon="🛡️",
        port=port,
        storage_secret=config.NICEGUI_STORAGE_SECRET,
        reload=False,
    )