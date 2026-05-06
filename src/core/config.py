from pydantic_settings import BaseSettings

 
class Settings(BaseSettings):
    APP_NAME: str = "Каталог продуктов"
    SECRET_KEY: str = "secret_key_not_for_production"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60 * 8
    DATABASE_URL: str = "postgresql+asyncpg://postgres:postgres@db:5432/product_catalog"
    NB_API_URL: str = "https://api.nbrb.by/exrates/rates/431?periodicity=0"
 
    class Config:
        env_file = ".env"
 
 
settings = Settings()