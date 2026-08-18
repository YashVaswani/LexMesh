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
):

    with ui.left_drawer(
        value=True
    ).classes(
        "lex-sidebar"
    ):

        # ====================================================
        # PIPELINE
        # ====================================================

        with ui.card().classes(
            "lex-sidebar-section lex-pipeline-section"
        ):

            with ui.row().classes(
                "items-center gap-3"
            ):

                lucide_icon("workflow", size=24, class_name="lex-section-icon lex-pipeline-icon")

                with ui.column().classes("gap-0"):

                    ui.label(
                        "System Pipeline"
                    ).classes(
                        "lex-section-title"
                    )

                    ui.label(
                        "AI compliance infrastructure"
                    ).classes(
                        "lex-section-subtitle"
                    )

            ui.separator().classes(
                "lex-section-divider"
            )

            _service(
                "sparkles",
                "Gemini API",
                "Google AI",
                gemini_connected,
                "lex-gemini-icon",
            )

            _service(
                "zap",
                "Groq API",
                "Fast inference",
                groq_connected,
                "lex-groq-icon",
            )

            _service(
                "database",
                "Supabase DB",
                "Data layer",
                supabase_connected,
                "lex-db-icon",
            )

            _service(
                "layers",
                "Google ADK",
                "Orchestration",
                True,
                "lex-adk-icon",
            )

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
                "accept=.pdf flat bordered class=w-full"
            ).classes(
                "lex-policy-upload"
            )

            ui.label(
                "PDF only • Select your company policy document"
            ).classes(
                "lex-upload-help"
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
            "org_type_select": org_type_select,
            "gdpr_checkbox": gdpr_checkbox,
            "hipaa_checkbox": hipaa_checkbox,
            "rbi_checkbox": rbi_checkbox,
            "soc2_checkbox": soc2_checkbox,
            "uploaded_file": uploaded_file,
            "company_name": company_name,
            "policy_name": policy_name,
            "run_button": run_button,
        }


def _service(
    icon,
    name,
    subtitle,
    connected,
    icon_class,
):

    with ui.row().classes(
        "lex-service-row items-center"
    ):

        lucide_icon(icon, size=18, class_name=f"lex-service-icon {icon_class}")

        with ui.column().classes(
            "gap-0 flex-1"
        ):

            ui.label(
                name
            ).classes(
                "lex-service-name"
            )

            ui.label(
                subtitle
            ).classes(
                "lex-service-subtitle"
            )

        ui.badge(
            "Connected"
            if connected
            else "Offline"
        ).classes(
            "lex-connected-badge"
            if connected
            else "lex-warning-badge"
        )