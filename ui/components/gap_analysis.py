from nicegui import ui
from ui.components.lucide import lucide_icon


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

    # Filter out Fully Met / Compliant items — they belong exclusively in the Compliant Areas tab
    gaps = [
        g for g in gaps
        if "fully" not in str(g.get("verdict") or g.get("status") or "").lower()
        and str(g.get("verdict") or g.get("status") or "").strip().lower() not in ("met", "compliant")
    ]

    ui.label(
        "Detailed Policy Gaps"
    ).classes(
        "lex-section-heading"
    )

    ui.label(
        f"{len(gaps)} compliance gaps requiring remediation"
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
                with ui.row().classes("items-center gap-2 mt-3 mb-1"):
                    lucide_icon("file-text", size=18, class_name="text-emerald-800 dark:text-emerald-300")
                    ui.label("Mandatory Statutory Standard").classes("lex-gap-label")
                ui.label(str(mandate)).classes("lex-gap-text")

            if policy_citation:
                with ui.row().classes("items-center gap-2 mt-3 mb-1"):
                    lucide_icon("file-check", size=18, class_name="text-emerald-800 dark:text-emerald-300")
                    ui.label("Policy Citation & Extract").classes("lex-gap-label")
                ui.label(str(policy_citation)).classes("lex-gap-text")

            if explanation:
                with ui.row().classes("items-center gap-2 mt-3 mb-1"):
                    lucide_icon("shield-alert", size=18, class_name="text-emerald-800 dark:text-emerald-300")
                    ui.label("Analysis & Compliance Gap").classes("lex-gap-label")
                ui.label(str(explanation)).classes("lex-gap-text")

            if fix:
                with ui.row().classes("items-center gap-2 mt-3 mb-1"):
                    lucide_icon("sparkles", size=18, class_name="text-emerald-800 dark:text-emerald-300")
                    ui.label("Recommended Remediation Fix").classes("lex-gap-label")
                ui.label(str(fix)).classes("lex-fix-box")