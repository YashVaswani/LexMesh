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
from agents.triage_agent import triage_document
from logger import get_logger
import auth

logger = get_logger("app")

# Serve static assets (OG social images, logos, etc.)
_static_path = Path(__file__).parent / "ui" / "static"
if _static_path.exists():
    app.add_static_files("/static", str(_static_path))

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
<script src="https://cdn.jsdelivr.net/npm/canvas-confetti@1.9.3/dist/confetti.browser.min.js"></script>
<!-- Custom favicon: branded mesh-shield icon -->
<link rel="icon" type="image/png" href="/static/favicon.png">
<link rel="shortcut icon" href="/static/favicon.png">
<link rel="apple-touch-icon" href="/static/favicon.png">
''', shared=True)

# ── Global UX JS bundle (13, 2, 1, 10, 8, 14) ───────────────────────────────
ui.add_head_html('''
<script>
// 13. Dark Mode Persistence
(function(){
  if(localStorage.getItem('lex_dark_mode')==='1'){
    document.body.classList.add('body--dark','q-dark');
  }
})();
document.addEventListener('DOMContentLoaded',function(){
  var obs=new MutationObserver(function(){
    var dark=document.body.classList.contains('body--dark')||document.body.classList.contains('q-dark');
    localStorage.setItem('lex_dark_mode',dark?'1':'0');
  });
  obs.observe(document.body,{attributes:true,attributeFilter:['class']});
});

// 2. Keyboard Shortcuts
document.addEventListener('keydown',function(e){
  if((e.ctrlKey||e.metaKey)&&e.key==='Enter'){
    e.preventDefault();
    var btn=document.querySelector('.lex-run-button');
    if(btn&&!btn.disabled)btn.click();
  }
});

// 1. Animated Score Counter
window.lexAnimateScore=function(el,target,dur){
  if(!el)return;
  el.classList.add('lex-score-animated');
  var st=null;
  function step(ts){
    if(!st)st=ts;
    var p=Math.min((ts-st)/dur,1);
    var ease=1-Math.pow(1-p,3);
    el.textContent=Math.round(ease*target)+'%';
    if(p<1)requestAnimationFrame(step);
  }
  requestAnimationFrame(step);
};

// 10. Confetti on High Score
window.lexConfetti=function(){
  if(typeof confetti!=='undefined'){
    confetti({particleCount:120,spread:80,origin:{y:0.55},colors:['#4e795d','#7ca689','#eae3d2','#3b6349','#8a7642']});
    setTimeout(function(){
      confetti({particleCount:60,angle:60,spread:55,origin:{x:0,y:0.6},colors:['#4e795d','#d4e2d8','#23382b']});
      confetti({particleCount:60,angle:120,spread:55,origin:{x:1,y:0.6},colors:['#4e795d','#d4e2d8','#23382b']});
    },260);
  }
};

// 8. Copy to Clipboard
window.lexCopyText=function(text,btn){
  navigator.clipboard.writeText(text).then(function(){
    var orig=btn.innerHTML;
    btn.innerHTML='<svg xmlns="http://www.w3.org/2000/svg" width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round"><polyline points="20 6 9 17 4 12"></polyline></svg>';
    btn.style.color='#3b6349';
    setTimeout(function(){btn.innerHTML=orig;btn.style.color='';},1800);
  });
};

// 14. Onboarding Tour
window.lexStartTour=function(){
  var steps=[
    {selector:'.lex-policy-upload',title:'Step 1 — Upload Policy',desc:'Upload your company policy PDF here (max 25 MB). We support Privacy, Security, and Data Protection policies.'},
    {selector:'.lex-framework-select',title:'Step 2 — Select Industry',desc:'Choose your organisation type to auto-configure the relevant compliance frameworks.'},
    {selector:'.lex-run-button',title:'Step 3 — Run Analysis',desc:'Click to start the AI-powered audit. Keyboard shortcut: Ctrl + Enter.'},
    {selector:'.lex-dashboard-tabs',title:'Step 4 — Review Results',desc:'Your compliance scores, policy gaps, action plan, and exportable PDF report appear here.'},
  ];
  var i=0;
  var overlay=document.createElement('div');
  overlay.style.cssText='position:fixed;top:0;left:0;width:100%;height:100%;background:rgba(0,0,0,0.42);z-index:99990;pointer-events:none;';
  document.body.appendChild(overlay);
  function showStep(){
    document.querySelectorAll('.lex-tour-highlight').forEach(function(e){e.classList.remove('lex-tour-highlight');});
    if(i>=steps.length){overlay.remove();document.getElementById('lex-tour-popup')?.remove();return;}
    var s=steps[i];
    var target=document.querySelector(s.selector);
    if(target){target.classList.add('lex-tour-highlight');target.scrollIntoView({behavior:'smooth',block:'center'});}
    var popup=document.getElementById('lex-tour-popup')||document.createElement('div');
    popup.id='lex-tour-popup';
    popup.style.cssText='position:fixed;bottom:32px;left:50%;transform:translateX(-50%);z-index:99995;background:#1b2721;border:2px solid #4e795d;border-radius:18px;padding:20px 28px;max-width:420px;width:calc(100vw - 48px);box-shadow:0 12px 40px rgba(0,0,0,0.6);font-family:Plus Jakarta Sans,sans-serif;pointer-events:all;';
    popup.innerHTML='<div style="font-size:0.75rem;font-weight:800;color:#7ca689;letter-spacing:0.06em;text-transform:uppercase;margin-bottom:6px;">'+(i+1)+' / '+steps.length+'</div>'
      +'<div style="font-size:1rem;font-weight:900;color:#f5f2eb;margin-bottom:8px;">'+s.title+'</div>'
      +'<div style="font-size:0.88rem;color:#a3b8aa;line-height:1.6;margin-bottom:16px;">'+s.desc+'</div>'
      +'<div style="display:flex;gap:10px;">'
      +'<button onclick="document.querySelectorAll(\'.lex-tour-highlight\').forEach(e=>e.classList.remove(\'lex-tour-highlight\'));document.getElementById(\'lex-tour-popup\').remove();document.body.querySelector(\'[style*=99990]\')?.remove();" style="flex:1;padding:8px;border-radius:10px;border:1.5px solid #36483e;background:transparent;color:#a3b8aa;font-weight:700;cursor:pointer;font-size:0.85rem;">Skip</button>'
      +'<button id="lex-tour-next" style="flex:2;padding:8px;border-radius:10px;border:none;background:linear-gradient(135deg,#4e795d,#23382b);color:#fff;font-weight:800;cursor:pointer;font-size:0.85rem;">'+(i<steps.length-1?'Next &rarr;':'Done &check;')+'</button>'
      +'</div>';
    document.body.appendChild(popup);
    document.getElementById('lex-tour-next').onclick=function(){i++;showStep();};
  }
  showStep();
};
document.addEventListener('DOMContentLoaded',function(){
  if(!localStorage.getItem('lex_tour_seen')){
    setTimeout(function(){
      if(!document.querySelector('.lex-run-button'))return;
      var fab=document.createElement('button');
      fab.title='Take a product tour';
      fab.innerHTML='<svg xmlns="http://www.w3.org/2000/svg" width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round"><circle cx="12" cy="12" r="10"></circle><path d="M9.09 9a3 3 0 0 1 5.83 1c0 2-3 3-3 3"></path><line x1="12" y1="17" x2="12.01" y2="17"></line></svg>';
      fab.style.cssText='position:fixed;bottom:80px;right:24px;z-index:9999;width:48px;height:48px;border-radius:50%;background:linear-gradient(135deg,#4e795d,#23382b);color:#fff;border:none;cursor:pointer;box-shadow:0 6px 20px rgba(78,121,93,0.5);display:flex;align-items:center;justify-content:center;transition:transform 0.2s ease;';
      fab.onmouseenter=function(){this.style.transform='scale(1.12)';};fab.onmouseleave=function(){this.style.transform='scale(1)';};
      fab.onclick=function(){localStorage.setItem('lex_tour_seen','1');fab.remove();window.lexStartTour();};
      document.body.appendChild(fab);
    },2500);
  }
});
</script>
''', shared=True)


# Plausible privacy-friendly analytics (no cookies, GDPR-compliant)
ui.add_head_html(
    '<script defer data-domain="lexmesh.onrender.com" src="https://plausible.io/js/script.js"></script>',
    shared=True,
)

# Cookie Consent Banner — injected once, self-dismisses via localStorage
ui.add_head_html('''
<style>
  #lex-cookie-banner {
    position: fixed;
    bottom: 24px;
    left: 50%;
    transform: translateX(-50%);
    z-index: 99999;
    display: flex;
    align-items: center;
    gap: 18px;
    background: rgba(15, 23, 18, 0.96);
    border: 1px solid rgba(78, 121, 93, 0.55);
    border-radius: 16px;
    padding: 14px 22px;
    box-shadow: 0 8px 40px rgba(0,0,0,0.55), 0 0 0 1px rgba(78,121,93,0.18);
    backdrop-filter: blur(16px);
    -webkit-backdrop-filter: blur(16px);
    max-width: 640px;
    width: calc(100vw - 48px);
    font-family: \'Plus Jakarta Sans\', Inter, sans-serif;
    animation: lex-cookie-slide-in 0.45s cubic-bezier(0.34,1.56,0.64,1) both;
  }
  @keyframes lex-cookie-slide-in {
    from { opacity: 0; transform: translateX(-50%) translateY(24px); }
    to   { opacity: 1; transform: translateX(-50%) translateY(0); }
  }
  #lex-cookie-banner p {
    flex: 1;
    margin: 0;
    font-size: 0.82rem;
    color: #c8c0b0;
    line-height: 1.55;
  }
  #lex-cookie-banner a {
    color: #7ca689;
    font-weight: 600;
    text-decoration: underline;
    text-underline-offset: 2px;
  }
  #lex-cookie-accept {
    flex-shrink: 0;
    background: linear-gradient(135deg, #4e795d, #3b6349);
    color: #eae3d2;
    border: none;
    border-radius: 10px;
    padding: 8px 22px;
    font-size: 0.82rem;
    font-weight: 700;
    cursor: pointer;
    transition: opacity 0.2s ease, transform 0.15s ease;
    letter-spacing: 0.02em;
  }
  #lex-cookie-accept:hover { opacity: 0.88; transform: scale(1.03); }
  #lex-cookie-banner.lex-cookie-hide {
    animation: lex-cookie-slide-out 0.3s ease forwards;
  }
  @keyframes lex-cookie-slide-out {
    to { opacity: 0; transform: translateX(-50%) translateY(20px); }
  }
</style>
<script>
(function() {
  if (localStorage.getItem(\'lex_cookie_accepted\') === \'1\') return;
  document.addEventListener(\'DOMContentLoaded\', function() {
    var banner = document.createElement(\'div\');
    banner.id = \'lex-cookie-banner\';
    banner.innerHTML = [
      \'<p>🔒 We use <strong>essential session cookies</strong> for authentication and audit state only. \',
      \'No analytics cookies, no tracking pixels. Uploaded documents are processed in-memory and never stored. \',
      \'<a href="/privacy" target="_blank">Privacy Policy</a></p>\',
      \'<button id="lex-cookie-accept">Got it</button>\'
    ].join(\'\');
    document.body.appendChild(banner);
    document.getElementById(\'lex-cookie-accept\').addEventListener(\'click\', function() {
      localStorage.setItem(\'lex_cookie_accepted\', \'1\');
      banner.classList.add(\'lex-cookie-hide\');
      setTimeout(function() { banner.remove(); }, 320);
    });
  });
})();
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
<meta property="og:image" content="https://lexmesh.onrender.com/static/lexmesh_og.jpg">
<meta property="og:image:width" content="1200">
<meta property="og:image:height" content="630">
<meta property="og:site_name" content="LexMesh">
<meta property="og:url" content="https://lexmesh.onrender.com">

<!-- Twitter Card -->
<meta name="twitter:card" content="summary_large_image">
<meta name="twitter:title" content="LexMesh — AI-Powered Compliance Engine">
<meta name="twitter:description" content="Upload your policy PDF. Get instant GDPR, HIPAA, RBI &amp; SOC 2 compliance scores, gap analysis, and a prioritised action plan.">
<meta name="twitter:image" content="https://lexmesh.onrender.com/static/lexmesh_og.jpg">
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
                        ui.notify("Please enter both email and password.", type="warning", position='top')
                        return
                    success, msg = auth.sign_in(email.value, password.value)
                    if success:
                        ui.notify("Logged in successfully!", type="positive", position='top')
                        ui.navigate.to('/')
                    else:
                        err = str(msg)
                        if 'email' in err.lower() and 'confirm' in err.lower():
                            ui.notify("Please verify your email first. Check your inbox.", type="warning", timeout=6000, position='top')
                        else:
                            ui.notify(err, type="negative", position='top')

                email.on('keydown.enter', do_login)
                password.on('keydown.enter', do_login)

                ui.button("LOG IN", on_click=do_login).classes("w-full mt-2 h-12 rounded-lg font-bold text-white shadow-lg shadow-emerald-500/30 tracking-wider").props("color=primary unelevated icon-right=arrow_forward")
            
            # Footer Divider
            with ui.row().classes("w-full items-center justify-center mt-8 gap-3"):
                ui.element('div').classes("h-px bg-slate-200 flex-grow")
                with ui.row().classes("items-center gap-1 text-sm font-medium"):
                    ui.label("Don't have an account?").classes("text-slate-500")
                    ui.link("Sign Up", "/signup").classes("text-emerald-600 hover:text-emerald-700 transition-colors")
                ui.element('div').classes("h-px bg-slate-200 flex-grow")

            # Legal footer
            with ui.row().classes("w-full items-center justify-center gap-3 mt-4"):
                ui.link("Privacy Policy", "/privacy?from=login").classes("text-xs text-slate-400 hover:text-slate-600").style("word-spacing:0.25em;")
                ui.label("·").classes("text-xs text-slate-300")
                ui.link("Terms & Conditions", "/terms?from=login").classes("text-xs text-slate-400 hover:text-slate-600").style("word-spacing:0.25em;")

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
                # Company Name
                company_name_input = ui.input("Company Name", placeholder="e.g. TechStartup Pvt Ltd").classes("w-full text-md").props('outlined rounded bg-color="white" color="emerald"')
                with company_name_input.add_slot('prepend'):
                    ui.icon('business').classes('text-slate-400')

                email = ui.input("Email").classes("w-full text-md").props('outlined rounded bg-color="white" color="emerald"')
                with email.add_slot('prepend'):
                    ui.icon('mail_outline').classes('text-slate-400')
                
                password = ui.input("Password", password=True, password_toggle_button=True).classes("w-full text-md").props('outlined rounded bg-color="white" color="emerald"')
                with password.add_slot('prepend'):
                    ui.icon('lock_outline').classes('text-slate-400')

                # Confirm Password
                confirm_password = ui.input("Confirm Password", password=True, password_toggle_button=True).classes("w-full text-md").props('outlined rounded bg-color="white" color="emerald"')
                with confirm_password.add_slot('prepend'):
                    ui.icon('lock_reset').classes('text-slate-400')
                
                def do_signup():
                    if not email.value or not password.value:
                        ui.notify("Please enter both email and password.", type="warning", position='top')
                        return
                    if not company_name_input.value.strip():
                        ui.notify("Please enter your company name.", type="warning", position='top')
                        return
                    if len(password.value) < 6:
                        ui.notify("Password must be at least 6 characters.", type="warning", position='top')
                        return
                    if password.value != confirm_password.value:
                        ui.notify("Passwords do not match. Please check and try again.", type="negative", position='top')
                        return
                    success, msg = auth.sign_up(email.value, password.value)
                    if success and msg == "CHECK_EMAIL":
                        email.value = ''
                        password.value = ''
                        confirm_password.value = ''
                        company_name_input.value = ''
                        ui.notify(
                            "Account created! Please check your inbox and click the verification link to activate your account.",
                            type="positive",
                            timeout=8000,
                            position='top'
                        )
                        ui.navigate.to('/verify-email')
                    elif success:
                        ui.notify("Signed up successfully! Welcome to LexMesh.", type="positive", position='top')
                        ui.navigate.to('/')
                    else:
                        ui.notify(msg, type="negative", position='top')

                email.on('keydown.enter', do_signup)
                password.on('keydown.enter', do_signup)
                confirm_password.on('keydown.enter', do_signup)

                ui.button("SIGN UP", on_click=do_signup).classes("w-full mt-2 h-12 rounded-lg font-bold text-white shadow-lg shadow-emerald-500/30 tracking-wider").props("color=primary unelevated icon-right=person_add")
            
            with ui.row().classes("w-full items-center justify-center mt-8 gap-3"):
                ui.element('div').classes("h-px bg-slate-200 flex-grow")
                with ui.row().classes("items-center gap-1 text-sm font-medium"):
                    ui.label("Already have an account?").classes("text-slate-500")
                    ui.link("Log In", "/login").classes("text-emerald-600 hover:text-emerald-700 transition-colors")
                ui.element('div').classes("h-px bg-slate-200 flex-grow")

            # Legal footer
            with ui.row().classes("w-full items-center justify-center gap-3 mt-4"):
                ui.link("Privacy Policy", "/privacy?from=login").classes("text-xs text-slate-400 hover:text-slate-600").style("word-spacing:0.25em;")
                ui.label("·").classes("text-xs text-slate-300")
                ui.link("Terms & Conditions", "/terms?from=login").classes("text-xs text-slate-400 hover:text-slate-600").style("word-spacing:0.25em;")

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
# PUBLIC LEGAL PAGES (no auth guard)
# ============================================================

@ui.page("/privacy")
def privacy_page(request: Request):
    """Public Privacy Policy page — accessible without login."""
    from ui.components.privacy_policy import create_privacy_policy_page
    from_param = request.query_params.get("from")
    create_privacy_policy_page(from_page=from_param)

@ui.page("/terms")
def terms_page(request: Request):
    """Public Terms & Conditions page — accessible without login."""
    from ui.components.terms_page import create_terms_page
    from_param = request.query_params.get("from")
    create_terms_page(from_page=from_param)

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
        "last_run_at": 0.0,  # Unix timestamp — for 30s rate limiting
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
        # Legal footer
        with ui.row().classes("w-full items-center justify-center gap-3 pb-6 px-6").style(
            "border-top: 1px solid var(--lex-border);"
        ):
            ui.label("LexMesh outputs are for informational purposes only and do not constitute legal advice.").style(
                "font-size:0.75rem; color: var(--lex-muted);"
            )
            ui.label("·").style("color: var(--lex-muted); font-size:0.75rem;")
            ui.link("Privacy Policy", "/privacy?from=dashboard").style(
                "font-size:0.75rem; color: var(--lex-sage); font-weight:600;"
            )
            ui.label("·").style("color: var(--lex-muted); font-size:0.75rem;")
            ui.link("Terms & Conditions", "/terms?from=dashboard").style(
                "font-size:0.75rem; color: var(--lex-sage); font-weight:600;"
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

        # Status row: inline spinner (hidden by default) + text label
        with ui.row().classes("items-center gap-3") as status_row:
            status_spinner = ui.spinner(size="sm", color="primary")
            status_spinner.set_visibility(False)
            status = ui.label(
                "Upload a company policy PDF to begin."
            ).classes(
                "lex-analysis-status"
            )

        # ====================================================
        # PROGRESS STEPS BAR (3)
        # ====================================================
        with ui.element('div').classes('lex-progress-steps w-full') as progress_steps:
            # Step 1
            with ui.element('span').classes('lex-step').props('id="lstep1"'):
                ui.html('<span class="lex-step-dot">1</span> Upload')
            ui.html('<div class="lex-step-connector" id="lconn1"></div>')
            # Step 2
            with ui.element('span').classes('lex-step').props('id="lstep2"'):
                ui.html('<span class="lex-step-dot">2</span> Classify')
            ui.html('<div class="lex-step-connector" id="lconn2"></div>')
            # Step 3
            with ui.element('span').classes('lex-step').props('id="lstep3"'):
                ui.html('<span class="lex-step-dot">3</span> Analyse')
            ui.html('<div class="lex-step-connector" id="lconn3"></div>')
            # Step 4
            with ui.element('span').classes('lex-step').props('id="lstep4"'):
                ui.html('<span class="lex-step-dot">4</span> Report')

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

                    # PDF Preview (18) — shown before first analysis run
                    with ui.element('div').classes('lex-pdf-preview-panel w-full') as pdf_preview_container:
                        with ui.column().classes('items-center gap-3 w-full'):
                            ui.html('<svg xmlns="http://www.w3.org/2000/svg" width="48" height="48" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round" style="color:var(--lex-muted);opacity:0.5"><path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z"></path><polyline points="14 2 14 8 20 8"></polyline><line x1="16" y1="13" x2="8" y2="13"></line><line x1="16" y1="17" x2="8" y2="17"></line><polyline points="10 9 9 9 8 9"></polyline></svg>')
                            ui.label('Upload a policy PDF to preview it here').style('color:var(--lex-muted);font-size:0.95rem;font-weight:600;text-align:center;')
                            ui.label('Then click Run Analysis to generate your compliance report').style('color:var(--lex-muted);font-size:0.82rem;text-align:center;opacity:0.7;')
                    with ui.element('div').classes('w-full') as pdf_canvas_container:
                        pass
                    pdf_canvas_container.set_visibility(False)


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
    # LEGAL FOOTER
    # ========================================================

    with ui.row().classes("w-full items-center justify-center gap-3 py-4 mt-4").style(
        "border-top: 1px solid var(--lex-border); margin-top: 12px;"
    ):
        ui.label("LexMesh outputs are for informational purposes only and do not constitute legal advice.").style(
            "font-size:0.75rem; color: var(--lex-muted);"
        )
        ui.label("·").style("color: var(--lex-muted); font-size:0.75rem;")
        ui.link("Privacy Policy", "/privacy?from=audit").style(
            "font-size:0.75rem; color: var(--lex-sage); font-weight:600;"
        )
        ui.label("·").style("color: var(--lex-muted); font-size:0.75rem;")
        ui.link("Terms & Conditions", "/terms?from=audit").style(
            "font-size:0.75rem; color: var(--lex-sage); font-weight:600;"
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

            # ------------------------------------------------
            # UPLOADING FEEDBACK — show inline spinner
            # ------------------------------------------------
            status_spinner.set_visibility(True)
            status.set_text("Uploading & understanding document...")

            if "attached_file_container" in sidebar:
                sidebar["attached_file_name_label"].text = uploaded_file.name
                sidebar["attached_file_container"].set_visibility(True)

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

            status_spinner.set_visibility(False)
            status.set_text(
                f"✅ Document ready — {uploaded_file.name}{det_str}"
            )

            ui.notify(
                f"✅ Document understood — {company or 'Company'} · {policy or 'Policy'}",
                type="positive",
                position='top',
            )

            # Progress: step 1 done -> step 2 active
            ui.run_javascript("""
                var s=document.getElementById('lstep1');
                if(s){s.classList.remove('active');s.classList.add('done');}
                var c=document.getElementById('lconn1');if(c)c.classList.add('done');
                var s2=document.getElementById('lstep2');if(s2)s2.classList.add('active');
            """)

            # 18. PDF Preview
            import base64 as _b64
            _pdf_b64 = _b64.b64encode(pdf_data).decode()
            pdf_preview_container.set_visibility(False)
            pdf_canvas_container.set_visibility(True)
            pdf_canvas_container.clear()
            _fname = uploaded_file.name
            with pdf_canvas_container:
                ui.html(f"""
<div class="lex-pdf-preview-panel">
  <div style="font-size:0.82rem;font-weight:800;color:var(--lex-muted);text-transform:uppercase;letter-spacing:0.06em;margin-bottom:4px;">Document Preview</div>
  <div style="font-size:0.9rem;font-weight:700;color:var(--lex-text);margin-bottom:12px;">{_fname}</div>
  <div class="lex-pdf-canvas-wrapper"><canvas id="lex-pdf-preview-canvas"></canvas></div>
  <div style="font-size:0.78rem;color:var(--lex-muted);margin-top:8px;">Page 1 preview &#x2022; Select frameworks then click Run Analysis</div>
</div>
<script type="module">
import * as pdfjsLib from 'https://cdnjs.cloudflare.com/ajax/libs/pdf.js/4.0.379/pdf.min.mjs';
pdfjsLib.GlobalWorkerOptions.workerSrc = 'https://cdnjs.cloudflare.com/ajax/libs/pdf.js/4.0.379/pdf.worker.min.mjs';
try {
  const raw = atob('{_pdf_b64}');
  const arr = new Uint8Array(raw.length);
  for(let i=0;i<raw.length;i++) arr[i]=raw.charCodeAt(i);
  const pdf = await pdfjsLib.getDocument({data:arr}).promise;
  const page = await pdf.getPage(1);
  const canvas = document.getElementById('lex-pdf-preview-canvas');
  if(canvas){
    const vp = page.getViewport({scale:1.4});
    canvas.height=vp.height; canvas.width=vp.width;
    await page.render({canvasContext:canvas.getContext('2d'),viewport:vp}).promise;
  }
} catch(e){ console.warn('PDF preview:',e); }
</script>
""")

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

            status_spinner.set_visibility(False)
            status.set_text(f"❌ Upload failed: {e}")

            ui.notify(
                f"Upload failed: {e}",
                type="negative",
                position='top',
            )

            logger.error("PDF upload error: %s", e, exc_info=True)

    sidebar[
        "uploaded_file"
    ].on_upload(
        handle_upload
    )

    def handle_clear_upload():
        sidebar["uploaded_file"].reset()
        if "attached_file_container" in sidebar:
            sidebar["attached_file_container"].set_visibility(False)
            sidebar["attached_file_name_label"].text = ""
        page_state["pdf_bytes"] = None
        page_state["pdf_name"] = ""
        sidebar["company_name"].value = ""
        sidebar["company_name"].update()
        sidebar["policy_name"].value = ""
        sidebar["policy_name"].update()
        pdf_canvas_container.set_visibility(False)
        pdf_canvas_container.clear()
        pdf_preview_container.set_visibility(True)
        ui.run_javascript("""
            ['lstep1','lstep2','lstep3','lstep4'].forEach(function(id, i) {
                var el = document.getElementById(id);
                if (el) { el.classList.remove('done', 'active'); if (i === 0) el.classList.add('active'); }
            });
            ['lconn1','lconn2','lconn3'].forEach(function(id) {
                var el = document.getElementById(id); if (el) el.classList.remove('done');
            });
        """)
        status.set_text("Upload a company policy PDF to begin.")
        ui.notify("Document removed. You can now upload a new PDF.", type="info", position='top')

    if "clear_upload_btn" in sidebar:
        sidebar["clear_upload_btn"].on_click(handle_clear_upload)

    def handle_upload_rejected(event):
        sidebar["uploaded_file"].reset()
        if "attached_file_container" in sidebar:
            sidebar["attached_file_container"].set_visibility(False)
            sidebar["attached_file_name_label"].text = ""
        ui.notify("File exceeds limit or is not a PDF (Max 25 MB).", type="warning", position='top')

    sidebar["uploaded_file"].on("rejected", handle_upload_rejected)

    # --------------------------------------------------------
    # DEMO MODE — auto-load sample GDPR PDF when ?demo=1
    # --------------------------------------------------------

    _is_demo = (
        request is not None
        and request.query_params.get("demo") == "1"
    )
    if _is_demo:
        _sample_pdf_path = Path(__file__).parent / "GDPR_Condensed_Articles_1-99.pdf"
        if _sample_pdf_path.exists():
            _sample_bytes = _sample_pdf_path.read_bytes()
            _sample_name = "GDPR_Sample_Policy.pdf"

            page_state["pdf_bytes"] = _sample_bytes
            page_state["pdf_name"] = _sample_name

            # Auto-populate sidebar labels
            if "attached_file_container" in sidebar:
                sidebar["attached_file_name_label"].text = _sample_name
                sidebar["attached_file_container"].set_visibility(True)

            # Extract & populate company / policy fields
            _demo_company, _demo_policy = extract_metadata_from_pdf(_sample_bytes, _sample_name)
            sidebar["company_name"].value = _demo_company or "Sample Organisation"
            sidebar["company_name"].update()
            sidebar["policy_name"].value = _demo_policy or "GDPR Condensed Policy"
            sidebar["policy_name"].update()

            status.set_text(
                "🎬 Demo mode: GDPR sample policy loaded. Select frameworks and click 'Run Audit' to see results."
            )
            ui.notify(
                "Sample GDPR policy loaded! Click 'Run Audit' to try LexMesh.",
                type="positive",
                timeout=5000,
            )


    # ========================================================
    # RUN ANALYSIS
    # ========================================================

    async def run_analysis():
        import time
        import asyncio

        logger.info("=== RUN ANALYSIS TRIGGERED ===")

        # ----------------------------------------------------
        # RATE LIMITING — 30-second cooldown per session
        # ----------------------------------------------------
        now = time.monotonic()
        elapsed = now - page_state.get("last_run_at", 0.0)
        cooldown_secs = 30
        if elapsed < cooldown_secs:
            remaining = int(cooldown_secs - elapsed)
            ui.notify(
                f"⏳ Please wait {remaining}s before running another audit.",
                type="warning",
                position='top',
            )
            return

        # ----------------------------------------------------
        # GET CURRENT PAGE PDF
        # ----------------------------------------------------

        pdf_bytes = page_state.get("pdf_bytes")

        logger.debug(
            "PDF state: %s (%d bytes)",
            "AVAILABLE" if pdf_bytes else "EMPTY",
            len(pdf_bytes) if pdf_bytes else 0,
        )

        # ----------------------------------------------------
        # FORM VALIDATION — Check PDF, frameworks, company
        # ----------------------------------------------------

        validation_errors = []

        if pdf_bytes is None or len(pdf_bytes) == 0:
            validation_errors.append("📄 No policy document uploaded. Please upload a PDF first.")

        selected_fw_check = []
        if sidebar["gdpr_checkbox"].value:
            selected_fw_check.append("gdpr")
        if sidebar["hipaa_checkbox"].value:
            selected_fw_check.append("hipaa")
        if sidebar["rbi_checkbox"].value:
            selected_fw_check.append("rbi")
        if sidebar["soc2_checkbox"].value:
            selected_fw_check.append("soc2")
        if not selected_fw_check:
            validation_errors.append("⚖️ No compliance framework selected. Please choose at least one framework.")

        if validation_errors:
            for err in validation_errors:
                ui.notify(err, type="warning", timeout=5000, position='top')
            status.set_text(" · ".join(validation_errors))
            return

        button = sidebar["run_button"]

        # Record timestamp BEFORE analysis starts (prevents double-click spam)
        page_state["last_run_at"] = time.monotonic()

        button.disable()
        status_spinner.set_visibility(True)

        # Step tracker (3): Move to step 2 (Classify)
        ui.run_javascript("""
            var s1 = document.getElementById('lstep1'); if(s1){s1.classList.remove('active'); s1.classList.add('done');}
            var c1 = document.getElementById('lconn1'); if(c1) c1.classList.add('done');
            var s2 = document.getElementById('lstep2'); if(s2) s2.classList.add('active');
        """)

        # Skeleton loaders (8): show shimmer placeholders while analysis runs
        score_container.clear()
        with score_container:
            ui.html("""
            <div class="w-full flex flex-col gap-4">
                <div class="lex-skeleton-card w-full">
                    <div class="lex-skeleton lex-skeleton-title"></div>
                    <div class="lex-skeleton lex-skeleton-score"></div>
                    <div class="lex-skeleton lex-skeleton-line" style="width:75%; margin:16px auto 0;"></div>
                </div>
                <div class="grid grid-cols-1 md:grid-cols-2 xl:grid-cols-4 gap-4 w-full">
                    <div class="lex-skeleton-card"><div class="lex-skeleton lex-skeleton-title"></div><div class="lex-skeleton lex-skeleton-line"></div><div class="lex-skeleton lex-skeleton-line" style="width:60%;"></div></div>
                    <div class="lex-skeleton-card"><div class="lex-skeleton lex-skeleton-title"></div><div class="lex-skeleton lex-skeleton-line"></div><div class="lex-skeleton lex-skeleton-line" style="width:60%;"></div></div>
                    <div class="lex-skeleton-card"><div class="lex-skeleton lex-skeleton-title"></div><div class="lex-skeleton lex-skeleton-line"></div><div class="lex-skeleton lex-skeleton-line" style="width:60%;"></div></div>
                    <div class="lex-skeleton-card"><div class="lex-skeleton lex-skeleton-title"></div><div class="lex-skeleton lex-skeleton-line"></div><div class="lex-skeleton lex-skeleton-line" style="width:60%;"></div></div>
                </div>
            </div>
            """)

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
                ui.notify("Please select at least one framework.", type="warning", position='top')
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
                "Reading policy PDF..."
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
            # DOCUMENT TRIAGE — POLICY-ONLY GATE
            # =================================================

            status.set_text(
                "Classifying document type..."
            )

            logger.info("Running document triage classification...")

            import asyncio as _aio_triage
            import functools as _ft_triage
            triage_result = await _aio_triage.get_event_loop().run_in_executor(
                None,
                _ft_triage.partial(triage_document, policy_text),
            )

            if not triage_result["is_policy"]:
                logger.info(
                    "Triage REJECTED document: type='%s', reason='%s'",
                    triage_result.get("document_type", "Unknown"),
                    triage_result.get("reason", ""),
                )

                doc_type = triage_result.get("document_type", "Non-Policy Document")
                reason = triage_result.get("reason", "This document does not appear to be a company policy.")

                # ---- Rejection UI ----
                rejection_msg = (
                    f"⚠️ Document Rejected — This appears to be a "
                    f"{doc_type}, not a company policy."
                )
                status.set_text(rejection_msg)
                status_spinner.set_visibility(False)
                ui.notify(
                    f"Not a policy document: {reason}",
                    type="warning",
                    close_button=True,
                    position='top',
                )

                # Clear all tab containers and show rejection state
                try:
                    score_container.clear()
                    posture_container.clear()
                    gap_container.clear()
                    action_container.clear()
                    compliant_container.clear()
                    export_container.clear()
                except RuntimeError:
                    button.enable()
                    return

                # Score tab: show 0% with rejection explanation
                with score_container:
                    with ui.card().classes("w-full p-6").style(
                        "background: linear-gradient(135deg, #fef3cd 0%, #fff8e1 100%); "
                        "border: 2px solid #f0ad4e; border-radius: 12px;"
                    ):
                        with ui.column().classes("w-full items-center gap-4"):
                            ui.label("0%").style(
                                "font-size: 4rem; font-weight: 900; color: #856404; line-height: 1;"
                            )
                            ui.label("NOT A POLICY DOCUMENT").style(
                                "font-size: 1.2rem; font-weight: 700; color: #856404; "
                                "letter-spacing: 0.05em;"
                            )
                            ui.separator()
                            ui.label(f"Document Type: {doc_type}").style(
                                "font-size: 1rem; font-weight: 600; color: #664d03;"
                            )
                            ui.label(reason).style(
                                "font-size: 0.95rem; color: #664d03; text-align: center; "
                                "max-width: 600px;"
                            )
                            ui.label(
                                "Please upload a company policy document "
                                "(e.g., Privacy Policy, Security Policy, Data Protection Policy) "
                                "to receive a compliance score."
                            ).style(
                                "font-size: 0.85rem; color: #997a00; text-align: center; "
                                "max-width: 600px; margin-top: 8px;"
                            )

                # Other tabs: show empty-state message
                _rejection_empty_msg = (
                    "No compliance data — the uploaded document was not "
                    "recognized as a company policy."
                )
                for _container in [
                    posture_container, gap_container,
                    action_container, compliant_container,
                    export_container,
                ]:
                    with _container:
                        ui.label(_rejection_empty_msg).classes("lex-empty-state")

                button.enable()
                return

            logger.info("Triage PASSED: document classified as '%s'.", triage_result.get("document_type", "Policy"))

            # =================================================
            # RUN REAL ADK PIPELINE
            # =================================================

            status.set_text(
                "Running LexMesh compliance analysis..."
            )

            # Step tracker (3): Move to step 3 (Analyse)
            ui.run_javascript("""
                var s2 = document.getElementById('lstep2'); if(s2){s2.classList.remove('active'); s2.classList.add('done');}
                var c2 = document.getElementById('lconn2'); if(c2) c2.classList.add('done');
                var s3 = document.getElementById('lstep3'); if(s3) s3.classList.add('active');
            """)

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
                "✅ Compliance analysis completed successfully.",
                type="positive",
                position='top',
            )

            # Step tracker (3): Move to step 4 (Report)
            ui.run_javascript("""
                var s3 = document.getElementById('lstep3'); if(s3){s3.classList.remove('active'); s3.classList.add('done');}
                var c3 = document.getElementById('lconn3'); if(c3) c3.classList.add('done');
                var s4 = document.getElementById('lstep4'); if(s4){s4.classList.remove('active'); s4.classList.add('done');}
            """)

            logger.info("=== ANALYSIS SUCCESS | Overall Score: %s%% ===", score)

        except Exception as e:

            if "client this element belongs to has been deleted" in str(e):
                logger.warning("Client session disconnected during analysis pipeline.")
                return

            logger.error("Analysis pipeline error: %s", e, exc_info=True)

            try:
                status.set_text(f"Analysis failed: {e}")
                ui.notify(f"Analysis failed: {e}", type="negative", position='top')
            except Exception:
                pass

        finally:

            button.enable()
            status_spinner.set_visibility(False)

    # ========================================================
    # CONNECT RUN BUTTON
    # ========================================================

    sidebar[
        "run_button"
    ].on_click(
        run_analysis
    )

    # 2. Keyboard shortcuts (Ctrl+Enter -> Run Analysis, Esc -> Clear Upload)
    ui.run_javascript("""
        window.addEventListener('keydown', function(e) {
            if ((e.ctrlKey || e.metaKey) && e.key === 'Enter') {
                e.preventDefault();
                var btn = document.querySelector('.lex-run-button') || document.querySelector('button.lex-btn-primary');
                if (btn && !btn.disabled) btn.click();
            }
            if (e.key === 'Escape') {
                var cBtn = document.querySelector('[title*="Remove"]') || document.querySelector('.lex-clear-btn');
                if (cBtn) cBtn.click();
            }
        });
    """)

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
        favicon="/static/favicon.png",
        port=port,
        storage_secret=config.NICEGUI_STORAGE_SECRET,
        reload=False,
    )
