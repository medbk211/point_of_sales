from fastapi import FastAPI
from app.database import database
import uvicorn

app = FastAPI()

# Connexion à la base de données au démarrage
@app.on_event("startup")
async def startup():
    await database.database.connect()
    print("🚀 FastAPI est prêt et connecté à la base de données !")

@app.on_event("shutdown")
async def shutdown():
    await database.database.disconnect()
    print("🛑 Déconnexion de la base de données.")

@app.get("/")
async def root():
    return {"message": "Bienvenue dans le système de point de vente !"}

if __name__ == "__main__":
    uvicorn.run(app, host="127.0.0.1", port=8000, reload=True)
