from nicegui import ui
from ui.components.lucide import lucide_icon


def create_header(on_nav_change=None, active_tab="dashboard"):
    """Create the top header bar.

    Parameters
    ----------
    on_nav_change : callable | None
        Callback invoked with the new tab name ("dashboard" or "audit")
        when the user clicks a navigation pill.
    active_tab : str
        The currently active tab, either "dashboard" or "audit".
    """

    dark_mode = ui.dark_mode()

    with ui.header().classes(
        "lex-header h-20 px-6 items-center justify-between"
    ):

        # ====================================================
        # LEFT — LOGO + BRAND (clickable → home)
        # ====================================================

        with ui.row().classes(
            "items-center gap-3 cursor-pointer select-none"
        ).style(
            "transition: opacity 0.18s ease;"
        ).on(
            "click", lambda: ui.navigate.to('/dashboard')
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
        # CENTER — spacer for layout balance
        # ====================================================

        ui.element("div")

        # ====================================================
        # RIGHT — THEME TOGGLE + LOGOUT
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

            import auth
            def on_logout():
                auth.sign_out()
                ui.navigate.to('/login')

            ui.button(
                icon="logout",
                on_click=on_logout
            ).props(
                "flat round color=emerald"
            ).tooltip("Log out")

    return {}