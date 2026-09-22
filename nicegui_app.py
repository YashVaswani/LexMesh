import os
import json
import re
import warnings
from pathlib import Path

# Suppress SDK deprecation warnings in application output logs
warnings.filterwarnings("ignore")

import pymupdf as fitz
from nicegui import app, ui
from fastapi import Request
from fastapi.responses import JSONResponse

from config import config
from db.supabase_client import supabase_db
from agents.adk_agent import adk_supervisor
from logger import get_logger
import auth

logger = get_logger("app")

@app.post("/api/confirm-email")
async def api_confirm_email(request: Request):
    """Receives the Supabase access/refresh tokens from the /confirm page JS
    and validates the session server-side."""
    try:
        body = await request.json()
        access_token = body.get("access_token", "")
        refresh_token = body.get("refresh_token", "")
        if not access_token:
            return JSONResponse({"success": False, "error": "Missing token"}, status_code=400)
        # We do NOT set the NiceGUI session here (different request context).
        # Just validate the token with Supabase to confirm the user is real.
        # The user will log in normally after this.
        res = supabase_db.client.auth.get_user(access_token)
        if res and res.user:
            return JSONResponse({"success": True})
        return JSONResponse({"success": False, "error": "Token validation failed"})
    except Exception as e:
        return JSONResponse({"success": False, "error": str(e)}, status_code=500)


from ui.components.header import create_header
from ui.components.sidebar import create_sidebar, create_dashboard_sidebar
from ui.components.score_cards import create_score_cards
from ui.components.policy_posture import create_policy_posture
from ui.components.gap_analysis import create_gap_analysis
from ui.components.action_plan import create_action_plan
from ui.components.compliant_areas import create_compliant_areas
from ui.components.report_export import create_report_export
from ui.components.dashboard_landing import create_dashboard_landing
from ui.components.lucide import lucide_icon

# Load Custom Enterprise Theme CSS & Lucide Icons CDN
theme_css_path = Path(__file__).parent / "ui" / "styles" / "theme.css"
if theme_css_path.exists():
    ui.add_head_html(f"<style>{theme_css_path.read_text(encoding='utf-8')}</style>", shared=True)

ui.add_head_html('''
<script src="https://unpkg.com/lucide@latest"></script>
<script>
    document.addEventListener("DOMContentLoaded", () => {
        if (window.lucide) lucide.createIcons();
    });
</script>
''', shared=True)

# OpenGraph & SEO Meta Tags — rich link previews when shared on Slack/WhatsApp/LinkedIn
ui.add_head_html('''
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<meta name="description" content="LexMesh — AI-powered multi-framework compliance engine for GDPR, HIPAA, RBI, and SOC 2. Upload your policy PDF and get instant gap analysis with a prioritised action plan.">
<meta name="keywords" content="compliance, GDPR, HIPAA, SOC2, RBI, AI compliance, policy analysis, LexMesh">
<meta name="author" content="LexMesh">

<!-- OpenGraph -->
<meta property="og:type" content="website">
<meta property="og:title" content="LexMesh — AI-Powered Compliance Engine">
<meta property="og:description" content="Instantly audit your company policy PDF against GDPR, HIPAA, RBI &amp; SOC 2 with AI-powered multi-framework gap analysis and a prioritised action plan.">
<meta property="og:image" content="https://placehold.co/1200x630/101713/eae3d2?text=LexMesh+Compliance+Engine">
<meta property="og:site_name" content="LexMesh">

<!-- Twitter Card -->
<meta name="twitter:card" content="summary_large_image">
<meta name="twitter:title" content="LexMesh — AI-Powered Compliance Engine">
<meta name="twitter:description" content="Upload your policy PDF. Get instant GDPR, HIPAA, RBI &amp; SOC 2 compliance scores, gap analysis, and a prioritised action plan.">
<meta name="twitter:image" content="https://placehold.co/1200x630/101713/eae3d2?text=LexMesh+Compliance+Engine">
''', shared=True)


# ============================================================
# FRAMEWORKS
# ============================================================

FRAMEWORKS = {
    "All Standards (Full Scope)": [
        "gdpr",
        "hipaa",
        "rbi",
        "soc2",
    ],

    "EU GDPR": [
        "gdpr",
    ],

    "US HIPAA": [
        "hipaa",
    ],

    "RBI Cyber Framework": [
        "rbi",
    ],

    "SOC 2 Type II": [
        "soc2",
    ],
}


# ============================================================
# LOAD CUSTOM CSS
# ============================================================

theme_path = Path("ui/styles/theme.css")

if theme_path.exists():

    theme_css = theme_path.read_text(
        encoding="utf-8"
    )

    ui.add_head_html(
        f"<style>{theme_css}</style>",
        shared=True,
    )


@ui.page("/login")
def login_page():
    if auth.get_current_user():
        ui.navigate.to('/')
        return
        
    ui.colors(primary='#558b63', secondary='#34d399', accent='#059669', positive='#558b63')

    # Main wrapper with gradient background to mimic the design
    with ui.column().classes("w-full h-screen items-center justify-center relative overflow-hidden").style("background: linear-gradient(135deg, #f3f8f4 0%, #e8f2ea 100%);"):
        
        # Decorative circles (optional, just for background vibe)
        ui.element('div').classes('absolute top-[-10%] left-[-10%] w-[40%] h-[40%] rounded-full opacity-30 blur-3xl bg-[#d1e8d6]')
        ui.element('div').classes('absolute bottom-[-10%] right-[-10%] w-[50%] h-[50%] rounded-full opacity-30 blur-3xl bg-[#cce3d2]')

        with ui.card().classes("w-96 p-10 items-center shadow-[0_15px_40px_-5px_rgba(78,121,93,0.4)] border-2 border-[#4e795d]/60 rounded-3xl bg-[#f8f6f0]/95 backdrop-blur-sm z-10 gap-0"):
            
            # Shield Icon in a circle
            with ui.element('div').classes('w-16 h-16 rounded-full bg-emerald-50 flex items-center justify-center mb-4'):
                from ui.components.lucide import lucide_icon
                lucide_icon("shield", size=32, class_name="text-emerald-500")
            
            # Titles
            ui.label("LexMesh").classes("text-3xl font-bold text-slate-800 tracking-tight mb-1")
            ui.label("Sign in to your account").classes("text-sm text-slate-500 font-medium mb-8")
            
            # Show confirmation success banner if redirected from email verification
            ui.add_body_html('''
            <script>
            (function() {
                var urlParams = new URLSearchParams(window.location.search);
                if (urlParams.get('confirmed') === '1') {
                    var banner = document.createElement('div');
                    banner.style.cssText = 'background:#d1fae5;border:1px solid #6ee7b7;color:#065f46;border-radius:8px;padding:10px 16px;margin-bottom:16px;font-size:0.875rem;text-align:center;font-weight:500;';
                    banner.innerHTML = '✅ Email verified! You can now log in.';
                    var card = document.querySelector('.nicegui-card');
                    if (card) card.prepend(banner);
                }
            })();
            </script>
            ''')
            
            # Form Container
            with ui.column().classes("w-full gap-4"):
                # Email Input
                email = ui.input("Email").classes("w-full text-md").props('outlined rounded bg-color="white" color="emerald"')
                with email.add_slot('prepend'):
                    ui.icon('mail_outline').classes('text-slate-400')
                
                # Password Input
                password = ui.input("Password", password=True, password_toggle_button=True).classes("w-full text-md").props('outlined rounded bg-color="white" color="emerald"')
                with password.add_slot('prepend'):
                    ui.icon('lock_outline').classes('text-slate-400')
                
                # Login Action
                def do_login():
                    if not email.value or not password.value:
                        ui.notify("Please enter both email and password.", type="warning")
                        return
                    success, msg = auth.sign_in(email.value, password.value)
                    if success:
                        ui.notify("Logged in successfully!", type="positive")
                        ui.navigate.to('/')
                    else:
                        err = str(msg)
                        if 'email' in err.lower() and 'confirm' in err.lower():
                            ui.notify("Please verify your email first. Check your inbox.", type="warning", timeout=6000)
                        else:
                            ui.notify(err, type="negative")

                ui.button("LOG IN", on_click=do_login).classes("w-full mt-2 h-12 rounded-lg font-bold text-white shadow-lg shadow-emerald-500/30 tracking-wider").props("color=primary unelevated icon-right=arrow_forward")
            
            # Footer Divider
            with ui.row().classes("w-full items-center justify-center mt-8 gap-3"):
                ui.element('div').classes("h-px bg-slate-200 flex-grow")
                with ui.row().classes("items-center gap-1 text-sm font-medium"):
                    ui.label("Don't have an account?").classes("text-slate-500")
                    ui.link("Sign Up", "/signup").classes("text-emerald-600 hover:text-emerald-700 transition-colors")
                ui.element('div').classes("h-px bg-slate-200 flex-grow")

@ui.page("/signup")
def signup_page():
    if auth.get_current_user():
        ui.navigate.to('/')
        return
        
    ui.colors(primary='#558b63', secondary='#34d399', accent='#059669', positive='#558b63')

    # Main wrapper with gradient background
    with ui.column().classes("w-full h-screen items-center justify-center relative overflow-hidden").style("background: linear-gradient(135deg, #f3f8f4 0%, #e8f2ea 100%);"):
        
        ui.element('div').classes('absolute top-[-10%] left-[-10%] w-[40%] h-[40%] rounded-full opacity-30 blur-3xl bg-[#d1e8d6]')
        ui.element('div').classes('absolute bottom-[-10%] right-[-10%] w-[50%] h-[50%] rounded-full opacity-30 blur-3xl bg-[#cce3d2]')

        with ui.card().classes("w-96 p-10 items-center shadow-[0_15px_40px_-5px_rgba(78,121,93,0.4)] border-2 border-[#4e795d]/60 rounded-3xl bg-[#f8f6f0]/95 backdrop-blur-sm z-10 gap-0"):
            
            with ui.element('div').classes('w-16 h-16 rounded-full bg-emerald-50 flex items-center justify-center mb-4'):
                from ui.components.lucide import lucide_icon
                lucide_icon("shield", size=32, class_name="text-emerald-500")
            
            ui.label("LexMesh").classes("text-3xl font-bold text-slate-800 tracking-tight mb-1")
            ui.label("Create a new account").classes("text-sm text-slate-500 font-medium mb-8")
            
            with ui.column().classes("w-full gap-4"):
                email = ui.input("Email").classes("w-full text-md").props('outlined rounded bg-color="white" color="emerald"')
                with email.add_slot('prepend'):
                    ui.icon('mail_outline').classes('text-slate-400')
                
                password = ui.input("Password", password=True, password_toggle_button=True).classes("w-full text-md").props('outlined rounded bg-color="white" color="emerald"')
                with password.add_slot('prepend'):
                    ui.icon('lock_outline').classes('text-slate-400')
                
                def do_signup():
                    if not email.value or not password.value:
                        ui.notify("Please enter both email and password.", type="warning")
                        return
                    if len(password.value) < 6:
                        ui.notify("Password must be at least 6 characters.", type="warning")
                        return
                    success, msg = auth.sign_up(email.value, password.value)
                    if success and msg == "CHECK_EMAIL":
                        # Clear the form and show a verification pending message
                        email.value = ''
                        password.value = ''
                        ui.notify(
                            "Account created! Please check your inbox and click the verification link to activate your account.",
                            type="positive",
                            timeout=8000
                        )
                        # Navigate to a confirmation-pending page
                        ui.navigate.to('/verify-email')
                    elif success:
                        ui.notify("Signed up successfully! Welcome to LexMesh.", type="positive")
                        ui.navigate.to('/')
                    else:
                        ui.notify(msg, type="negative")

                ui.button("SIGN UP", on_click=do_signup).classes("w-full mt-2 h-12 rounded-lg font-bold text-white shadow-lg shadow-emerald-500/30 tracking-wider").props("color=primary unelevated icon-right=person_add")
            
            with ui.row().classes("w-full items-center justify-center mt-8 gap-3"):
                ui.element('div').classes("h-px bg-slate-200 flex-grow")
                with ui.row().classes("items-center gap-1 text-sm font-medium"):
                    ui.label("Already have an account?").classes("text-slate-500")
                    ui.link("Log In", "/login").classes("text-emerald-600 hover:text-emerald-700 transition-colors")
                ui.element('div').classes("h-px bg-slate-200 flex-grow")

# ============================================================
# EMAIL VERIFICATION PENDING PAGE
# ============================================================

@ui.page("/verify-email")
def verify_email_page():
    ui.colors(primary='#558b63', secondary='#34d399', accent='#059669', positive='#558b63')
    with ui.column().classes("w-full h-screen items-center justify-center").style("background: linear-gradient(135deg, #f3f8f4 0%, #e8f2ea 100%);"):
        with ui.card().classes("w-96 p-10 items-center shadow-[0_15px_40px_-5px_rgba(78,121,93,0.4)] border-2 border-[#4e795d]/60 rounded-3xl bg-[#f8f6f0]/95 z-10 gap-0"):
            with ui.element('div').classes('w-20 h-20 rounded-full bg-emerald-50 flex items-center justify-center mb-6'):
                ui.icon('mark_email_read').classes('text-emerald-500 text-5xl')
            ui.label('Check Your Email').classes('text-2xl font-bold text-slate-800 mb-3 text-center')
            ui.label('We have sent a verification link to your email address.').classes('text-sm text-slate-500 text-center mb-2')
            ui.label('Please click the link in the email to activate your account, then log in.').classes('text-sm text-slate-500 text-center mb-8')
            ui.button('Go to Login', on_click=lambda: ui.navigate.to('/login')).classes('w-full h-12 rounded-lg font-bold text-white').props('color=primary unelevated icon-right=login')

# ============================================================
# EMAIL CONFIRMATION CALLBACK PAGE (Supabase redirects here)
# ============================================================

@ui.page("/confirm")
def confirm_page():
    """Supabase redirects here after user clicks the email confirmation link.
    URL contains: /confirm#access_token=...&refresh_token=...&type=signup
    We extract the tokens via JS, set the session, then redirect to login.
    """
    ui.colors(primary='#558b63')
    with ui.column().classes("w-full h-screen items-center justify-center").style("background: linear-gradient(135deg, #f3f8f4 0%, #e8f2ea 100%);"):
        with ui.card().classes("w-96 p-10 items-center shadow-[0_15px_40px_-5px_rgba(78,121,93,0.4)] border-2 border-[#4e795d]/60 rounded-3xl bg-[#f8f6f0]/95 z-10 gap-0"):
            with ui.element('div').classes('w-20 h-20 rounded-full bg-emerald-50 flex items-center justify-center mb-6'):
                ui.icon('verified_user').classes('text-emerald-500 text-5xl')
            status_label = ui.label('Verifying your email...').classes('text-xl font-bold text-slate-800 mb-3 text-center')
            sub_label = ui.label('Please wait a moment.').classes('text-sm text-slate-500 text-center mb-8')
            login_btn = ui.button('Go to Login', on_click=lambda: ui.navigate.to('/login')).classes('w-full h-12 rounded-lg font-bold text-white').props('color=primary unelevated icon-right=login')
            login_btn.set_visibility(False)

    # JS: Read tokens from the URL hash fragment and POST them to a server endpoint
    ui.add_body_html('''
    <script>
    (function() {
        var hash = window.location.hash.substring(1);
        var params = {};
        hash.split('&').forEach(function(part) {
            var item = part.split('=');
            if (item.length === 2) params[item[0]] = decodeURIComponent(item[1]);
        });
        var accessToken = params['access_token'];
        var refreshToken = params['refresh_token'];
        var type = params['type'];
        if (accessToken && (type === 'signup' || type === 'email_change' || type === 'recovery')) {
            fetch('/api/confirm-email', {
                method: 'POST',
                headers: {'Content-Type': 'application/json'},
                body: JSON.stringify({access_token: accessToken, refresh_token: refreshToken})
            })
            .then(function(r) { return r.json(); })
            .then(function(data) {
                if (data.success) {
                    window.location.href = '/login?confirmed=1';
                } else {
                    document.querySelector('.text-xl').textContent = 'Verification Failed';
                    document.querySelector('.text-sm').textContent = data.error || 'Invalid or expired link. Please sign up again.';
                }
            })
            .catch(function() {
                document.querySelector('.text-xl').textContent = 'Error';
                document.querySelector('.text-sm').textContent = 'Something went wrong. Please try again.';
            });
        } else {
            window.location.href = '/login';
        }
    })();
    </script>
    ''')

# ============================================================
# DASHBOARD
# ============================================================

@ui.page("/")
def root_redirect():
    """Always redirect / to /dashboard so the URL is clean."""
    ui.navigate.to('/dashboard')

@ui.page("/dashboard")
@ui.page("/audit")
@ui.page("/frameworks")
def dashboard(request: Request):
    if not auth.get_current_user():
        ui.navigate.to('/login')
        return


    # Set Quasar Brand Colors for this page
    ui.colors(
        primary='#4e795d',
        secondary='#eae3d2',
        accent='#8a7642',
        dark='#101713',
        positive='#3b6349',
        negative='#9e3232',
        info='#3b6b78',
        warning='#b45339',
    )

    # ========================================================
    # PAGE STATE
    #
    # IMPORTANT:
    # This state belongs to THIS browser page/session.
    # ========================================================

    page_state = {
        "pdf_bytes": None,
        "pdf_name": "",
        "master_report": None,
        "selected_frameworks": [
            "gdpr",
            "hipaa",
            "rbi",
            "soc2",
        ],
    }

    # ========================================================
    # VIEW STATE
    # ========================================================

    initial_tab = "dashboard"
    if request:
        if request.url.path == "/audit":
            initial_tab = "audit"
        elif request.url.path == "/frameworks":
            initial_tab = "frameworks"

    # ========================================================
    # HEADER
    # ========================================================

    header = create_header(
        active_tab=initial_tab,
    )

    # ========================================================
    # SIDEBAR — only on audit page
    # ========================================================

    if initial_tab == "audit":
        sidebar = create_sidebar(
            gemini_connected=bool(
                config.GEMINI_API_KEY
            ),
            groq_connected=bool(
                config.GROQ_API_KEY
            ),
            supabase_connected=bool(
                supabase_db.is_connected()
            ),
        )
        # Show only audit controls in sidebar
        sidebar["dash_nav_container"].set_visibility(False)
        sidebar["audit_controls_container"].set_visibility(True)

    # ========================================================
    # DASHBOARD LANDING VIEW
    # ========================================================

    if initial_tab == "dashboard":
        with ui.column().classes("w-full p-6 gap-5"):
            create_dashboard_landing(
                on_run_new_audit=lambda: ui.navigate.to('/audit'),
            )
        return  # Dashboard page is complete, no audit UI needed

    # ========================================================
    # FRAMEWORKS PAGE
    # ========================================================

    if initial_tab == "frameworks":
        from ui.components.frameworks_page import create_frameworks_page
        create_frameworks_page()
        return

    # ========================================================
    # AUDIT VIEW (existing interface)
    # ========================================================

    audit_view = ui.column().classes(
        "w-full p-6 gap-5"
    )

    with audit_view:

        # ----------------------------------------------------
        # TITLE
        # ----------------------------------------------------

        with ui.column().classes(
            "gap-1"
        ):

            ui.label(
                "LexMesh Compliance Dashboard"
            ).classes(
                "text-3xl font-bold lex-page-title"
            )

            ui.label(
                "Policy-Centric Multi-Framework Compliance Engine"
            ).classes(
                "text-sm lex-page-subtitle"
            )

        # ----------------------------------------------------
        # STATUS
        # ----------------------------------------------------

        status = ui.label(
            "Upload a company policy PDF to begin."
        ).classes(
            "lex-analysis-status"
        )

        # ====================================================
        # HORIZONTAL TABS
        # ====================================================

        with ui.tabs().classes(
            "w-full lex-dashboard-tabs"
        ) as tabs:

            with ui.tab("score", label="").classes("lex-tab-item"):
                with ui.row().classes("items-center gap-2"):
                    lucide_icon("bar-chart-3", size=18)
                    ui.label("Score & Framework")

            with ui.tab("action", label="").classes("lex-tab-item"):
                with ui.row().classes("items-center gap-2"):
                    lucide_icon("clipboard-list", size=18)
                    ui.label("Priority Action Plan")

            with ui.tab("gaps", label="").classes("lex-tab-item"):
                with ui.row().classes("items-center gap-2"):
                    lucide_icon("shield-alert", size=18)
                    ui.label("Detailed Policy Gaps")

            with ui.tab("compliant", label="").classes("lex-tab-item"):
                with ui.row().classes("items-center gap-2"):
                    lucide_icon("check-circle", size=18)
                    ui.label("Compliant Areas")

            with ui.tab("posture", label="").classes("lex-tab-item"):
                with ui.row().classes("items-center gap-2"):
                    lucide_icon("file-check", size=18)
                    ui.label("Executive Posture")

            with ui.tab("export", label="").classes("lex-tab-item"):
                with ui.row().classes("items-center gap-2"):
                    lucide_icon("file-down", size=18)
                    ui.label("Report Export")

        # ====================================================
        # TAB PANELS
        # ====================================================

        with ui.tab_panels(
            tabs,
            value="score",
        ).classes(
            "w-full"
        ):

            # =================================================
            # 1. SCORE TAB
            # =================================================

            with ui.tab_panel(
                "score"
            ):

                with ui.column().classes("w-full") as score_container:

                    ui.label(
                        "Upload a company policy PDF and click Run Analysis to view compliance scores."
                    ).classes(
                        "lex-empty-state"
                    )

            # =================================================
            # 2. ACTION PLAN
            # =================================================

            with ui.tab_panel(
                "action"
            ):

                with ui.column().classes("w-full") as action_container:

                    ui.label(
                        "Run an analysis to view the action plan."
                    ).classes(
                        "lex-empty-state"
                    )

            # =================================================
            # 3. DETAILED GAPS
            # =================================================

            with ui.tab_panel(
                "gaps"
            ):

                with ui.column().classes("w-full") as gap_container:

                    ui.label(
                        "Run an analysis to view detailed gaps."
                    ).classes(
                        "lex-empty-state"
                    )

            # =================================================
            # 4. COMPLIANT AREAS
            # =================================================

            with ui.tab_panel(
                "compliant"
            ):

                with ui.column().classes("w-full") as compliant_container:

                    ui.label(
                        "Run an analysis to view compliant areas."
                    ).classes(
                        "lex-empty-state"
                    )

            # =================================================
            # 5. POLICY POSTURE
            # =================================================

            with ui.tab_panel(
                "posture"
            ):

                with ui.column().classes("w-full") as posture_container:

                    ui.label(
                        "Run an analysis to view policy posture."
                    ).classes(
                        "lex-empty-state"
                    )

            # =================================================
            # 6. EXPORT
            # =================================================

            with ui.tab_panel(
                "export"
            ):

                with ui.column().classes("w-full") as export_container:

                    ui.label(
                        "Run an analysis to enable exports."
                    ).classes(
                        "lex-empty-state"
                    )

    # ========================================================
    # PDF METADATA EXTRACTION
    # ========================================================

    def extract_metadata_from_pdf(
        pdf_bytes: bytes,
        filename: str = "",
    ):
        try:
            doc = fitz.open(
                stream=pdf_bytes,
                filetype="pdf",
            )
            if len(doc) == 0:
                return "", ""

            # Check up to first 2 pages
            page_texts = [doc[i].get_text() for i in range(min(2, len(doc)))]
            full_header_text = "\n".join(page_texts)
            lines = [l.strip() for l in full_header_text.splitlines() if l.strip()]

            company = ""
            policy = ""

            # ----------------------------------------------------
            # 1. COMPANY EXTRACTION (Multi-Tier Robust Strategy)
            # ----------------------------------------------------

            # Tier 1: Key-Value label pattern (e.g. "Company QuickCart Retail LLC", "Company: Acme Corp")
            for line in lines:
                kv_match = re.match(
                    r"^(?:Company|Organization|Legal\s+Entity)(?:\s+Name)?\s*[:\t\-–—|]?\s+(.+)$",
                    line,
                    re.IGNORECASE,
                )
                if kv_match:
                    candidate = kv_match.group(1).strip()
                    if len(candidate) >= 2 and not re.match(r"^(?:Name|Title|Address|Location|Description|Registered|Effective)$", candidate, re.IGNORECASE):
                        company = candidate
                        break

            # Tier 2: Two-line table cell format (Line 1: "Company", Line 2: "QuickCart Retail LLC")
            if not company:
                for i, line in enumerate(lines):
                    if re.match(r"^(?:Company|Organization|Legal\s+Entity)(?:\s+Name)?\s*[:\t\-–—|]?$", line, re.IGNORECASE):
                        if i + 1 < len(lines):
                            candidate = lines[i + 1].strip()
                            if candidate and not re.match(r"^(?:Registered|Effective|Website|Contact|Version|Date|Review|Document)\b", candidate, re.IGNORECASE):
                                company = candidate
                                break

            # Tier 3: Legal Preamble / Introduction Sentence
            # e.g. "This Privacy Policy describes how QuickCart Retail LLC ('QuickCart', 'we') handles..."
            if not company:
                preamble_match = re.search(
                    r"(?:This\s+(?:[A-Za-z\s]+)?Policy\s+(?:describes|explains|governs|sets\s+forth|outlines)\s+how\s+)"
                    r"([A-Z0-9][A-Za-z0-9&.,'’\- ]+?)"
                    r"(?:\s*\((?:['\"‘“]|we\b|collectively|the\b)|,|\s+handles|\s+collects|\s+uses|\s+processes|\s+operates|\s+ships)",
                    full_header_text,
                    re.IGNORECASE,
                )
                if preamble_match:
                    candidate = preamble_match.group(1).strip()
                    if 2 <= len(candidate) <= 60 and not re.search(r"\b(?:Policy|Notice|Document|Statement)\b", candidate, re.IGNORECASE):
                        company = candidate

            if not company:
                preamble_match2 = re.search(
                    r"(?:privacy\s+practices\s+of\s+|welcome\s+to\s+|at\s+)"
                    r"([A-Z0-9][A-Za-z0-9&.,'’\- ]{2,50}?)"
                    r"(?:\s*\((?:['\"‘“]|we\b|collectively)|,\s*we\b|\.\s|\n)",
                    full_header_text,
                    re.IGNORECASE,
                )
                if preamble_match2:
                    candidate = preamble_match2.group(1).strip()
                    if 2 <= len(candidate) <= 60:
                        company = candidate

            # Tier 4: Corporate Entity Suffix Match (Comprehensive legal suffixes)
            if not company:
                corp_suffix_match = re.search(
                    r"\b([A-Z][A-Za-z0-9&.]*(?:\s+[A-Z0-9][A-Za-z0-9&.]*){0,5}\s+"
                    r"(?:LLC|L\.L\.C\.|LLP|L\.L\.P\.|Ltd\.?|LTD|Limited|Inc\.?|INC|Incorporated|"
                    r"Corp\.?|CORP|Corporation|Pvt\.?\s+Ltd\.?|Private\s+Limited|Co\.?|Company|"
                    r"GmbH|AG|PLC|Retail\s+LLC|Technologies|Technology|Systems|AI|Labs|Solutions|"
                    r"Holdings|Group|Enterprises|Ventures|Partners|Services|Bank|Capital))\b",
                    full_header_text,
                )
                if corp_suffix_match:
                    candidate = re.sub(r"\s+", " ", corp_suffix_match.group(1)).strip()
                    if not re.search(r"\b(?:Privacy|Security|Cookie|Terms|Compliance)\b", candidate, re.IGNORECASE):
                        company = candidate

            # Tier 5: Title Block on Page 1 (Line directly above PRIVACY POLICY / SECURITY POLICY)
            if not company:
                for i, line in enumerate(lines[:10]):
                    if re.search(r"\b(?:PRIVACY\s+POLICY|SECURITY\s+POLICY|DATA\s+PROTECTION)\b", line, re.IGNORECASE):
                        if i > 0:
                            candidate = lines[i - 1].strip()
                            if len(candidate) >= 3 and not re.search(r"\b(?:Page\s+\d+|Version|\d{4}|Confidential|Table\s+of)\b", candidate, re.IGNORECASE):
                                company = candidate
                                break

            # Tier 6: PDF Document Metadata Properties
            if not company and doc.metadata:
                meta_author = doc.metadata.get("author") or doc.metadata.get("creator") or ""
                meta_author = meta_author.strip()
                if meta_author and len(meta_author) >= 3 and not re.search(r"(?:Word|Acrobat|PDF|Canva|LaTeX|ReportLab|Writer|InDesign)", meta_author, re.IGNORECASE):
                    company = meta_author

            # Tier 7: Filename Fallback (e.g. "SampleInput_QuickCart_Policy.pdf" -> "QuickCart")
            if not company and filename:
                base = os.path.splitext(filename)[0]
                base = re.sub(r"^(?:SampleInput_|Sample_Input_|Sample_|Input_|Test_|Demo_|Draft_)", "", base, flags=re.IGNORECASE)
                base = re.sub(r"(?:_Policy|-Policy|_Privacy|-Privacy|_Security|-Security|_v\d+.*|-v\d+.*|_condensed.*)$", "", base, flags=re.IGNORECASE)
                base = re.sub(r"[-_]+", " ", base).strip()
                if base and len(base) >= 2:
                    company = base

            # Clean company name
            if company:
                company = re.sub(r"\s+", " ", company).strip()

            # ----------------------------------------------------
            # 2. POLICY NAME & VERSION EXTRACTION
            # ----------------------------------------------------

            known_types = [
                ("Information Security Policy", r"Information\s+Security\s+Policy"),
                ("Data Protection Policy", r"Data\s+Protection\s+Policy"),
                ("Incident Response Plan", r"Incident\s+Response\s+(?:Plan|Policy)"),
                ("Access Control Policy", r"Access\s+Control\s+Policy"),
                ("Acceptable Use Policy", r"Acceptable\s+Use\s+Policy"),
                ("Customer Data Statement", r"Customer\s+Data\s+Statement"),
                ("Privacy Policy", r"Privacy\s+Policy"),
                ("Privacy Notice", r"Privacy\s+Notice"),
                ("Security Policy", r"Security\s+Policy"),
                ("Terms of Service", r"Terms\s+of\s+(?:Service|Use)"),
            ]

            policy_type = ""
            for p_name, p_pattern in known_types:
                if re.search(r"\b" + p_pattern + r"\b", full_header_text, re.IGNORECASE):
                    policy_type = p_name
                    break

            if not policy_type:
                policy_type = "Privacy Policy"

            # Version detection
            version_str = ""
            v_match = re.search(
                r"(?:Document\s+Version|Policy\s+Version|Version|Ver\.?|v)\s*[:\s\-]*([vV]?\d+(?:\.\d+)*)\b",
                full_header_text,
                re.IGNORECASE,
            )
            if v_match:
                v_val = v_match.group(1).strip()
                version_str = v_val if v_val.lower().startswith("v") else f"v{v_val}"
            else:
                v_match2 = re.search(r"\b(v\d+\.\d+)\b", full_header_text, re.IGNORECASE)
                if v_match2:
                    version_str = v_match2.group(1).strip()

            if policy_type and version_str:
                policy = f"{policy_type} {version_str}"
            elif policy_type:
                policy = policy_type
            elif version_str:
                policy = f"Enterprise Policy {version_str}"
            else:
                policy = "Enterprise Privacy Policy"

            return company.strip(), policy.strip()

        except Exception as e:
            logger.error("[LexMesh] Metadata extraction error: %s", e)
            fallback_co = ""
            if filename:
                base = os.path.splitext(filename)[0]
                base = re.sub(r"^(?:SampleInput_|Sample_Input_|Sample_|Input_|Test_|Demo_)", "", base, flags=re.IGNORECASE)
                base = re.sub(r"(?:_Policy|-Policy|_Privacy|-Privacy|_v\d+.*|-v\d+.*)$", "", base, flags=re.IGNORECASE)
                fallback_co = re.sub(r"[-_]+", " ", base).strip()
            return fallback_co, "Privacy Policy"

    # ========================================================
    # REPORT FILTER
    # ========================================================

    def filter_report_payload(
        report_json,
        target_fw_keys,
    ):

        # All frameworks selected
        if (
            not target_fw_keys
            or set(target_fw_keys)
            == {
                "gdpr",
                "hipaa",
                "rbi",
                "soc2",
            }
        ):

            return report_json

        filtered = json.loads(
            json.dumps(report_json)
        )

        # ----------------------------------------------------
        # SUMMARY
        # ----------------------------------------------------

        summary = filtered.setdefault(
            "summary",
            {},
        )

        framework_summaries = (
            summary.get(
                "framework_summaries",
                {},
            )
        )

        selected_summaries = {
            key: value
            for key, value in framework_summaries.items()
            if key in target_fw_keys
        }

        summary[
            "framework_summaries"
        ] = selected_summaries

        # ----------------------------------------------------
        # OVERALL SCORE
        # ----------------------------------------------------

        scores = []

        for value in selected_summaries.values():

            try:

                score = float(
                    str(
                        value.get(
                            "score",
                            0,
                        )
                    ).replace(
                        "%",
                        "",
                    )
                )

                scores.append(score)

            except Exception:
                pass

        if scores:

            overall_score = int(
                round(
                    sum(scores)
                    / len(scores)
                )
            )

            summary[
                "overall_score"
            ] = overall_score

            if overall_score >= 80:

                summary[
                    "overall_risk"
                ] = (
                    "LOW RISK — "
                    "High Compliance Posture"
                )

            elif overall_score >= 60:

                summary[
                    "overall_risk"
                ] = (
                    "MEDIUM RISK — "
                    "Operational Gaps Exist"
                )

            else:

                summary[
                    "overall_risk"
                ] = (
                    "HIGH RISK — "
                    "Critical Compliance Omissions"
                )

        # ----------------------------------------------------
        # POLICY DOMAIN BREAKDOWN
        # ----------------------------------------------------

        domains = filtered.get(
            "policy_domain_breakdown",
            [],
        )

        for domain in domains:

            framework_scores = (
                domain.get(
                    "framework_scores",
                    {},
                )
            )

            selected_scores = {
                key: value
                for key, value in framework_scores.items()
                if key in target_fw_keys
            }

            domain[
                "framework_scores"
            ] = selected_scores

            if selected_scores:

                values = []

                for value in selected_scores.values():

                    try:

                        values.append(
                            float(
                                str(value)
                                .replace(
                                    "%",
                                    "",
                                )
                            )
                        )

                    except Exception:
                        pass

                if values:

                    domain[
                        "score"
                    ] = (
                        f"{int(round(sum(values) / len(values)))}%"
                    )

        # ----------------------------------------------------
        # DETAILED GAPS
        # ----------------------------------------------------

        detailed_gaps = (
            filtered.get(
                "detailed_policy_gaps",
                {},
            )
        )

        for domain_data in detailed_gaps.values():

            framework_gaps = (
                domain_data.get(
                    "framework_gaps",
                    {},
                )
            )

            domain_data[
                "framework_gaps"
            ] = {
                key: value
                for key, value in framework_gaps.items()
                if key in target_fw_keys
            }

        # ----------------------------------------------------
        # FLAT GAPS
        # ----------------------------------------------------

        all_gaps = filtered.get(
            "all_gaps_flat",
            filtered.get(
                "detailed_gaps",
                [],
            ),
        )

        filtered[
            "all_gaps_flat"
        ] = [
            gap
            for gap in all_gaps
            if gap.get(
                "framework"
            ) in target_fw_keys
        ]

        # ----------------------------------------------------
        # ACTION PLAN
        # ----------------------------------------------------

        plan = filtered.get(
            "priority_action_plan",
            {},
        )

        def matches_framework(item):

            tag = str(
                item.get(
                    "Framework Standard",
                    item.get(
                        "framework_tag",
                        "",
                    ),
                )
            ).lower()

            for framework in target_fw_keys:

                if (
                    framework == "gdpr"
                    and "gdpr" in tag
                ):
                    return True

                if (
                    framework == "hipaa"
                    and "hipaa" in tag
                ):
                    return True

                if (
                    framework == "rbi"
                    and "rbi" in tag
                ):
                    return True

                if (
                    framework == "soc2"
                    and (
                        "soc2" in tag
                        or "soc" in tag
                    )
                ):
                    return True

            return False

        filtered[
            "priority_action_plan"
        ] = {

            "p1_critical": [
                item
                for item in plan.get(
                    "p1_critical",
                    [],
                )
                if matches_framework(item)
            ],

            "p2_high": [
                item
                for item in plan.get(
                    "p2_high",
                    [],
                )
                if matches_framework(item)
            ],

            "p3_medium": [
                item
                for item in plan.get(
                    "p3_medium",
                    [],
                )
                if matches_framework(item)
            ],
        }

        # ----------------------------------------------------
        # COMPLIANT AREAS
        # ----------------------------------------------------
        comp_areas = filtered.get("compliant_areas", [])
        filtered["compliant_areas"] = [
            item
            for item in comp_areas
            if matches_framework(item)
        ]

        return filtered

    # ========================================================
    # UPLOAD CALLBACK
    #
    # IMPORTANT:
    # Use NiceGUI's dedicated .on_upload().
    # ========================================================

    async def handle_upload(event):

        try:

            print()
            print(
                "=========================================="
            )
            print(
                "[LexMesh] UPLOAD EVENT RECEIVED"
            )
            print(
                "=========================================="
            )

            uploaded_file = event.file

            if uploaded_file is None:

                raise ValueError(
                    "NiceGUI did not provide an uploaded file."
                )

            print(
                "[LexMesh] File:",
                uploaded_file.name,
            )

            # ------------------------------------------------
            # READ FILE
            # ------------------------------------------------

            pdf_data = await uploaded_file.read()

            if pdf_data is None:

                raise ValueError(
                    "Uploaded file returned no data."
                )

            pdf_data = bytes(
                pdf_data
            )

            if len(pdf_data) == 0:

                raise ValueError(
                    "Uploaded PDF is empty."
                )

            # ------------------------------------------------
            # SAVE TO PAGE STATE
            # ------------------------------------------------

            page_state[
                "pdf_bytes"
            ] = pdf_data

            page_state[
                "pdf_name"
            ] = uploaded_file.name

            print(
                "[LexMesh] PDF bytes:",
                len(pdf_data),
            )

            # ------------------------------------------------
            # TRY METADATA EXTRACTION
            # ------------------------------------------------

            company, policy = extract_metadata_from_pdf(
                pdf_data,
                filename=uploaded_file.name,
            )

            print(
                "[LexMesh] Extracted company:",
                company,
            )

            print(
                "[LexMesh] Extracted policy:",
                policy,
            )

            # ------------------------------------------------
            # POPULATE INPUTS
            # ------------------------------------------------

            if company:
                sidebar[
                    "company_name"
                ].value = company
                sidebar[
                    "company_name"
                ].update()

            if policy:
                sidebar[
                    "policy_name"
                ].value = policy
                sidebar[
                    "policy_name"
                ].update()

            # ------------------------------------------------
            # SUCCESS
            # ------------------------------------------------

            detected_parts = []
            if company:
                detected_parts.append(f"Company: {company}")
            if policy:
                detected_parts.append(f"Policy: {policy}")
            det_str = f" • Detected { ' | '.join(detected_parts) }" if detected_parts else ""

            status.set_text(
                f"Document {uploaded_file.name} uploaded and ready for analysis.{det_str}"
            )

            ui.notify(
                f"Recognized: {company or 'Company'} — {policy or 'Policy'}",
                type="positive",
            )

            logger.info(
                "PDF ready for analysis: %s (%d bytes, company='%s', policy='%s')",
                page_state['pdf_name'],
                len(pdf_data),
                company,
                policy,
            )

        except Exception as e:

            page_state["pdf_bytes"] = None
            page_state["pdf_name"] = ""

            status.set_text(f"❌ Upload failed: {e}")

            ui.notify(
                f"Upload failed: {e}",
                type="negative",
            )

            logger.error("PDF upload error: %s", e, exc_info=True)

    # --------------------------------------------------------
    # THIS IS THE IMPORTANT CHANGE
    # --------------------------------------------------------

    sidebar[
        "uploaded_file"
    ].on_upload(
        handle_upload
    )

    # ========================================================
    # RUN ANALYSIS
    # ========================================================

    async def run_analysis():

        logger.info("=== RUN ANALYSIS TRIGGERED ===")

        # ----------------------------------------------------
        # GET CURRENT PAGE PDF
        # ----------------------------------------------------

        pdf_bytes = page_state.get(
            "pdf_bytes"
        )

        logger.debug(
            "PDF state: %s (%d bytes)",
            "AVAILABLE" if pdf_bytes else "EMPTY",
            len(pdf_bytes) if pdf_bytes else 0,
        )

        # ----------------------------------------------------
        # CHECK PDF
        # ----------------------------------------------------

        if (
            pdf_bytes is None
            or len(pdf_bytes) == 0
        ):

            status.set_text(
                "Please upload a company policy PDF document first."
            )

            ui.notify(
                "Please upload a PDF first.",
                type="warning",
            )

            return

        button = sidebar[
            "run_button"
        ]

        button.disable()

        try:

            # =================================================
            # COMPANY
            # =================================================

            company = (
                sidebar[
                    "company_name"
                ].value
                or "Uploaded Organization"
            ).strip()

            # =================================================
            # POLICY
            # =================================================

            policy = (
                sidebar[
                    "policy_name"
                ].value
                or "Company Policy Document"
            ).strip()

            # =================================================
            # FRAMEWORK
            # =================================================

            selected_fw_keys = []
            if sidebar["gdpr_checkbox"].value:
                selected_fw_keys.append("gdpr")
            if sidebar["hipaa_checkbox"].value:
                selected_fw_keys.append("hipaa")
            if sidebar["rbi_checkbox"].value:
                selected_fw_keys.append("rbi")
            if sidebar["soc2_checkbox"].value:
                selected_fw_keys.append("soc2")

            if not selected_fw_keys:
                status.set_text("Please select at least one evaluation framework in the sidebar.")
                ui.notify("Please select at least one framework.", type="warning")
                button.enable()
                return

            page_state[
                "selected_frameworks"
            ] = selected_fw_keys

            logger.info(
                "Analysis requested — Company: %s | Policy: %s | Frameworks: %s",
                company, policy, selected_fw_keys,
            )

            # =================================================
            # EXTRACT POLICY TEXT
            # =================================================

            status.set_text(
                "📖 Reading policy PDF..."
            )

            logger.info("Opening PDF for text extraction...")

            doc = fitz.open(
                stream=pdf_bytes,
                filetype="pdf",
            )

            policy_pages = []

            for page in doc:

                text = page.get_text()

                if text:

                    policy_pages.append(
                        text
                    )

            doc.close()

            policy_text = "\n".join(
                policy_pages
            )

            logger.info("Extracted %d characters from policy PDF.", len(policy_text))

            if not policy_text.strip():

                raise ValueError(
                    "No readable text was found "
                    "inside the uploaded PDF."
                )

            # =================================================
            # RUN REAL ADK PIPELINE
            # =================================================

            status.set_text(
                "Running LexMesh compliance analysis..."
            )

            logger.info("Calling ADK pipeline...")
            import asyncio
            import functools
            func = functools.partial(
                adk_supervisor.run_adk_pipeline,
                company,
                policy,
                policy_text,
                active_frameworks=selected_fw_keys,
                user_id=auth.get_current_user()
            )
            master_report = await asyncio.get_event_loop().run_in_executor(None, func)

            # =================================================
            # VALIDATE REPORT
            # =================================================

            if master_report is None:

                raise ValueError(
                    "ADK pipeline returned None."
                )

            if not isinstance(
                master_report,
                dict,
            ):

                raise TypeError(
                    "ADK pipeline returned "
                    f"{type(master_report).__name__}, "
                    "expected dict."
                )

            page_state[
                "master_report"
            ] = master_report

            logger.info(
                "ADK pipeline completed. Report keys: %s",
                list(master_report.keys()),
            )

            # =================================================
            # APPLY FRAMEWORK FILTER
            # =================================================

            report = filter_report_payload(
                master_report,
                selected_fw_keys,
            )

            # =================================================
            # CLEAR OLD UI (Safely handle client disconnects)
            # =================================================

            try:
                score_container.clear()
                posture_container.clear()
                gap_container.clear()
                action_container.clear()
                compliant_container.clear()
                export_container.clear()
            except RuntimeError as e:
                if "client this element belongs to has been deleted" in str(e):
                    logger.warning("Client session ended during analysis. Skipping UI update.")
                    return
                raise e

            # =================================================
            # SCORE TAB
            # =================================================

            with score_container:

                summary = report.get(
                    "summary",
                    {},
                )

                framework_summaries = (
                    summary.get(
                        "framework_summaries",
                        {},
                    )
                )

                create_score_cards(
                    summary=summary,
                    framework_summaries=framework_summaries,
                    selected_fw_keys=selected_fw_keys,
                )

            # =================================================
            # POLICY POSTURE
            # =================================================

            with posture_container:

                create_policy_posture(
                    report
                )

            # =================================================
            # DETAILED GAPS
            # =================================================

            with gap_container:

                create_gap_analysis(
                    report
                )

            # =================================================
            # ACTION PLAN
            # =================================================

            with action_container:

                create_action_plan(
                    report
                )

            # =================================================
            # COMPLIANT AREAS
            # =================================================

            with compliant_container:

                create_compliant_areas(
                    report
                )

            # =================================================
            # EXPORT
            # =================================================

            with export_container:

                create_report_export(
                    report=report,
                    company=company,
                )

            # =================================================
            # SUCCESS
            # =================================================

            # Trace overall score
            _summary_obj = report.get("summary", {})
            logger.debug(
                "Summary keys: %s | overall_score: %s | framework scores: %s",
                list(_summary_obj.keys()) if isinstance(_summary_obj, dict) else type(_summary_obj),
                repr(_summary_obj.get("overall_score")) if isinstance(_summary_obj, dict) else "N/A",
                {
                    k: v.get("score") if isinstance(v, dict) else v
                    for k, v in _summary_obj.get("framework_summaries", {}).items()
                } if isinstance(_summary_obj, dict) else "N/A",
            )

            score = (
                report
                .get(
                    "summary",
                    {},
                )
                .get(
                    "overall_score",
                    0,
                )
            )

            status.set_text(
                f"Analysis completed successfully. "
                f"Overall Score: {score}%"
            )

            ui.notify(
                "Compliance analysis completed successfully.",
                type="positive",
            )

            logger.info("=== ANALYSIS SUCCESS | Overall Score: %s%% ===", score)

        except Exception as e:

            if "client this element belongs to has been deleted" in str(e):
                logger.warning("Client session disconnected during analysis pipeline.")
                return

            logger.error("Analysis pipeline error: %s", e, exc_info=True)

            try:
                status.set_text(f"Analysis failed: {e}")
                ui.notify(f"Analysis failed: {e}", type="negative")
            except Exception:
                pass

        finally:

            button.enable()

    # ========================================================
    # CONNECT RUN BUTTON
    # ========================================================

    sidebar[
        "run_button"
    ].on_click(
        run_analysis
    )

    # ========================================================
    # FRAMEWORK CHANGE CALLBACK
    # ========================================================
    
    def handle_framework_change():
        if page_state.get("master_report"):
            selected_fw_keys = []
            if sidebar["gdpr_checkbox"].value:
                selected_fw_keys.append("gdpr")
            if sidebar["hipaa_checkbox"].value:
                selected_fw_keys.append("hipaa")
            if sidebar["rbi_checkbox"].value:
                selected_fw_keys.append("rbi")
            if sidebar["soc2_checkbox"].value:
                selected_fw_keys.append("soc2")

            page_state["selected_frameworks"] = selected_fw_keys
            
            report = filter_report_payload(
                page_state["master_report"],
                selected_fw_keys,
            )
            
            score_container.clear()
            posture_container.clear()
            gap_container.clear()
            action_container.clear()
            compliant_container.clear()
            export_container.clear()
            
            with score_container:
                summary = report.get("summary", {})
                framework_summaries = summary.get("framework_summaries", {})
                create_score_cards(
                    summary=summary,
                    framework_summaries=framework_summaries,
                    selected_fw_keys=selected_fw_keys,
                )
                
            with posture_container:
                create_policy_posture(report)
                
            with gap_container:
                create_gap_analysis(report)
                
            with action_container:
                create_action_plan(report)

            with compliant_container:
                create_compliant_areas(report)
                
            with export_container:
                create_report_export(
                    report=report,
                    company=sidebar["company_name"].value or "Uploaded Organization",
                )

    for cb_key in ["gdpr_checkbox", "hipaa_checkbox", "rbi_checkbox", "soc2_checkbox"]:
        sidebar[cb_key].on_value_change(handle_framework_change)


# ============================================================
# CUSTOM 404 PAGE
# ============================================================

@ui.page("/404")
def not_found_page():
    ui.colors(
        primary='#4e795d',
        dark='#101713',
    )
    with ui.column().classes("w-full min-h-screen items-center justify-center gap-6").style(
        "background: linear-gradient(135deg, #101713 0%, #1a2e20 50%, #101713 100%); "
        "min-height: 100vh; display: flex; flex-direction: column; "
        "align-items: center; justify-content: center; padding: 2rem;"
    ):
        # Shield icon
        ui.html('''
        <div style="
            width: 100px; height: 100px;
            background: linear-gradient(135deg, #4e795d, #3b6349);
            border-radius: 50%; display: flex; align-items: center;
            justify-content: center; font-size: 48px;
            box-shadow: 0 0 40px rgba(78,121,93,0.4);
            margin-bottom: 8px;
        ">🛡️</div>
        ''')

        ui.label("404").style(
            "font-size: 6rem; font-weight: 900; "
            "background: linear-gradient(135deg, #4e795d, #eae3d2); "
            "-webkit-background-clip: text; -webkit-text-fill-color: transparent; "
            "background-clip: text; line-height: 1; margin: 0;"
        )

        ui.label("Page Not Found").style(
            "font-size: 1.5rem; font-weight: 600; color: #eae3d2; margin-top: 4px;"
        )

        ui.label(
            "The page you're looking for doesn't exist or has been moved."
        ).style(
            "color: #8a9e8f; font-size: 1rem; text-align: center; max-width: 400px;"
        )

        ui.button(
            "← Return to LexMesh Dashboard",
            on_click=lambda: ui.navigate.to("/")
        ).style(
            "margin-top: 1rem; "
            "background: linear-gradient(135deg, #4e795d, #3b6349); "
            "color: #eae3d2; border: none; padding: 12px 28px; "
            "border-radius: 8px; font-size: 1rem; font-weight: 600; "
            "cursor: pointer; box-shadow: 0 4px 20px rgba(78,121,93,0.35); "
            "transition: all 0.2s ease;"
        )


if __name__ == "__main__":
    import os
    port = int(os.environ.get("PORT", 8080))
    ui.run(
        title="LexMesh — AI Compliance Engine",
        favicon="🛡️",
        port=port,
        storage_secret=config.NICEGUI_STORAGE_SECRET,
        reload=False,
    )