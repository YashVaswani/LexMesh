from nicegui import ui
from ui.components.lucide import lucide_icon


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

            lucide_icon("shield", size=32, class_name="text-emerald-400")

            with ui.column().classes(
                "gap-0"
            ):

                ui.label(
                    "LexMesh"
                ).classes(
                    "lex-brand-title"
                )

                ui.label(
                    "Multi-Framework Compliance Engine"
                ).classes(
                    "lex-brand-subtitle"
                )

        # ====================================================
        # RIGHT — THEME TOGGLE
        # ====================================================

        with ui.row().classes(
            "items-center gap-3"
        ):

            lucide_icon("sun", size=20, class_name="text-amber-400")

            ui.switch(
                value=False,
                on_change=lambda e: dark_mode.set_value(e.value),
            ).props(
                "color=emerald"
            )

            lucide_icon("moon", size=20, class_name="text-emerald-200 dark:text-emerald-400")