from nicegui import ui
from ui.components.lucide import lucide_icon

def create_compliant_areas(report):
    compliant_items = report.get("compliant_areas", [])

    ui.label("Compliant Areas").classes("lex-section-heading")

    with ui.card().classes("w-full lex-action-card lex-p3"):
        with ui.row().classes("items-center gap-2"):
            lucide_icon("check-circle", size=20, class_name="text-emerald-500")
            ui.label(f"Fully Met Requirements ({len(compliant_items)} items)").classes("lex-action-title")

        if not compliant_items:
            ui.label("No fully compliant requirements found yet.").classes("lex-empty-small")
            return

        for item in compliant_items:
            title_text = item.get("Requirement Citation", "")
            quote = item.get("Verification Quote", "")
            framework = item.get("Framework Standard", "")
            domain = item.get("Policy Domain", "")

            with ui.card().classes("w-full lex-action-item"):
                ui.label(str(title_text)).classes("lex-action-item-title")

                with ui.row().classes("items-center gap-2 mt-1"):
                    if framework:
                        ui.badge(str(framework)).classes("lex-framework-mini-badge")
                    if domain:
                        ui.badge(str(domain)).classes("lex-domain-badge-outline")
                    ui.badge("Fully Met").classes("lex-connected-badge text-emerald-800 bg-emerald-100")

                if quote and quote != "No relevant policy clause found.":
                    with ui.row().classes("items-center gap-2 mt-3 mb-1"):
                        lucide_icon("file-text", size=16, class_name="text-emerald-800")
                        ui.label("Verified Policy Clause").classes("lex-gap-label")
                    ui.label(f'"{str(quote)}"').classes("lex-gap-text italic")
