from nicegui import ui


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
        "priority_high",
    )

    _priority(
        "P2 — High",
        plan.get(
            "p2_high",
            [],
        ),
        "lex-p2",
        "warning",
    )

    _priority(
        "P3 — Medium",
        plan.get(
            "p3_medium",
            [],
        ),
        "lex-p3",
        "schedule",
    )


def _priority(
    title,
    items,
    css_class,
    icon,
):

    with ui.card().classes(
        f"w-full lex-action-card {css_class}"
    ):

        with ui.row().classes(
            "items-center gap-2"
        ):

            ui.icon(
                icon
            )

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
                    "title",
                    item.get(
                        "Requirement",
                        item.get(
                            "requirement",
                            "Compliance action",
                        ),
                    ),
                )
            )

            action = (
                item.get(
                    "recommended_action",
                    item.get(
                        "Fix Required",
                        item.get(
                            "fix_suggestion",
                            "",
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

            with ui.card().classes(
                "w-full lex-action-item"
            ):

                ui.label(
                    str(title_text)
                ).classes(
                    "lex-action-item-title"
                )

                if framework:

                    ui.badge(
                        str(framework)
                    ).classes(
                        "lex-framework-mini-badge"
                    )

                if action:

                    ui.label(
                        str(action)
                    ).classes(
                        "lex-action-item-text"
                    )