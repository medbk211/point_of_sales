from os import error
from sqlalchemy.orm import Session
from app.models.Employee import Employee
from app.models.EmployeeRole import Employee_role
from app.models.AcountActivation import Acount_Activation  # Correction
from app.models.ChangePasword import ChangePasword  # Correction
from app.models.error import Error



from app.enums.TokenStatusEnum import TokenStatusEnum
from app.schemas.employee import EmployeeCreate
from app.service.Sending_email import send_email_with_template
from app.utils.helpers import get_error_message
from fastapi.responses import JSONResponse 
from fastapi import HTTPException
import uuid
from datetime import datetime, timedelta, timezone
import logging


from passlib.context import CryptContext

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

logger = logging.getLogger(__name__)


def get_all_employee(db: Session):
    """ Récupère tous les employés de la base de données. """
    return db.query(Employee).all()



def get_employee_id(db: Session, id: int):
    """ Récupère un employé par son ID. """
    return db.query(Employee).filter(Employee.id == id).first()

def get_employee_email(db: Session, email: str):
    """ Récupère un employé par son adresse email. """
    return db.query(Employee).filter(Employee.email == email).first()


def get_confirmation_code(db: Session, code: str):
    """ Récupère un code de confirmation par son code. """
    return db.query(Acount_Activation).filter(Acount_Activation.token == code).first()

def get_confirmation_code_change_password(db: Session, code: str):
    """ Récupère un code de confirmation pour réinitialiser le mot de passe par son code. """
    return db.query(ChangePasword).filter(ChangePasword.token == code).first()


def add_error_log(error_message, db: Session):
    try : 
        error = Error(
            error_message=error_message,
            created_at=datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S")
        )    
        db.add(error)
        db.commit()
        db.refresh(error)
        return error
    except Exception as e:
        logger.error(f"Failed to log error: {str(e)}")
        return None



async def add_employee(db: Session, employee_data: EmployeeCreate):
    

    try:
        # Préparation des données
        employee_dict = employee_data.model_dump(exclude={'confirm_password'})
        roles = employee_dict.pop('role', [])

        # Hashage du mot de passe
        if employee_data.password:
            employee_dict["password"] = pwd_context.hash(employee_data.password)

        # Création de l'employé sans commit immédiat
        new_employee = Employee(**employee_dict)
        db.add(new_employee)
        db.flush()  # Permet d'obtenir l'ID sans commit
        db.refresh(new_employee)

        # Assignation des rôles (si présents)
        if roles:
            db.add_all([
                Employee_role(Employee_id=new_employee.id, role=role)
                for role in roles
            ])

        # Création et ajout du token d'activation
        token = str(uuid.uuid4())
        activation = Acount_Activation(
            Employee_id=new_employee.id,
            Email=new_employee.email,
            token=token,
            created_on=datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S"),
            token_status_id=TokenStatusEnum.Valid
        )
        db.add(activation)
        db.commit()

        # Envoi d'email en tâche de fond
        await  send_email_with_template(emails=[new_employee.email], body={"token": token},subject="Set Your Password",template_name="set_password.html") 
        return JSONResponse(
        status_code=200,
        content={"message": "Employee added", "employee_id": new_employee.id}
       )

    except Exception as e:
        db.rollback()  # Annulation en cas d'erreur
        add_error_log(str(e), db)  # Enregistrement de l'erreur dans la base de données
        raise HTTPException(status_code=500, detail=get_error_message(str(e)))
    
    



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
        await send_email_with_template(emails=[employee.email], body={"token": token},subject="Reset Your Password",template_name="reset_password.html")
    except Exception as e:
        return JSONResponse(status_code=500, content={"message": " email failed", "error": str(e)})

    return JSONResponse(status_code=200, content={"message": "email sent check your mail :)", "employee_id": employee.id})

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
