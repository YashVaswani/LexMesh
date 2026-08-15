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

            framework_select = ui.select(
                options=list(
                    FRAMEWORKS.keys()
                ),
                value=(
                    'All Standards'
                ),
                label="Compliance framework",
            ).props(
                "outlined dense"
            ).classes(
                "lex-framework-select"
            )

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
            "framework_select": framework_select,
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