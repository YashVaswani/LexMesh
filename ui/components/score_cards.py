from nicegui import ui


FRAMEWORK_INFO = {
    "gdpr": {
        "name": "EU GDPR",
        "icon": "🇪🇺",
        "class": "lex-gdpr-card",
    },
    "hipaa": {
        "name": "US HIPAA",
        "icon": "🏥",
        "class": "lex-hipaa-card",
    },
    "rbi": {
        "name": "RBI Cyber",
        "icon": "🏦",
        "class": "lex-rbi-card",
    },
    "soc2": {
        "name": "SOC 2 Type II",
        "icon": "🛡️",
        "class": "lex-soc2-card",
    },
}


def create_score_cards(
    summary,
    framework_summaries,
    selected_fw_keys,
):

    overall = _number(
        summary.get(
            "overall_score",
            0,
        )
    )

    risk = summary.get(
        "overall_risk",
        "Risk not available",
    )

    # ========================================================
    # OVERALL
    # ========================================================

    with ui.card().classes(
        "w-full lex-score-card"
    ):

        with ui.row().classes(
            "w-full items-center justify-between"
        ):

            with ui.column().classes(
                "gap-1"
            ):

                ui.label(
                    "Overall Compliance Score"
                ).classes(
                    "lex-card-title"
                )

                ui.label(
                    str(risk)
                ).classes(
                    "lex-risk-text"
                )

            ui.label(
                f"{overall:.0f}%"
            ).classes(
                "lex-overall-score"
            )

        ui.linear_progress(
            value=max(
                0,
                min(
                    overall / 100,
                    1,
                ),
            )
        ).classes(
            "lex-score-progress"
        )

    # ========================================================
    # FRAMEWORKS
    # ========================================================

    ui.label(
        "Framework Breakdown"
    ).classes(
        "lex-section-heading"
    )

    with ui.grid().classes(
        "w-full grid-cols-1 md:grid-cols-2 xl:grid-cols-4 gap-4"
    ):

        for key in selected_fw_keys:

            data = framework_summaries.get(
                key
            )

            if data is None:
                continue

            info = FRAMEWORK_INFO.get(
                key,
                {
                    "name": key.upper(),
                    "icon": "🛡️",
                    "class": "",
                },
            )

            score = _number(
                data.get(
                    "score",
                    0,
                )
            )

            risk_level = data.get(
                "risk_level",
                "—",
            )

            penalty = data.get(
                "penalty_exposure",
                "—",
            )

            with ui.card().classes(
                f"lex-framework-card {info['class']}"
            ):

                with ui.row().classes(
                    "items-center justify-between"
                ):

                    ui.label(
                        f"{info['icon']} {info['name']}"
                    ).classes(
                        "lex-framework-name"
                    )

                    ui.label(
                        f"{score:.0f}%"
                    ).classes(
                        "lex-framework-score"
                    )

                ui.linear_progress(
                    value=max(
                        0,
                        min(
                            score / 100,
                            1,
                        ),
                    )
                )

                ui.label(
                    f"Risk: {risk_level}"
                ).classes(
                    "lex-framework-risk"
                )

                ui.label(
                    f"Exposure: {penalty}"
                ).classes(
                    "lex-framework-exposure"
                )


def _number(value):

    try:
        return float(
            str(value)
            .replace("%", "")
            .strip()
        )
    except Exception:
        return 0