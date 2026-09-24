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

            def handle_theme_toggle(e):
                dark_mode.set_value(e.value)
                ui.run_javascript(f"localStorage.setItem('lexmesh_dark_mode', '{str(e.value).lower()}');")

            theme_switch = ui.switch(
                value=False,
                on_change=handle_theme_toggle,
            ).props(
                "color=emerald"
            )

            # Restore dark mode preference on page load
            ui.run_javascript("""
                try {
                    const saved = localStorage.getItem('lexmesh_dark_mode');
                    if (saved === 'true') {
                        var sw = document.querySelector('.q-toggle');
                        if (sw && !sw.classList.contains('q-toggle--active')) sw.click();
                    }
                } catch(e) {}
            """)

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