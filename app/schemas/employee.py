from pydantic import BaseModel, Field, EmailStr
from datetime import date
from typing import Optional, List

from app.enums import ContractTypeEnum, GenderEnum, StatusAccountEnum, RoleEnum


# === Base Config ===
class OurBaseModel(BaseModel):
    class Config:
        from_attributes = True


# === Shared Base for Employees ===
class EmployeeBase(OurBaseModel):
    first_name: str = Field(..., max_length=50)
    last_name: str = Field(..., max_length=50)
    gender: GenderEnum
    birth_date: Optional[date] = None
    number: str = Field(..., max_length=11)
    phone_number: Optional[str] = Field(None, max_length=15)
    address: Optional[str] = Field(None, max_length=100)
    email: EmailStr = Field(..., max_length=100)
    contract_type: Optional[ContractTypeEnum] = None
    cnss_number: Optional[str] = Field(None, max_length=11)


# === Employee Profile View (for personal info only) ===
class EmployeeProfile(OurBaseModel):
    first_name: str = Field(..., max_length=50)
    last_name: str = Field(..., max_length=50)
    gender: GenderEnum
    birth_date: Optional[date] = None
    phone_number: Optional[str] = Field(None, max_length=15)
    address: Optional[str] = Field(None, max_length=100)


# === Create Employee Input ===
class EmployeeCreate(EmployeeBase):
    password: Optional[str] = Field(None, min_length=6, max_length=100)
    confirm_password: Optional[str] = Field(None, min_length=6, max_length=100)
    role: List[RoleEnum] = Field(default_factory=list)


# === Employee in DB (internal model) ===
class EmployeeInDB(EmployeeBase):
    password: str
    disabled: bool = False


# === Output Employee to clients ===
class EmployeeOut(EmployeeBase):
    id: int
    created_at: Optional[date] = None
    role: List[RoleEnum] = Field(default_factory=list)


# === Admin Update Employee Request ===
class AdminEmployeeUpdateRequest(BaseModel):
    contract_type: Optional[str] = None
    cnss_number: Optional[str] = None
    number: str = Field(..., max_length=11)
    role: List[RoleEnum] = Field(default_factory=list)


# === Email Change Request ===
class EmailChangeRequest(BaseModel):
    new_email: EmailStr
    current_password: str


# === Password Change Request ===
class PasswordChangeRequest(BaseModel):
    current_password: str
    new_password: str = Field(..., min_length=6, max_length=100)
    confirm_new_password: str = Field(..., min_length=6, max_length=100)


# === Set Password After Token (e.g. from Email) ===
class SetPasswordInput(BaseModel):
    token: str
    password: str
    confirm_password: str


# === Confirm Password Reset Request (step 1) ===
class ConfirmResetPasswordRequest(OurBaseModel):
    email: EmailStr


# === Confirm Reset Password Response (step 1 response) ===
class ConfirmResetPasswordResponse(OurBaseModel):
    detail: str
    status_code: int


# === Reset Password with Token (step 2) ===
class ResetPasswordRequest(OurBaseModel):
    token: str
    password: Optional[str] = Field(None, min_length=6, max_length=100)
    confirm_password: Optional[str] = Field(None, min_length=6, max_length=100)


# === Reset Password Final Response ===
class ResetPasswordResponse(OurBaseModel):
    detail: str
    status_code: int


# === Generic Confirmation Output ===
class ConfirmationResponse(OurBaseModel):
    detail: str
    status_code: int
