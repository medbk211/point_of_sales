from sqlalchemy.orm import Session
from app.models.Employee import Employee
from app.models.EmployeeRole import Employee_role
from app.models.AcountActivation import Acount_Activation  # Correction
from app.models.ChangePasword import ChangePasword  # Correction

from app.enums.TokenStatusEnum import TokenStatusEnum
from app.schemas.employee import EmployeeCreate
from app.service.Sending_email import send_email_with_template
from fastapi.responses import JSONResponse 
from fastapi import HTTPException, status
import uuid
from datetime import datetime, timedelta, timezone
import logging

logger = logging.getLogger(__name__)

# ------------------------------------------------------
# 📌 Récupération de tous les employés
# ------------------------------------------------------
def get_all_employee(db: Session):
    """ Récupère tous les employés de la base de données. """
    return db.query(Employee).all()

# ------------------------------------------------------
# 📌 Récupération d'un employé par son ID
# ------------------------------------------------------
def get_employee_id(db: Session, id: int):
    """ Récupère un employé par son ID. """
    return db.query(Employee).filter(Employee.id == id).first()

# ------------------------------------------------------
# 📌 Récupération d'un employé par son adresse email
# ------------------------------------------------------
def get_employee_email(db: Session, email: str):
    """ Récupère un employé par son adresse email. """
    return db.query(Employee).filter(Employee.email == email).first()

# ------------------------------------------------------
# 📌 Récupération du code de confirmation par son code
# ------------------------------------------------------
def get_confirmation_code(db: Session, code: str):
    """ Récupère un code de confirmation par son code. """
    return db.query(Acount_Activation).filter(Acount_Activation.token == code).first()

# ------------------------------------------------------
# 📌 Récupération du code de confirmation pour la réinitialisation du mot de passe
# ------------------------------------------------------
def get_confirmation_code_change_password(db: Session, code: str):
    """ Récupère un code de confirmation pour réinitialiser le mot de passe par son code. """
    return db.query(ChangePasword).filter(ChangePasword.token == code).first()

# ------------------------------------------------------
# 📌 Ajout d'un employé avec gestion des rôles et envoi d'un email de confirmation
# ------------------------------------------------------
async def add_employee(db: Session, employee_data: EmployeeCreate):
    """ Ajoute un employé, attribue des rôles et envoie un email d'activation. """

    # Vérification si l'email existe déjà dans la base de données
    if get_employee_email(db, employee_data.email):
        return JSONResponse(status_code=400, content={"message": "Email already exists"})

    # Préparer les données de l'employé
    employee_dict = employee_data.model_dump()  # Transformation du schéma Pydantic en dictionnaire
    employee_dict.pop('confirm_password', None)  # Supprimer confirm_password qui ne doit pas être en base
    roles = employee_dict.pop('role', [])  # Extraire les rôles pour les ajouter après

    # Création de l'employé dans la base de données
    new_employee = Employee(**employee_dict)
    db.add(new_employee)
    db.commit()
    db.refresh(new_employee)  # Rafraîchir pour récupérer les valeurs générées (ex: ID)

    # Ajout des rôles à l'employé
    employee_roles = [Employee_role(Employee_id=new_employee.id, role=role) for role in roles]
    db.add_all(employee_roles)
    db.commit()

    # Génération d'un token UUID pour l'activation du compte
    token = str(uuid.uuid4())
    created_on = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S")

    # Création d'un enregistrement d'activation avec le token
    employee_Account_Activation = Acount_Activation(
        Employee_id=new_employee.id,
        Email=new_employee.email,
        token=token,
        created_on=created_on,
        token_status_id=TokenStatusEnum.Valid  # Statut du token actif
    )
    db.add(employee_Account_Activation)
    db.commit()

    # Envoi de l'email de confirmation avec gestion des erreurs
    try:
        await send_email_with_template([new_employee.email], {"token": token})
    except Exception as e:
        return JSONResponse(status_code=500, content={"message": "Employee added but email failed", "error": str(e)})

    return JSONResponse(status_code=200, content={"message": "Employee added and email sent", "employee_id": new_employee.id})

# ------------------------------------------------------
# 📌 Confirmation du changement de mot de passe d'un employé
# ------------------------------------------------------
async def confirmation_change_password(db: Session, employee: Employee):
    """ Confirme le changement de mot de passe d'un employé en générant un token. """
    
    # Génération d'un token unique pour le changement de mot de passe
    token = str(uuid.uuid4())
    expired_date = datetime.now(timezone.utc) + timedelta(hours=1)  # Expiration dans 1 heure

    # Enregistrement du changement de mot de passe dans la base
    employee_change_password = ChangePasword(
        Employee_id=employee.id,  
        expired_date=expired_date,
        token=token,
        token_status_id=TokenStatusEnum.Valid  # Statut du token valide
    )

    db.add(employee_change_password)
    db.commit()
    db.refresh(employee_change_password)  # Rafraîchir pour récupérer les valeurs générées

    # Envoi de l'email de réinitialisation du mot de passe avec gestion des erreurs
    try:
        await send_email_with_template([employee.email], {"token": token})
    except Exception as e:
        return JSONResponse(status_code=500, content={"message": "Employee added but email failed", "error": str(e)})

    return JSONResponse(status_code=200, content={"message": "Employee added and email sent", "employee_id": employee.id})

# ------------------------------------------------------
# 📌 Mise à jour des informations d'un employé
# ------------------------------------------------------
def update_employee(db: Session, id: int, employee_data: EmployeeCreate):
    """ Met à jour un employé existant. """
    employee = get_employee_id(db, id)
    if employee:
        # Extraire les données à mettre à jour
        update_data = employee_data.model_dump(exclude_unset=True)
        update_data.pop('confirm_password', None)  # Ne pas mettre à jour confirm_password
        update_data.pop('role', None)  # Ne pas mettre à jour les rôles directement

        # Mise à jour des attributs de l'employé
        for attr, new_val in update_data.items():
            setattr(employee, attr, new_val)

        db.commit()  # Appliquer les changements dans la base de données
        db.refresh(employee)  # Rafraîchir les données
        return employee
    return None

# ------------------------------------------------------
# 📌 Suppression d'un employé
# ------------------------------------------------------
def delete_employee(db: Session, id: int):
    """ Supprime un employé de la base de données. """
    employee = get_employee_id(db, id)
    if employee:
        db.delete(employee)  # Supprimer l'employé
        db.commit()  # Appliquer les changements
        return True
    return False
