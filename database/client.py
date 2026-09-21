from supabase import create_client, Client
_supabase: Client | None = None

def get_supabase() -> Client:
    global _supabase
    if _supabase is None:
        import streamlit as st
        SUPABASE_URL = st.secrets.get("SUPABASE_URL")
        # ↓修正这里，和toml里面键名保持一致 SUPABASE_KEY
        SUPABASE_KEY = st.secrets.get("SUPABASE_KEY")

        if not SUPABASE_URL or not SUPABASE_KEY:
            raise Exception("请在 .streamlit/secrets.toml 配置 SUPABASE_URL / SUPABASE_KEY")
        
        _supabase = create_client(SUPABASE_URL, SUPABASE_KEY)
    return _supabase
