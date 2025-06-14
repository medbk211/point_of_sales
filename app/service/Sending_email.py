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
async def send_email_with_template(emails: List[EmailStr], body: dict, subject: str, template_name: str):
    try:
        message = MessageSchema(
            subject=subject,
            recipients=emails,
            subtype=MessageType.html,
            template_body=body
        )
        fm = FastMail(conf)
        await fm.send_message(message, template_name=template_name)
        return {"message": "Email envoyé avec succès"}
    except Exception as e:
        print(f"❌ Failed to send email to {emails}: {e}")
        return {"error": str(e)}
