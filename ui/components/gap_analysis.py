from nicegui import ui


STATUS_CLASS = {
    "Fully Met": "lex-status-met",
    "Partially Met": "lex-status-partial",
    "Not Met": "lex-status-not",
    "Conflicting": "lex-status-conflict",
}


def create_gap_analysis(report):

    gaps = report.get(
        "all_gaps_flat",
        [],
    )

    if not gaps:

        detailed = report.get(
            "detailed_policy_gaps",
            {},
        )

        for domain in detailed.values():

            for framework_gaps in domain.get(
                "framework_gaps",
                {},
            ).values():

                if isinstance(
                    framework_gaps,
                    list,
                ):
                    gaps.extend(
                        framework_gaps
                    )

    ui.label(
        "Detailed Policy Gaps"
    ).classes(
        "lex-section-heading"
    )

    ui.label(
        f"{len(gaps)} findings identified"
    ).classes(
        "lex-section-subtitle"
    )

    if not gaps:

        ui.label(
            "No detailed gaps are available."
        ).classes(
            "lex-empty-state"
        )

        return

    for index, gap in enumerate(gaps):

        requirement = gap.get(
            "requirement_text",
            gap.get(
                "requirement",
                gap.get(
                    "title",
                    "Compliance Requirement",
                ),
            ),
        )

        status = gap.get(
            "status",
            "Unknown",
        )

        framework = gap.get(
            "framework",
            gap.get(
                "framework_standard",
                "—",
            ),
        )

        explanation = gap.get(
            "explanation",
            gap.get(
                "analysis",
                "",
            ),
        )

        fix = gap.get(
            "fix_suggestion",
            gap.get(
                "fix_required",
                gap.get(
                    "recommended_action",
                    "",
                ),
            ),
        )

        with ui.expansion(
            f"{index + 1}. {str(requirement)[:100]}"
        ).classes(
            "w-full lex-gap-expansion"
        ):

            with ui.row().classes(
                "items-center gap-2 mb-3"
            ):

                ui.badge(
                    str(framework).upper()
                ).classes(
                    "lex-framework-mini-badge"
                )

                ui.badge(
                    str(status)
                ).classes(
                    STATUS_CLASS.get(
                        status,
                        "lex-status-unknown",
                    )
                )

            if explanation:

                ui.label(
                    "Analysis"
                ).classes(
                    "lex-gap-label"
                )

                ui.label(
                    str(explanation)
                ).classes(
                    "lex-gap-text"
                )

            if fix:

                ui.label(
                    "Recommended Fix"
                ).classes(
                    "lex-gap-label"
                )

                ui.label(
                    str(fix)
                ).classes(
                    "lex-fix-box"
                )