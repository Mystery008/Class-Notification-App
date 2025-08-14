import os
from supabase import create_client

# Try to load local .env file only if running locally
try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass  # On Streamlit Cloud, secrets are already in env vars

def init_supabase():
    url = os.getenv("SUPABASE_URL")
    key = os.getenv("SUPABASE_KEY")

    if not url or not key:
        raise ValueError(
            "Supabase credentials not found. "
            "Set SUPABASE_URL and SUPABASE_KEY in your .env (local) "
            "or in Streamlit Cloud Secrets (deployment)."
        )

    return create_client(url, key)
