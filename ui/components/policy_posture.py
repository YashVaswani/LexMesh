from nicegui import ui


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

        icon = item.get("icon", "📄")

        score = item.get(
            "score",
            "—",
        )

        verdict = item.get(
            "status",
            item.get(
                "verdict",
                "—",
            ),
        )

        with ui.card().classes(
            "w-full lex-domain-card"
        ):

            with ui.row().classes(
                "w-full items-center justify-between"
            ):

                ui.label(
                    f"{icon} {domain}"
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