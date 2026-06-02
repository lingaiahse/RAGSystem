from pydantic import BaseSettings, AnyUrl, Field


class Settings(BaseSettings):
    GEMINI_API_KEY: str = Field(..., env='GEMINI_API_KEY')
    JWT_PUBLIC_KEY: str = Field('', env='JWT_PUBLIC_KEY')
    JWT_ALGORITHM: str = Field('RS256', env='JWT_ALGORITHM')
    DATABASE_URL: AnyUrl = Field(None, env='DATABASE_URL')
    VECTOR_PROVIDER: str = Field('in_memory', env='VECTOR_PROVIDER')
    APP_HOST: str = Field('0.0.0.0', env='APP_HOST')
    APP_PORT: int = Field(8000, env='APP_PORT')

    class Config:
        env_file = '.env'


settings = Settings()
