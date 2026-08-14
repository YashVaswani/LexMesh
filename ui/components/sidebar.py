from nicegui import ui


FRAMEWORKS = {
    '🌐 All Standards (Full Scope)': [
        'gdpr',
        'hipaa',
        'rbi',
        'soc2',
    ],
    '🇪🇺 EU GDPR': ['gdpr'],
    '🏥 US HIPAA': ['hipaa'],
    '🏦 RBI Cyber Framework': ['rbi'],
    '🛡️ SOC 2 Type II': ['soc2'],
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

                ui.icon(
                    "account_tree"
                ).classes(
                    "lex-section-icon lex-pipeline-icon"
                )

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
                "auto_awesome",
                "Gemini API",
                "Google AI",
                gemini_connected,
                "lex-gemini-icon",
            )

            _service(
                "bolt",
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
                "hub",
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

                ui.icon(
                    "verified_user"
                ).classes(
                    "lex-section-icon lex-target-icon"
                )

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
                    '🌐 All Standards (Full Scope)'
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

                ui.icon(
                    "picture_as_pdf"
                ).classes(
                    "lex-section-icon lex-document-icon"
                )

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
                "accept=.pdf"
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
                icon="rocket_launch",
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
        "lex-service-row"
    ):

        ui.icon(
            icon
        ).classes(
            f"lex-service-icon {icon_class}"
        )

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