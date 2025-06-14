import os
import logging
import asyncio
from pathlib import Path
from typing import List
from dotenv import load_dotenv
from fastapi_mail import FastMail, MessageSchema, ConnectionConfig, MessageType
from pydantic import EmailStr

# Chargement des variables d'environnement depuis le fichier .env
load_dotenv()

# Configuration du serveur SMTP
conf = ConnectionConfig(
    MAIL_USERNAME=os.getenv("MAIL_USERNAME"),
    MAIL_PASSWORD=os.getenv("MAIL_PASSWORD"),
    MAIL_FROM=os.getenv("MAIL_FROM"),
    MAIL_PORT=int(os.getenv("MAIL_PORT", 587)),
    MAIL_SERVER=os.getenv("MAIL_SERVER"),
    MAIL_STARTTLS=os.getenv("MAIL_STARTTLS", "True").lower() == "true",
    MAIL_SSL_TLS=os.getenv("MAIL_SSL_TLS", "False").lower() == "true",
    USE_CREDENTIALS=True,
    VALIDATE_CERTS=True,
    TEMPLATE_FOLDER=Path(__file__).parent.parent / 'template'
)

# Fonction asynchrone pour envoyer un email en utilisant un template Jinja2
async def send_email_with_template(emails: List[EmailStr], body: dict):
    """
    Envoie un email en utilisant un template Jinja2.
    
    :param emails: Liste d'adresses email destinataires.
    :param body: Dictionnaire contenant les données à passer au template.
    :return: Dictionnaire indiquant le résultat de l'envoi.
    """

    message = MessageSchema(
        subject=" reset your password",
        recipients=emails,
        subtype=MessageType.html,
        template_body=body
    )

    fm = FastMail(conf)

    # Envoi de l'email en utilisant un template
    await fm.send_message(message, template_name="email.html")

    return {"message": "Email envoyé avec succès"}
