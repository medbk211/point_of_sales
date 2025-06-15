import os
from logging.config import fileConfig
from sqlalchemy import create_engine, pool
from alembic import context
from dotenv import load_dotenv
from app.core.database import Base  # Importer la base SQLAlchemy

# Charger les variables d'environnement
load_dotenv()

# Charger la config Alembic
config = context.config

# Définir l'URL de la base de données
database_url = os.getenv("DATABASE_URL")
if not database_url:
    raise ValueError("❌ DATABASE_URL is not set. Check your .env file.")

config.set_main_option("sqlalchemy.url", database_url)

# Configurer le logging si un fichier est spécifié
if config.config_file_name:
    fileConfig(config.config_file_name)

# Définir les métadonnées des modèles SQLAlchemy

from app.models.Employee import Employee
from app.models.EmployeeRole import Employee_role
from app.models.AcountActivation import Acount_Activation
from app.models.ChangePasword import ChangePasword
from app.models.error import Error
from app.models.EmailChangeToken import EmailChangeToken    

target_metadata = Base.metadata

def run_migrations_offline() -> None:
    """Exécute les migrations en mode 'offline'."""
    context.configure(
        url=database_url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
    )
    with context.begin_transaction():
        context.run_migrations()

def run_migrations_online() -> None:
    """Exécute les migrations en mode 'online'."""
    connectable = create_engine(database_url, poolclass=pool.NullPool)

    with connectable.connect() as connection:
        context.configure(connection=connection, target_metadata=target_metadata)
        with context.begin_transaction():
            context.run_migrations()

if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
