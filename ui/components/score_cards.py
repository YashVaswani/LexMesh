from nicegui import ui
from ui.components.lucide import lucide_icon


FRAMEWORK_INFO = {
    "gdpr": {
        "name": "EU GDPR",
        "icon": "shield-check",
        "class": "lex-gdpr-card",
        "color": "text-emerald-600",
    },
    "hipaa": {
        "name": "US HIPAA",
        "icon": "activity",
        "class": "lex-hipaa-card",
        "color": "text-teal-600",
    },
    "rbi": {
        "name": "RBI Cyber",
        "icon": "building-2",
        "class": "lex-rbi-card",
        "color": "text-orange-600",
    },
    "soc2": {
        "name": "SOC 2 Type II",
        "icon": "lock",
        "class": "lex-soc2-card",
        "color": "text-amber-600",
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
            ),
            show_value=False,
        ).props(
            ':show-value="false"'
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
                    "icon": "shield-check",
                    "class": "",
                    "color": "text-emerald-600",
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

                    with ui.row().classes("items-center gap-2"):
                        lucide_icon(info["icon"], size=20, class_name=info["color"])
                        ui.label(
                            info['name']
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
                    ),
                    show_value=False,
                ).props(
                    ':show-value="false"'
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