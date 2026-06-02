# backend/app/config.py
from typing import Optional
from pydantic import AnyUrl, Field
from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    # In Pydantic v2, we pass env variable names using validation_alias
    GEMINI_API_KEY: str = Field(..., validation_alias='GEMINI_API_KEY')
    JWT_PUBLIC_KEY: str = Field('', validation_alias='JWT_PUBLIC_KEY')
    JWT_ALGORITHM: str = Field('RS256', validation_alias='JWT_ALGORITHM')
    
    # Using Optional[] for fields that can be None/empty
    DATABASE_URL: Optional[AnyUrl] = Field(None, validation_alias='DATABASE_URL')
    VECTOR_PROVIDER: str = Field('in_memory', validation_alias='VECTOR_PROVIDER')
    APP_HOST: str = Field('0.0.0.0', validation_alias='APP_HOST')
    APP_PORT: int = Field(8000, validation_alias='APP_PORT')
    DEV_AUTH_BYPASS: bool = Field(False, validation_alias='DEV_AUTH_BYPASS')
    DEV_USER_JSON: Optional[str] = Field(None, validation_alias='NEXT_PUBLIC_DEV_USER')

    # This replaces the old 'class Config:' block entirely
    model_config = SettingsConfigDict(
        env_file='.env', 
        env_file_encoding='utf-8', 
        extra='ignore' # Ignores extra fields in your .env without crashing
    )

settings = Settings()