from nicegui import ui
from ui.components.lucide import lucide_icon


FRAMEWORK_INFO = {
    "gdpr": {
        "name": "EU GDPR",
        "icon": "shield-check",
        "class": "lex-gdpr-card",
        "color": "text-emerald-600",
        "badge": "lex-fw-badge-gdpr",
    },
    "hipaa": {
        "name": "US HIPAA",
        "icon": "activity",
        "class": "lex-hipaa-card",
        "color": "text-teal-600",
        "badge": "lex-fw-badge-hipaa",
    },
    "rbi": {
        "name": "RBI Cyber",
        "icon": "building-2",
        "class": "lex-rbi-card",
        "color": "text-orange-600",
        "badge": "lex-fw-badge-rbi",
    },
    "soc2": {
        "name": "SOC 2 Type II",
        "icon": "lock",
        "class": "lex-soc2-card",
        "color": "text-amber-600",
        "badge": "lex-fw-badge-soc2",
    },
}


def _score_colour(score: float) -> str:
    """Return CSS class based on score band."""
    if score >= 75:
        return "lex-score-high"
    elif score >= 50:
        return "lex-score-mid"
    return "lex-score-low"


def _pulse_class(score: float) -> str:
    if score >= 75:
        return "lex-pulse-green"
    elif score >= 50:
        return "lex-pulse-amber"
    return "lex-pulse-red"


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

    pulse = _pulse_class(overall)
    colour = _score_colour(overall)

    # ========================================================
    # OVERALL
    # ========================================================

    with ui.card().classes(
        f"w-full lex-score-card {pulse}"
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

            # Score element with animated counter
            score_el = ui.label(
                f"{overall:.0f}%"
            ).classes(
                f"lex-overall-score lex-score-animated {colour}"
            )
            # Trigger JS counter animation
            ui.run_javascript(
                f"lexAnimateScore(document.querySelector('.lex-overall-score'), {overall:.0f}, 900);"
            )
            # Trigger confetti if high score
            if overall >= 85:
                ui.run_javascript("setTimeout(lexConfetti, 400);")

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
                    "badge": "",
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

            fw_colour = _score_colour(score)
            fw_pulse = _pulse_class(score)

            with ui.card().classes(
                f"lex-framework-card {info['class']} lex-hover-lift"
            ):

                with ui.row().classes(
                    "w-full items-center justify-between no-wrap gap-1"
                ):

                    with ui.row().classes("items-center gap-1.5 no-wrap min-w-0"):
                        lucide_icon(info["icon"], size=18, class_name=f"{info['color']} shrink-0")
                        ui.label(
                            info['name']
                        ).classes(
                            "lex-framework-name whitespace-nowrap"
                        )

                    ui.label(
                        f"{score:.0f}%"
                    ).classes(
                        f"lex-framework-score shrink-0 lex-score-animated {fw_colour}"
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