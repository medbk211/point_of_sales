from pydantic import BaseModel, Field, EmailStr
from datetime import date
from app.enums import ContractTypeEnum, GenderEnum, StatusAccountEnum, RoleEnum
from typing import Optional, List

# Base model class with configurations
class OurBaseModel(BaseModel):
    class Config:
        # Allows the model to be created from dictionaries, like ORM models
        from_attributes = True

# Employee base model with common fields for all employees
class EmployeeBase(OurBaseModel):
    first_name: str = Field(..., max_length=50)  # First name of the employee, max 50 characters
    last_name: str = Field(..., max_length=50)   # Last name of the employee, max 50 characters
    gender: GenderEnum  # Gender of the employee, uses the GenderEnum for validation
    birth_date: Optional[date] = None  # Optional birth date field
    number: str = Field(..., max_length=10)  # Employee's personal number, max 10 characters
    phone_number: Optional[str] = Field(None, max_length=8)  # Optional phone number field, max 8 characters
    address: Optional[str] = Field(None, max_length=100)  # Optional address field, max 100 characters
    email: EmailStr = Field(..., max_length=100)  # Email address of the employee, validated by EmailStr
    contract_type: Optional[ContractTypeEnum] = None  # Optional field for contract type, uses ContractTypeEnum
    cnss_number: Optional[str] = Field(None, max_length=11)  # Optional CNSS number, max 11 characters

# Employee creation model with password fields and role list
class EmployeeCreate(EmployeeBase):
    password: Optional[str] = Field(None, min_length=6, max_length=100)  # Optional password, min 6 characters
    confirm_password: Optional[str] = Field(None, min_length=6, max_length=100)  # Optional confirm password field
    role: List[RoleEnum] = Field(default_factory=list)  # List of roles assigned to the employee, defaults to an empty list

# Output model for employee information with ID and roles
class EmployeeOut(EmployeeBase):
    id: int  # Employee's unique ID
    created_at: Optional[date] = None  # Optional field for when the employee was created
    role: List[RoleEnum] = Field(default_factory=list)  # List of roles assigned to the employee

# Model for account confirmation using a token
class Confirmation_Acount(OurBaseModel):
    token: str  # Token used for account confirmation

# Output model for account confirmation with a status message
class confirmation_out(OurBaseModel):
    detail: str  # Details about the confirmation
    status_code: int  # Status code indicating success or failure of the confirmation process

# Model to request password reset by email
class confirm_rest_pasword(OurBaseModel):
    email: EmailStr  # Email address to send the password reset request

# Output model for password reset request with status details
class confirm_rest_pasword_out(OurBaseModel):
    detail: str  # Details about the password reset request
    status_code: int  # Status code indicating the result of the reset request

# Model for resetting password with token and new password details
class rest_pasword(OurBaseModel):
    token: str  # Token used to identify the password reset request
    password: Optional[str] = Field(None, min_length=6, max_length=100)  # New password, min 6 characters
    confirm_password: Optional[str] = Field(None, min_length=6, max_length=100)  # Confirm the new password

# Output model for password reset response with status details
class rest_pasword_out(OurBaseModel):
    detail: str  # Details about the password reset result
    status_code: int  # Status code indicating success or failure of the reset
