from nicegui import ui
from ui.components.lucide import lucide_icon


def create_policy_posture(report):

    summary = report.get(
        "executive_summary",
        "",
    )

    if not summary:

        summary = (
            report.get(
                "summary",
                {},
            ).get(
                "overall_risk",
                "No executive summary available.",
            )
        )

    with ui.card().classes(
        "w-full lex-posture-summary"
    ):

        ui.label(
            "Executive Policy Posture"
        ).classes(
            "lex-section-heading"
        )

        ui.label(
            summary
        ).classes(
            "lex-posture-text"
        )

    breakdown = report.get(
        "policy_domain_breakdown",
        [],
    )

    ui.label(
        "Policy Domain Breakdown"
    ).classes(
        "lex-section-heading"
    )

    if not breakdown:

        ui.label(
            "No policy domain breakdown available."
        ).classes(
            "lex-empty-state"
        )

        return

    for item in breakdown:

        domain = item.get(
            "domain_title",
            item.get(
                "domain",
                item.get(
                    "policy_domain",
                    "Unknown Domain",
                ),
            ),
        )

        score = item.get(
            "score",
            "—",
        )

        raw_status = str(
            item.get(
                "status",
                item.get("verdict", "")
            ) or ""
        ).strip()

        # Sanitize status: remove any red/green/yellow emojis or bullets
        cleaned = (
            raw_status.replace("🟢", "")
            .replace("🟡", "")
            .replace("🔴", "")
            .replace("●", "")
            .replace("•", "")
            .strip()
        )
        lower_status = cleaned.lower()
        if "fully" in lower_status or ("compliant" in lower_status and "non" not in lower_status):
            verdict = "Fully Met"
        elif "part" in lower_status:
            verdict = "Partially Met"
        elif "not" in lower_status or "non" in lower_status or "unmet" in lower_status or "missing" in lower_status:
            verdict = "Not Met"
        elif cleaned:
            verdict = cleaned
        else:
            verdict = "—"

        with ui.card().classes(
            "w-full lex-domain-card"
        ):

            with ui.row().classes(
                "w-full items-center justify-between"
            ):

                with ui.row().classes("items-center gap-2"):
                    lucide_icon(item.get("icon", "file-text"), size=20, class_name="text-emerald-700 dark:text-emerald-400")
                    ui.label(
                        str(domain)
                    ).classes(
                        "lex-domain-title"
                    )

                ui.badge(
                    str(verdict)
                ).classes(
                    "lex-domain-badge"
                )

            ui.label(
                f"Compliance Score: {score}"
            ).classes(
                "lex-domain-score"
            )

            framework_scores = item.get(
                "framework_scores",
                {},
            )

            if framework_scores:

                with ui.row().classes(
                    "flex-wrap gap-2 mt-2"
                ):

                    for fw, fw_score in (
                        framework_scores.items()
                    ):

                        ui.badge(
                            f"{fw.upper()}: {fw_score}"
                        ).classes(
                            "lex-framework-mini-badge"
                        )