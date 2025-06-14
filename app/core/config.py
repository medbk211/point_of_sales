import os
from pydantic_settings import BaseSettings
from dotenv import load_dotenv

# Charger les variables d'environnement depuis .env
load_dotenv()

class Settings(BaseSettings):
    DATABASE_URL: str = os.getenv("DATABASE_URL")
    SECRET_KEY: str = os.getenv("SECRET_KEY", "supersecretkey")
    DEBUG: bool = os.getenv("DEBUG", "True").lower() == "true"
    

settings = Settings()
