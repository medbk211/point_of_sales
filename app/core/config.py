import os
from pydantic_settings import BaseSettings
from dotenv import load_dotenv

# Charger les variables d'environnement depuis .env
load_dotenv()

class Settings(BaseSettings):
    DATABASE_URL: str = os.getenv("DATABASE_URL")
    SECRET_KEY: str = os.getenv("SECRET_KEY", "supersecretkey")
    DEBUG: bool = os.getenv("DEBUG", "True").lower() == "true"
    ALGORITHM : str = os.getenv("ALGORITHM", "HS256")
    ACCESS_TOKEN_EXPIRE_MINUTES :int =os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES",30)
    

settings = Settings()
