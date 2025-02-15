from fastapi import FastAPI
from app.routes import employee  # Assure-toi d'importer le bon fichier de routes

app = FastAPI()

app.include_router(employee.router, prefix="/api")  # Vérifie le bon préfixe
