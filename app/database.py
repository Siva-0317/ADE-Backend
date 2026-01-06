from app.config import get_settings
from typing import Optional

settings = get_settings()

# Make Supabase optional for MVP
supabase = None

try:
    from supabase import create_client, Client
    supabase: Optional[Client] = create_client(
        settings.SUPABASE_URL,
        settings.SUPABASE_KEY
    )
    print("✓ Supabase connected successfully")
except Exception as e:
    print(f"⚠ Supabase connection failed: {e}")
    print("⚠ Running without Supabase - auth features disabled for MVP")
    supabase = None

def get_supabase():
    if supabase is None:
        raise Exception("Supabase not available - please use API without auth for MVP")
    return supabase
