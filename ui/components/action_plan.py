from nicegui import ui
from ui.components.lucide import lucide_icon


def create_action_plan(report):

    plan = report.get(
        "priority_action_plan",
        {},
    )

    ui.label(
        "Policy Action Plan"
    ).classes(
        "lex-section-heading"
    )

    _priority(
        "P1 — Critical",
        plan.get(
            "p1_critical",
            [],
        ),
        "lex-p1",
        "alert-octagon",
        "text-red-500",
    )

    _priority(
        "P2 — High",
        plan.get(
            "p2_high",
            [],
        ),
        "lex-p2",
        "alert-triangle",
        "text-amber-500",
    )

    _priority(
        "P3 — Medium",
        plan.get(
            "p3_medium",
            [],
        ),
        "lex-p3",
        "info",
        "text-emerald-500",
    )


def _priority(
    title,
    items,
    css_class,
    icon,
    color_class="text-emerald-500",
):

    with ui.card().classes(
        f"w-full lex-action-card {css_class}"
    ):

        with ui.row().classes(
            "items-center gap-2"
        ):

            lucide_icon(icon, size=20, class_name=color_class)

            ui.label(
                title
            ).classes(
                "lex-action-title"
            )

        if not items:

            ui.label(
                "No items in this priority."
            ).classes(
                "lex-empty-small"
            )

            return

        for item in items:

            title_text = (
                item.get(
                    "Requirement Citation",
                    item.get(
                        "title",
                        item.get(
                            "Requirement",
                            item.get(
                                "requirement",
                                "Compliance action",
                            ),
                        ),
                    ),
                )
            )

            action = (
                item.get(
                    "Action Required",
                    item.get(
                        "recommended_action",
                        item.get(
                            "Fix Required",
                            item.get(
                                "fix_suggestion",
                                "",
                            ),
                        ),
                    ),
                )
            )

            framework = (
                item.get(
                    "Framework Standard",
                    item.get(
                        "framework_tag",
                        "",
                    ),
                )
            )
            
            domain = item.get("Policy Domain", item.get("policy_domain", ""))
            status = item.get("Current Status", item.get("current_status", ""))

            with ui.card().classes(
                "w-full lex-action-item"
            ):

                ui.label(
                    str(title_text)
                ).classes(
                    "lex-action-item-title"
                )

                with ui.row().classes("items-center gap-2 mt-1"):
                    if framework:

                        ui.badge(
                            str(framework)
                        ).classes(
                            "lex-framework-mini-badge"
                        )
                        
                    if domain:
                        ui.badge(str(domain)).classes("lex-domain-badge-outline")
                        
                    if status:
                        ui.badge(str(status)).classes("lex-status-partial")

                if action:
                    with ui.row().classes("items-center gap-2 mt-3 mb-1"):
                        lucide_icon("sparkles", size=16, class_name="text-emerald-800 dark:text-emerald-300")
                        ui.label("Action Required").classes("lex-gap-label")
                    ui.label(
                        str(action)
                    ).classes(
                        "lex-gap-text"
                    )