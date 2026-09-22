from nicegui import ui
from ui.components.lucide import lucide_icon


FRAMEWORKS = {
    'All Standards': [
        'gdpr',
        'hipaa',
        'rbi',
        'soc2',
    ],
    'EU GDPR': ['gdpr'],
    'US HIPAA': ['hipaa'],
    'RBI Cyber Framework': ['rbi'],
    'SOC 2 Type II': ['soc2'],
}


def create_sidebar(
    gemini_connected=False,
    groq_connected=False,
    supabase_connected=False,
    on_nav_change=None,
):

    with ui.left_drawer(
        value=True
    ).props(
        "width=340"
    ).classes(
        "lex-sidebar"
    ) as drawer:

        # ====================================================
        # DASHBOARD NAVIGATION SECTION (shown on Dashboard view)
        # ====================================================

        dash_nav_container = ui.column().classes("w-full gap-0 p-0")
        with dash_nav_container:
            with ui.card().classes(
                "lex-sidebar-section"
            ).style(
                "background: #ffffff; border-radius: 16px; "
                "border: 1px solid var(--lex-border);"
            ):
                with ui.row().classes("items-center gap-3 mb-3"):
                    lucide_icon("menu", size=22, class_name="lex-section-icon")
                    ui.label("Navigation").classes("lex-section-title")

                # Dashboard button
                ui.button(
                    "Dashboard",
                    icon="dashboard",
                    on_click=lambda: on_nav_change("dashboard") if on_nav_change else None,
                ).props(
                    "unelevated no-caps align=left"
                ).classes(
                    "w-full"
                ).style(
                    "background: var(--lex-sage) !important; "
                    "color: #ffffff !important; "
                    "border-radius: 12px; "
                    "font-weight: 700; "
                    "font-size: 0.95rem; "
                    "justify-content: flex-start; "
                    "padding: 10px 16px; "
                    "margin-bottom: 6px;"
                )

                # New Audit button
                ui.button(
                    "New Audit",
                    icon="add_circle_outline",
                    on_click=lambda: on_nav_change("audit") if on_nav_change else None,
                ).props(
                    "flat no-caps align=left"
                ).classes(
                    "w-full"
                ).style(
                    "color: var(--lex-text) !important; "
                    "border-radius: 12px; "
                    "font-weight: 600; "
                    "font-size: 0.95rem; "
                    "justify-content: flex-start; "
                    "padding: 10px 16px; "
                    "border: 1px solid var(--lex-border);"
                )

        # ====================================================
        # AUDIT COMPLIANCE & DOCUMENT SECTION (shown on Audit view)
        # ====================================================

        audit_controls_container = ui.column().classes("w-full gap-0 p-0")
        with audit_controls_container:

            # ====================================================
            # COMPLIANCE
            # ====================================================

            with ui.card().classes(
                "lex-sidebar-section lex-target-section"
            ):

                with ui.row().classes(
                    "items-center gap-3"
                ):

                    lucide_icon("shield-check", size=24, class_name="lex-section-icon lex-target-icon")

                    with ui.column().classes("gap-0"):

                        ui.label(
                            "Compliance Target"
                        ).classes(
                            "lex-section-title"
                        )

                        ui.label(
                            "Select frameworks to evaluate"
                        ).classes(
                            "lex-section-subtitle"
                        )

                org_type_select = ui.select(
                    options=[
                        'Global Conglomerate (Full Scope)',
                        'General SaaS / Technology Enterprise',
                        'Healthcare / Medical Technology',
                        'Fintech / Banking / NBFC',
                        'Custom / Manual Selection'
                    ],
                    value='Global Conglomerate (Full Scope)',
                    label="Organization Industry",
                ).props(
                    "outlined dense"
                ).classes(
                    "w-full lex-framework-select"
                )

                ui.label("Evaluation Frameworks").classes("text-xs font-semibold mt-2 text-slate-400")

                with ui.column().classes("gap-1 w-full pl-1 mb-2"):
                    gdpr_checkbox = ui.checkbox("EU GDPR (Art. 1-99)").classes("text-sm")
                    hipaa_checkbox = ui.checkbox("US HIPAA (45 CFR)").classes("text-sm")
                    rbi_checkbox = ui.checkbox("RBI Cyber Guidelines").classes("text-sm")
                    soc2_checkbox = ui.checkbox("SOC 2 Trust Criteria").classes("text-sm")

                # Set all checked by default
                gdpr_checkbox.value = True
                hipaa_checkbox.value = True
                rbi_checkbox.value = True
                soc2_checkbox.value = True

                # Reactivity functions
                def handle_org_change():
                    val = org_type_select.value
                    if val == 'Global Conglomerate (Full Scope)':
                        gdpr_checkbox.value = True
                        hipaa_checkbox.value = True
                        rbi_checkbox.value = True
                        soc2_checkbox.value = True
                    elif val == 'General SaaS / Technology Enterprise':
                        gdpr_checkbox.value = True
                        hipaa_checkbox.value = False
                        rbi_checkbox.value = False
                        soc2_checkbox.value = True
                    elif val == 'Healthcare / Medical Technology':
                        gdpr_checkbox.value = True
                        hipaa_checkbox.value = True
                        rbi_checkbox.value = False
                        soc2_checkbox.value = True
                    elif val == 'Fintech / Banking / NBFC':
                        gdpr_checkbox.value = True
                        hipaa_checkbox.value = False
                        rbi_checkbox.value = True
                        soc2_checkbox.value = True

                def handle_checkbox_change():
                    g = gdpr_checkbox.value
                    h = hipaa_checkbox.value
                    r = rbi_checkbox.value
                    s = soc2_checkbox.value

                    # Temporarily disconnect listener to avoid infinite feedback loop
                    org_type_select.on_value_change(None)

                    if g and h and r and s:
                        org_type_select.value = 'Global Conglomerate (Full Scope)'
                    elif g and not h and not r and s:
                        org_type_select.value = 'General SaaS / Technology Enterprise'
                    elif g and h and not r and s:
                        org_type_select.value = 'Healthcare / Medical Technology'
                    elif g and not h and r and s:
                        org_type_select.value = 'Fintech / Banking / NBFC'
                    else:
                        org_type_select.value = 'Custom / Manual Selection'

                    org_type_select.on_value_change(handle_org_change)

                org_type_select.on_value_change(handle_org_change)
                gdpr_checkbox.on_value_change(handle_checkbox_change)
                hipaa_checkbox.on_value_change(handle_checkbox_change)
                rbi_checkbox.on_value_change(handle_checkbox_change)
                soc2_checkbox.on_value_change(handle_checkbox_change)

            # ====================================================
            # DOCUMENT
            # ====================================================

            with ui.card().classes(
                "lex-sidebar-section lex-document-section"
            ):

                with ui.row().classes(
                    "items-center gap-3"
                ):

                    lucide_icon("file-text", size=24, class_name="lex-section-icon lex-document-icon")

                    with ui.column().classes("gap-0"):

                        ui.label(
                            "Document Input"
                        ).classes(
                            "lex-section-title"
                        )

                        ui.label(
                            "Upload your company policy"
                        ).classes(
                            "lex-section-subtitle"
                        )

                # ------------------------------------------------
                # REAL UPLOAD
                # ------------------------------------------------

                uploaded_file = ui.upload(
                    label="Upload Company Policy PDF",
                    auto_upload=True,
                ).props(
                    "accept=.pdf max-files=1 flat bordered class=w-full"
                ).classes(
                    "lex-policy-upload"
                )

                with ui.row().classes("w-full items-center justify-between mt-1 px-1"):
                    ui.label(
                        "PDF only • 1 document at a time"
                    ).classes(
                        "lex-upload-help"
                    )
                    clear_upload_btn = ui.button(
                        "Clear File",
                        icon="close",
                    ).props(
                        "flat dense size=xs color=negative"
                    ).classes(
                        "text-xs font-medium"
                    )

                # ------------------------------------------------
                # COMPANY
                # ------------------------------------------------

                company_name = ui.input(
                    label="Company Name",
                    placeholder="e.g. TechStartup Pvt Ltd",
                ).props(
                    "outlined dense"
                ).classes(
                    "lex-sidebar-input"
                )

                # ------------------------------------------------
                # POLICY
                # ------------------------------------------------

                policy_name = ui.input(
                    label="Policy Version / Name",
                    placeholder="e.g. Privacy Policy v2.1",
                ).props(
                    "outlined dense"
                ).classes(
                    "lex-sidebar-input"
                )

                # ------------------------------------------------
                # RUN
                # ------------------------------------------------

                run_button = ui.button(
                    "Run Unified Gap Analysis",
                ).props(
                    "unelevated"
                ).classes(
                    "lex-run-button"
                )

        return {
            "drawer": drawer,
            "dash_nav_container": dash_nav_container,
            "audit_controls_container": audit_controls_container,
            "org_type_select": org_type_select,
            "gdpr_checkbox": gdpr_checkbox,
            "hipaa_checkbox": hipaa_checkbox,
            "rbi_checkbox": rbi_checkbox,
            "soc2_checkbox": soc2_checkbox,
            "uploaded_file": uploaded_file,
            "clear_upload_btn": clear_upload_btn,
            "company_name": company_name,
            "policy_name": policy_name,
            "run_button": run_button,
        }


def create_dashboard_sidebar(on_nav_change=None):
    """Fallback helper (deprecated). Navigation controls are now embedded
    inside create_sidebar using single drawer layout."""
    return create_sidebar(on_nav_change=on_nav_change)