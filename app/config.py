"""Configuration management for the OMI Voice Inventory Assistant."""
import os
from typing import Optional
from pydantic_settings import BaseSettings
from pydantic import ValidationError


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""
    
    # Supabase - Allow None during initialization
    SUPABASE_URL: Optional[str] = None
    SUPABASE_KEY: Optional[str] = None
    
    # OMI
    OMI_WEBHOOK_TOKEN: Optional[str] = None
    
    # LLM
    OPENAI_API_KEY: Optional[str] = None
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
    ENABLE_RATE_LIMITING: bool = True  # Can disable for serverless (auto-disabled on Vercel)
    
    class Config:
        env_file = ".env"
        case_sensitive = True
    
    def validate_required(self):
        """Validate that required fields are set."""
        missing = []
        if not self.SUPABASE_URL:
            missing.append("SUPABASE_URL")
        if not self.SUPABASE_KEY:
            missing.append("SUPABASE_KEY")
        if not self.OMI_WEBHOOK_TOKEN:
            missing.append("OMI_WEBHOOK_TOKEN")
        if not self.OPENAI_API_KEY:
            missing.append("OPENAI_API_KEY")
        
        if missing:
            raise ValueError(
                f"Missing required environment variables: {', '.join(missing)}. "
                "Please set these in your Vercel project settings."
            )


# Initialize settings - allow None values, validate when used
try:
    settings = Settings()
except ValidationError as e:
    # If Pydantic validation fails, create a settings object with None values
    # This allows the app to start and show helpful error messages
    class DummySettings:
        SUPABASE_URL = None
        SUPABASE_KEY = None
        OMI_WEBHOOK_TOKEN = None
        OPENAI_API_KEY = None
        INTENT_PROVIDER = "openai"
        DEFAULT_LANGUAGE = "en"
        ENABLE_RATE_LIMITING = True
        
        def validate_required(self):
            raise ValueError(f"Configuration validation failed: {e}")
    
    settings = DummySettings()

