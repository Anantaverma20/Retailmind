"""Supabase client singleton."""
from typing import Optional
from supabase import create_client, Client
from app.config import settings


_supabase_client: Optional[Client] = None


def get_supabase_client() -> Client:
    """Get or create Supabase client singleton."""
    global _supabase_client
    if _supabase_client is None:
        _supabase_client = create_client(settings.SUPABASE_URL, settings.SUPABASE_KEY)
    return _supabase_client


# Export for convenience
supabase = get_supabase_client

