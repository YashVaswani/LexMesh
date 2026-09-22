from nicegui import ui
from ui.components.lucide import lucide_icon

def create_frameworks_page():
    """Render the standalone frameworks explanation page with full dark/light theme support."""
    
    with ui.column().classes("w-full p-8 max-w-4xl mx-auto gap-6"):
        
        # Header
        with ui.row().classes("w-full items-center justify-between mb-2"):
            with ui.row().classes("items-center gap-3"):
                lucide_icon("layers", size=32, class_name="text-emerald-700 dark:text-emerald-400")
                ui.label("Compliance Frameworks").classes("text-3xl font-extrabold text-[var(--lex-text)]")
        
        ui.label("LexMesh natively evaluates enterprise policies against the following global regulatory frameworks. Read below to learn more about each.").classes("text-base text-[var(--lex-muted)]")
        
        with ui.column().classes("w-full gap-4"):
            with ui.expansion("GDPR (General Data Protection Regulation)", icon="security").classes("w-full lex-framework-accordion"):
                with ui.column().classes("w-full gap-2"):
                    ui.label("The GDPR is a regulation in EU law on data protection and privacy in the European Union and the European Economic Area. It addresses the transfer of personal data outside the EU and EEA areas.").classes("lex-framework-desc")
                    with ui.row().classes("lex-framework-industries-box items-center gap-2 flex-wrap"):
                        ui.label("Applicable Industries:").classes("lex-framework-industries-label")
                        ui.label("All industries handling EU citizen data (Technology, Finance, Healthcare, Retail, etc.)").classes("lex-framework-industries-text")

            with ui.expansion("HIPAA (Health Insurance Portability and Accountability Act)", icon="local_hospital").classes("w-full lex-framework-accordion"):
                with ui.column().classes("w-full gap-2"):
                    ui.label("HIPAA is a US federal law that required the creation of national standards to protect sensitive patient health information from being disclosed without the patient's consent or knowledge.").classes("lex-framework-desc")
                    with ui.row().classes("lex-framework-industries-box items-center gap-2 flex-wrap"):
                        ui.label("Applicable Industries:").classes("lex-framework-industries-label")
                        ui.label("Healthcare providers, Health plans, Healthcare clearinghouses, and Business associates.").classes("lex-framework-industries-text")

            with ui.expansion("RBI Cyber Guidelines", icon="account_balance").classes("w-full lex-framework-accordion"):
                with ui.column().classes("w-full gap-2"):
                    ui.label("The Reserve Bank of India (RBI) mandates comprehensive cyber security frameworks for banks and NBFCs, focusing on IT governance, baseline security, and incident reporting.").classes("lex-framework-desc")
                    with ui.row().classes("lex-framework-industries-box items-center gap-2 flex-wrap"):
                        ui.label("Applicable Industries:").classes("lex-framework-industries-label")
                        ui.label("Banking, Financial Services, and NBFCs operating in India.").classes("lex-framework-industries-text")

            with ui.expansion("SOC 2 (System and Organization Controls 2)", icon="verified_user").classes("w-full lex-framework-accordion"):
                with ui.column().classes("w-full gap-2"):
                    ui.label("SOC 2 is a voluntary compliance standard for service organizations, developed by the AICPA, which specifies how organizations should manage customer data based on Trust Services Criteria: security, availability, processing integrity, confidentiality, and privacy.").classes("lex-framework-desc")
                    with ui.row().classes("lex-framework-industries-box items-center gap-2 flex-wrap"):
                        ui.label("Applicable Industries:").classes("lex-framework-industries-label")
                        ui.label("Cloud service providers, SaaS companies, Data centers, and B2B vendors.").classes("lex-framework-industries-text")
