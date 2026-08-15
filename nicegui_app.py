import json
import re
from pathlib import Path

import pymupdf as fitz
from nicegui import ui

from config import config
from db.supabase_client import supabase_db
from agents.adk_agent import adk_supervisor

from ui.components.header import create_header
from ui.components.sidebar import create_sidebar
from ui.components.score_cards import create_score_cards
from ui.components.policy_posture import create_policy_posture
from ui.components.gap_analysis import create_gap_analysis
from ui.components.action_plan import create_action_plan
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


# ============================================================
# DASHBOARD
# ============================================================

@ui.page("/")
def dashboard():

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

            print(
                "[LexMesh] PDF READY FOR ANALYSIS"
            )

        except Exception as e:

            page_state[
                "pdf_bytes"
            ] = None

            page_state[
                "pdf_name"
            ] = ""

            status.set_text(
                f"❌ Upload failed: {e}"
            )

            ui.notify(
                f"Upload failed: {e}",
                type="negative",
            )

            print()
            print(
                "=========================================="
            )
            print(
                "[LexMesh] UPLOAD ERROR"
            )
            print(
                "=========================================="
            )

            import traceback

            traceback.print_exc()

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

        print()
        print(
            "=========================================="
        )
        print(
            "[LexMesh] RUN BUTTON CLICKED"
        )
        print(
            "=========================================="
        )

        # ----------------------------------------------------
        # GET CURRENT PAGE PDF
        # ----------------------------------------------------

        pdf_bytes = page_state.get(
            "pdf_bytes"
        )

        print(
            "[LexMesh] PDF STATE:",
            (
                "AVAILABLE"
                if pdf_bytes
                else "EMPTY"
            ),
        )

        print(
            "[LexMesh] PDF SIZE:",
            (
                len(pdf_bytes)
                if pdf_bytes
                else 0
            ),
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

            selected_label = (
                sidebar[
                    "framework_select"
                ].value
            )

            selected_fw_keys = FRAMEWORKS.get(
                selected_label,
                FRAMEWORKS[
                    "All Standards (Full Scope)"
                ],
            )

            page_state[
                "selected_frameworks"
            ] = selected_fw_keys

            print(
                "[LexMesh] Company:",
                company,
            )

            print(
                "[LexMesh] Policy:",
                policy,
            )

            print(
                "[LexMesh] Frameworks:",
                selected_fw_keys,
            )

            # =================================================
            # EXTRACT POLICY TEXT
            # =================================================

            status.set_text(
                "📖 Reading policy PDF..."
            )

            print(
                "[LexMesh] Opening PDF..."
            )

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

            print(
                "[LexMesh] Extracted characters:",
                len(policy_text),
            )

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

            print()
            print(
                "=========================================="
            )
            print(
                "[LexMesh] CALLING ADK PIPELINE"
            )
            print(
                "=========================================="
            )

            import asyncio
            master_report = await asyncio.get_event_loop().run_in_executor(
                None,
                adk_supervisor.run_adk_pipeline,
                company,
                policy,
                policy_text,
            )

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

            print(
                "[LexMesh] ADK PIPELINE COMPLETED"
            )

            print(
                "[LexMesh] Report keys:",
                list(
                    master_report.keys()
                ),
            )

            # =================================================
            # APPLY FRAMEWORK FILTER
            # =================================================

            report = filter_report_payload(
                master_report,
                selected_fw_keys,
            )

            # =================================================
            # CLEAR OLD UI
            # =================================================

            score_container.clear()
            posture_container.clear()
            gap_container.clear()
            action_container.clear()
            export_container.clear()

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

            # DEBUG: Trace exactly where score comes from
            _summary_obj = report.get("summary", {})
            print(
                "[LexMesh] DEBUG summary keys:",
                list(_summary_obj.keys()) if isinstance(_summary_obj, dict) else type(_summary_obj),
            )
            print(
                "[LexMesh] DEBUG overall_score raw:",
                repr(_summary_obj.get("overall_score")) if isinstance(_summary_obj, dict) else "N/A",
            )
            print(
                "[LexMesh] DEBUG framework_summaries keys:",
                list(_summary_obj.get("framework_summaries", {}).keys()) if isinstance(_summary_obj, dict) else "N/A",
            )
            for _fw_key, _fw_val in _summary_obj.get("framework_summaries", {}).items():
                print(
                    f"[LexMesh] DEBUG   {_fw_key} -> score={_fw_val.get('score') if isinstance(_fw_val, dict) else _fw_val}"
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

            print()
            print(
                "=========================================="
            )
            print(
                "[LexMesh] ANALYSIS SUCCESS"
            )
            print(
                f"[LexMesh] Overall Score: {score}%"
            )
            print(
                "=========================================="
            )

        except Exception as e:

            status.set_text(
                f"❌ Analysis failed: {e}"
            )

            ui.notify(
                f"Analysis failed: {e}",
                type="negative",
            )

            print()
            print(
                "=========================================="
            )
            print(
                "[LexMesh] ANALYSIS ERROR"
            )
            print(
                "=========================================="
            )

            import traceback

            traceback.print_exc()

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
            # Update the page state and re-render
            selected_label = sidebar["framework_select"].value
            selected_fw_keys = FRAMEWORKS.get(
                selected_label,
                FRAMEWORKS["All Standards (Full Scope)"],
            )
            page_state["selected_frameworks"] = selected_fw_keys
            
            report = filter_report_payload(
                page_state["master_report"],
                selected_fw_keys,
            )
            
            score_container.clear()
            posture_container.clear()
            gap_container.clear()
            action_container.clear()
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
                
            with export_container:
                create_report_export(
                    report=report,
                    company=sidebar["company_name"].value or "Uploaded Organization",
                )

    sidebar[
        "framework_select"
    ].on_value_change(
        handle_framework_change
    )


# ============================================================
# START APPLICATION
# ============================================================

ui.run(
    title="LexMesh",
    port=8080,
)