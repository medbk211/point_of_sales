from typing import List
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

# Importation des modèles de la base de données
from app.models.Employee import Employee
from app.models.AcountActivation import Acount_Activation  # Correction du modèle
from app.models.ChangePasword import ChangePasword

# Pour le hashage sécurisé des mots de passe
from passlib.context import CryptContext

# Importation de la base de données et des fonctions CRUD
from app.core.database import get_db
from app.crud.employee import (
    get_employee_id,
    get_all_employee,
    add_employee,
    update_employee,
    delete_employee,
    get_employee_email,
    get_confirmation_code,
    confirmation_change_password,
    get_confirmation_code_change_password
)

# Importation des enums (statuts des tokens et comptes)
from app.enums import TokenStatusEnum, StatusAccountEnum

# Importation des schémas de validation Pydantic
from app.schemas.employee import (
    EmployeeOut,
    EmployeeCreate,
    Confirmation_Acount,
    confirmation_out,
    confirm_rest_pasword,
    confirm_rest_pasword_out,
    rest_pasword,
    rest_pasword_out
)

# Initialisation de l'outil de hashage de mots de passe
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# Création du routeur FastAPI
router = APIRouter()

# ------------------------------------
# 📌 Récupération de tous les employés
# ------------------------------------
@router.get("/employees", response_model=List[EmployeeOut])
def read_employees(db: Session = Depends(get_db)):
    """ Récupère la liste de tous les employés. """
    return get_all_employee(db)

# ------------------------------------
# 📌 Récupération d'un employé par son ID
# ------------------------------------
@router.get("/employees/{employee_id}", response_model=EmployeeOut)
def read_employee(employee_id: int, db: Session = Depends(get_db)):
    """ Récupère un employé spécifique en fonction de son ID. """
    employee = get_employee_id(db, employee_id)
    if not employee:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Employee not found")
    return employee

# ------------------------------------
# 📌 Création d'un employé
# ------------------------------------
@router.post("/employees", response_model=EmployeeOut, status_code=status.HTTP_201_CREATED)
async def create_employee(employee_data: EmployeeCreate, db: Session = Depends(get_db)):
    """ Crée un nouvel employé. """
    
    # Vérification si les mots de passe correspondent
    if employee_data.password != employee_data.confirm_password:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Passwords do not match")

    # Vérification si l'email existe déjà
    if get_employee_email(db, email=employee_data.email):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Email already exists")

    # Ajout de l'employé en base de données
    employee = await add_employee(db, employee_data)
    return employee

# ------------------------------------
# 📌 Envoi d'un email pour réinitialisation du mot de passe
# ------------------------------------
@router.post("/employees/confirm_reset_password", response_model=confirm_rest_pasword_out, status_code=status.HTTP_201_CREATED)
async def confirm_account(confirmation_data: confirm_rest_pasword, db: Session = Depends(get_db)):
    """ Envoie un email pour réinitialiser le mot de passe. """

    # Vérification si l'email existe en base
    employee_data = get_employee_email(db, email=confirmation_data.email)
    if not employee_data:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Employee not found"
        )

    # Génération et envoi du code de confirmation
    await confirmation_change_password(db, employee_data)
    
    return confirm_rest_pasword_out(status_code=str(200), detail="Envoie un email pour réinitialiser le mot de passe")

# ------------------------------------
# 📌 Confirmation de la réinitialisation du mot de passe
# ------------------------------------
@router.patch("/employees/confirm_reset_password", response_model=rest_pasword_out, status_code=status.HTTP_200_OK)
def confirmation_account(confirmation_input: rest_pasword, db: Session = Depends(get_db)):
    """ Confirme et applique la réinitialisation du mot de passe d'un employé. """

    # Vérification du code de confirmation
    confirmation_code = get_confirmation_code_change_password(db, confirmation_input.token)

    if not confirmation_code:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, 
            detail="Confirmation code not found"
        )

    if confirmation_code.token_status_id == TokenStatusEnum.Expired:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, 
            detail="Confirmation code expired"
        )

    if confirmation_input.password != confirmation_input.confirm_password:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Passwords do not match"
        )

    # Hashage du mot de passe avant mise à jour
    hashed_password = pwd_context.hash(confirmation_input.password)

    # Mise à jour du statut du token et du mot de passe en base de données
    db.query(ChangePasword).filter(ChangePasword.id == confirmation_code.id).update(
        {"token_status_id": TokenStatusEnum.Expired}
    )
    db.query(Employee).filter(Employee.id == confirmation_code.Employee_id).update(
        {"password": hashed_password}
    )
    
    db.commit()

    return confirmation_out(status_code=str(200), detail="Password changed successfully")

# ------------------------------------
# 📌 Confirmation de l'activation du compte employé
# ------------------------------------
@router.patch("/employees/confirm", response_model=confirmation_out, status_code=status.HTTP_200_OK)
def confirmation_account(confirmation_input: Confirmation_Acount, db: Session = Depends(get_db)):
    """ Active un compte employé après vérification du code de confirmation. """

    confirmation_code = get_confirmation_code(db, confirmation_input.token)

    if not confirmation_code:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, 
            detail="Confirmation code not found"
        )

    if confirmation_code.token_status_id == TokenStatusEnum.Expired:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, 
            detail="Confirmation code expired"
        )

    # Activation du compte employé et expiration du token d'activation
    db.query(Employee).filter(Employee.id == confirmation_code.Employee_id).update(
        {"status_account": StatusAccountEnum.Active}
    )
    db.query(Acount_Activation).filter(Acount_Activation.id == confirmation_code.id).update(
        {"token_status_id": TokenStatusEnum.Expired}
    )
    db.commit()
    
    return confirmation_out(status_code=str(200), detail="Account confirmed successfully")

# ------------------------------------
# 📌 Mise à jour d'un employé
# ------------------------------------
@router.put("/employees/{employee_id}", response_model=EmployeeOut)
def update_employee_route(employee_id: int, employee_data: EmployeeCreate, db: Session = Depends(get_db)):
    """ Met à jour les informations d'un employé existant. """
    
    employee = update_employee(db, employee_id, employee_data)
    if not employee:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Employee not found")
    return employee

# ------------------------------------
# 📌 Suppression d'un employé
# ------------------------------------
@router.delete("/employees/{employee_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_employee_route(employee_id: int, db: Session = Depends(get_db)):
    """ Supprime un employé en fonction de son ID. """

    if not delete_employee(db, employee_id):
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Employee not found")
    
    return {"message": "Employee deleted successfully"}
