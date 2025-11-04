"""Configuration management for the OMI Voice Inventory Assistant."""
import os
from typing import Optional
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""
    
    # Supabase
    SUPABASE_URL: str
    SUPABASE_KEY: str
    
    # OMI
    OMI_WEBHOOK_TOKEN: str
    
    # LLM
    OPENAI_API_KEY: str
    INTENT_PROVIDER: str = "openai"  # "openai" or "rules"
    DEFAULT_LANGUAGE: str = "en"  # "en" or "es"
    
    # Optional Integrations
    SHOPIFY_API_KEY: Optional[str] = None
    SHOPIFY_PASSWORD: Optional[str] = None
    SHOPIFY_STORE: Optional[str] = None
    QUICKBOOKS_CLIENT_ID: Optional[str] = None
    QUICKBOOKS_CLIENT_SECRET: Optional[str] = None
    AIRTABLE_API_KEY: Optional[str] = None
    
    # Feature flags
    ENABLE_SHOPIFY: bool = False
    ENABLE_QBO: bool = False
    ENABLE_AIRTABLE: bool = False
    
    class Config:
        env_file = ".env"
        case_sensitive = True


settings = Settings()

