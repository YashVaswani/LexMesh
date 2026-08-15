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
            "article",
            gap.get(
                "requirement_text",
                gap.get(
                    "title",
                    "Compliance Requirement",
                ),
            ),
        )

        req_id = gap.get("requirement_id", "")

        status = gap.get(
            "verdict",
            gap.get(
                "status",
                "Unknown",
            ),
        )

        framework = gap.get(
            "framework",
            gap.get(
                "framework_standard",
                "—",
            ),
        )

        explanation = gap.get(
            "analysis",
            gap.get(
                "explanation",
                "",
            ),
        )

        fix = gap.get(
            "fix_required",
            gap.get(
                "fix_suggestion",
                gap.get(
                    "recommended_action",
                    "",
                ),
            ),
        )
        
        mandate = gap.get("requirement_mandate", gap.get("gdpr_requires", ""))
        policy_citation = gap.get("your_policy", "")

        header_title = f"[{req_id}] {str(requirement)[:100]}" if req_id else f"{index + 1}. {str(requirement)[:100]}"
        with ui.expansion(
            header_title
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

            if mandate:
                ui.label("Mandate").classes("lex-gap-label")
                ui.label(str(mandate)).classes("lex-gap-text")

            if policy_citation:
                ui.label("Policy Citation").classes("lex-gap-label")
                ui.label(str(policy_citation)).classes("lex-gap-text")

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