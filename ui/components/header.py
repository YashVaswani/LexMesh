from nicegui import ui


def create_header():

    dark_mode = ui.dark_mode()

    with ui.header().classes(
        "lex-header h-20 px-6 items-center justify-between"
    ):

        # ====================================================
        # LEFT — LOGO + BRAND
        # ====================================================

        with ui.row().classes(
            "items-center gap-3"
        ):

            ui.icon(
                "shield"
            ).classes(
                "text-blue-500 text-4xl"
            )

            with ui.column().classes(
                "gap-0"
            ):

                ui.label(
                    "LexMesh"
                ).classes(
                    "text-2xl font-bold "
                    "text-slate-900 dark:text-white"
                )

                ui.label(
                    "Multi-Framework Compliance Engine"
                ).classes(
                    "text-xs "
                    "text-slate-500 dark:text-slate-400"
                )

        # ====================================================
        # RIGHT — THEME TOGGLE
        # ====================================================

        with ui.row().classes(
            "items-center gap-3"
        ):

            ui.icon(
                "light_mode"
            ).classes(
                "text-amber-500 text-xl"
            )

            ui.switch(
                value=False,
                on_change=lambda e: dark_mode.set_value(e.value),
            ).props(
                "color=primary"
            )

            ui.icon(
                "dark_mode"
            ).classes(
                "text-slate-500 dark:text-blue-400 text-xl"
            )