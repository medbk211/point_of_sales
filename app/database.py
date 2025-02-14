from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from app.config import settings  # Importation correcte de la configuration

# Créer le moteur SQLAlchemy
engine = create_engine(settings.DATABASE_URL, echo=True)

# Session pour interagir avec la base de données
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Base pour les modèles SQLAlchemy
Base = declarative_base()

def test_connection():
    """ Teste la connexion à la base de données. """
    try:
        db = SessionLocal()
        print("✅ Connexion réussie à la base de données !")
        db.close()
    except Exception as e:
        print(f"❌ Erreur de connexion : {e}")

# Tester la connexion seulement si ce fichier est exécuté directement
if __name__ == "__main__":
    test_connection()
