from nicegui import ui
from ui.components.lucide import lucide_icon


def create_privacy_policy_page():
    """Renders the LexMesh Privacy Policy page. Publicly accessible, no auth required."""

    ui.colors(
        primary='#4e795d',
        secondary='#eae3d2',
        positive='#3b6349',
        negative='#9e3232',
    )

    with ui.column().classes("w-full min-h-screen items-center py-12 px-4").style(
        "background: var(--lex-bg, #f5f2eb);"
    ):
        # ── Header ──────────────────────────────────────────────────────────
        with ui.column().classes("w-full max-w-3xl gap-2 mb-10"):
            with ui.row().classes("items-center gap-3 mb-4"):
                ui.link("← Back to LexMesh", "/").classes(
                    "text-sm font-semibold text-emerald-700 hover:text-emerald-900 transition-colors"
                )

            with ui.row().classes("items-center gap-3"):
                with ui.element("div").style(
                    "width:48px;height:48px;border-radius:14px;"
                    "background:linear-gradient(135deg,#4e795d,#23382b);"
                    "display:flex;align-items:center;justify-content:center;"
                    "box-shadow:0 4px 16px rgba(78,121,93,0.35);"
                ):
                    lucide_icon("shield", size=26, class_name="", extra_style="color:#eae3d2;")

                with ui.column().classes("gap-0"):
                    ui.label("Privacy Policy").style(
                        "font-size:2rem;font-weight:900;color:#1b3825;line-height:1.1;"
                    )
                    ui.label("LexMesh — AI Compliance Engine").style(
                        "font-size:0.9rem;font-weight:600;color:#647269;"
                    )

            ui.label("Effective Date: September 2026 · Applies to lexmesh.onrender.com").style(
                "font-size:0.82rem;color:#8a9e8f;margin-top:6px;"
            )

        # ── Content Card ────────────────────────────────────────────────────
        with ui.card().classes("w-full max-w-3xl shadow-lg").style(
            "border-radius:20px;border:2px solid #ddd8cc;"
            "background:#fdfcf9;padding:40px;"
        ):

            def section(icon_name: str, heading: str, body: str):
                with ui.column().classes("w-full gap-2 mb-8"):
                    with ui.row().classes("items-center gap-2"):
                        lucide_icon(icon_name, size=20, class_name="", extra_style="color:#4e795d;")
                        ui.label(heading).style(
                            "font-size:1.1rem;font-weight:800;color:#1b3825;"
                        )
                    ui.separator().style("border-color:#e8e3d8;")
                    ui.html(f'<p style="color:#3d4a42;line-height:1.75;font-size:0.95rem;">{body}</p>')

            section(
                "file-lock",
                "1. Document Processing & Data Handling",
                "When you upload a company policy PDF to LexMesh, your document is processed <strong>entirely in memory</strong> "
                "within your active browser session. <strong>No uploaded documents are stored, persisted, or written to any disk or database.</strong> "
                "Documents are discarded immediately when you clear the upload, log out, or your session expires. "
                "Your confidential corporate policies are never retained by LexMesh beyond the duration of your active audit session.",
            )

            section(
                "cpu",
                "2. AI Processing — Your Data Is Never Used for Training",
                "LexMesh uses third-party AI language model APIs solely to evaluate your policy text against statutory compliance criteria. "
                "<strong>Your uploaded documents are never used to train, fine-tune, or improve any AI model.</strong> "
                "Policy text is transmitted to AI providers exclusively for the purpose of generating your audit results and is subject to the data processing agreements of those providers.",
            )

            section(
                "database",
                "3. Audit Results & Storage",
                "Compliance audit results (scores, gap summaries, and action plans) are stored securely in your account's audit history "
                "to power your compliance dashboard and historical trend analytics. "
                "This stored data contains <strong>no raw document text</strong> — only the structured audit outcome data derived from the analysis. "
                "You may request deletion of your audit history at any time by contacting us.",
            )

            section(
                "user-check",
                "4. Account Information",
                "LexMesh collects your email address and encrypted password for account authentication. "
                "We do not collect payment information, phone numbers, or any personally identifying information beyond what is required for account access. "
                "We do not sell, share, or transfer your account data to any third party for marketing or commercial purposes.",
            )

            section(
                "cookie",
                "5. Cookies & Session Data",
                "LexMesh uses <strong>essential session cookies only</strong> to maintain your authenticated session state. "
                "We do not use tracking cookies, advertising cookies, or third-party analytics cookies. "
                "Session data is cleared when you log out or your browser session ends.",
            )

            section(
                "globe",
                "6. Compliance With Privacy Laws",
                "As a compliance platform, LexMesh is designed and operated with strict adherence to applicable data protection laws including "
                "<strong>EU GDPR</strong> (Regulation EU 2016/679) and India's <strong>DPDP Act 2023</strong>. "
                "Users in the EU have the right to access, correct, restrict, or erase their personal data. To exercise any of these rights, "
                "contact us using the information below.",
            )

            section(
                "mail",
                "7. Contact",
                "For any privacy-related inquiries, data deletion requests, or to report a concern, please contact the LexMesh team directly "
                "through the platform. We are committed to responding to all privacy inquiries within 5 business days.",
            )

        # ── Footer ───────────────────────────────────────────────────────────
        with ui.row().classes("w-full max-w-3xl items-center justify-center gap-4 mt-8"):
            ui.link("Back to Dashboard", "/").classes(
                "text-sm font-semibold text-emerald-700 hover:underline"
            )
            ui.label("·").style("color:#8a9e8f;")
            ui.link("Terms & Conditions", "/terms").classes(
                "text-sm font-semibold text-emerald-700 hover:underline"
            )
            ui.label("·").style("color:#8a9e8f;")
            ui.label("© 2026 LexMesh. All rights reserved.").style(
                "font-size:0.82rem;color:#8a9e8f;"
            )
