from fastapi import FastAPI
from app.routes import employee


app = FastAPI()

app.include_router(employee.router, prefix="/api")  # Vérifie le bon préfixe
