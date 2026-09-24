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

                with ui.row().classes("w-full items-center justify-between flex-wrap gap-2 mt-1"):
                    with ui.row().classes("items-center gap-2"):
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
                        ui.html(
                            f'<button class="lex-copy-btn" title="Copy action item to clipboard" '
                            f'onclick="lexCopyText({repr(str(action))}, this)" '
                            f'style="background:transparent;border:1.5px solid var(--lex-border);'
                            f'border-radius:8px;padding:4px 8px;cursor:pointer;color:var(--lex-muted);'
                            f'display:inline-flex;align-items:center;gap:5px;font-size:0.75rem;font-weight:700;'
                            f'transition:all 0.15s ease;">'
                            f'<svg xmlns="http://www.w3.org/2000/svg" width="13" height="13" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><rect width="14" height="14" x="8" y="8" rx="2" ry="2"/><path d="M4 16c-1.1 0-2-.9-2-2V4c0-1.1.9-2 2-2h10c1.1 0 2 .9 2 2"/></svg> Copy</button>'
                        )

                if action:
                    with ui.row().classes("items-center gap-2 mt-3 mb-1"):
                        lucide_icon("sparkles", size=16, class_name="text-emerald-800 dark:text-emerald-300")
                        ui.label("Action Required").classes("lex-gap-label")
                    ui.label(
                        str(action)
                    ).classes(
                        "lex-gap-text"
                    )