from pydantic import BaseModel, Field
from datetime import date
from app.enums import ContractTypeEnum, GenderEnum, StatusAccountEnum
from typing import Optional

class EmployeeBase(BaseModel):
    first_name: str = Field(..., max_length=50)
    last_name: str = Field(..., max_length=50)
    gender: GenderEnum
    number: str = Field(..., max_length=10)
    phone_number: Optional[str] = Field(None, max_length=10)
    email: str = Field(..., max_length=100)
    birth_date: Optional[date] = None  # يمكن تركه فارغًا
    address: Optional[str] = Field(None, max_length=100)
    contract_type: Optional[ContractTypeEnum] = None  # اختياري
    status_account: StatusAccountEnum = StatusAccountEnum.Inactive  # قيمة افتراضية
    cnss_number: Optional[str] = Field(None, max_length=11)
    created_at: Optional[date] = None  # يتم تحديده تلقائيًا من قاعدة البيانات

    class Config:
        from_attributes = True  # التعامل مع الخصائص بطريقة صحيحة في Pydantic v2

# Schéma pour la création d'un employé
class EmployeeCreate(EmployeeBase):
    pass

# Schéma pour la réponse avec l'ID de l'employé
class Employee(EmployeeBase):
    id: int
    created_at: date

    class Config:
        from_attributes = True  # Nouvelle syntaxe pour Pydantic v2
