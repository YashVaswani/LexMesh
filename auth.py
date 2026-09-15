from nicegui import app
from db.supabase_client import supabase_db

def sign_up(email, password):
    """Create account but do NOT log the user in — they must verify their email first."""
    if not supabase_db.is_connected():
        return False, "Database connection not initialized"
    try:
        res = supabase_db.client.auth.sign_up({
            "email": email,
            "password": password
        })
        if res.user:
            # Do NOT set session here — user must click the verification link first.
            return True, "CHECK_EMAIL"
        return False, "Unknown error during sign up"
    except Exception as e:
        return False, str(e)

def email_confirmed(access_token: str, refresh_token: str):
    """Called after user clicks the email confirmation link. Sets the session."""
    if not supabase_db.is_connected():
        return False, "Database connection not initialized"
    try:
        res = supabase_db.client.auth.set_session(access_token, refresh_token)
        if res.user:
            app.storage.user['user_id'] = res.user.id
            app.storage.user['email'] = res.user.email
            app.storage.user['access_token'] = access_token
            return True, res.user
        return False, "Could not verify session"
    except Exception as e:
        return False, str(e)

def sign_in(email, password):
    if not supabase_db.is_connected():
        return False, "Database connection not initialized"
    try:
        res = supabase_db.client.auth.sign_in_with_password({
            "email": email,
            "password": password
        })
        if res.user:
            app.storage.user['user_id'] = res.user.id
            app.storage.user['email'] = res.user.email
            app.storage.user['access_token'] = res.session.access_token if res.session else None
            return True, res.user
        return False, "Unknown error during sign in"
    except Exception as e:
        return False, str(e)

def sign_out():
    if not supabase_db.is_connected():
        return False, "Database connection not initialized"
    try:
        supabase_db.client.auth.sign_out()
        app.storage.user.clear()
        return True, "Signed out successfully"
    except Exception as e:
        app.storage.user.clear()
        return False, str(e)

def get_current_user():
    return app.storage.user.get('user_id')
