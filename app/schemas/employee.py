from pydantic import BaseModel, Field, EmailStr
from datetime import date
from app.enums import ContractTypeEnum, GenderEnum, StatusAccountEnum, RoleEnum
from typing import Optional, List

class OurBaseModel(BaseModel):
    class Config:
        
        from_attributes = True


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


class EmployeeCreate(EmployeeBase):
    password: Optional[str] = Field(None, min_length=6, max_length=100)  
    confirm_password: Optional[str] = Field(None, min_length=6, max_length=100)  
    role: List[RoleEnum] = Field(default_factory=list) 
class EmployeeInDB(EmployeeBase):
    password: str
    disabled: bool = False

class EmployeeOut(EmployeeBase):
    id: int 
    created_at: Optional[date] = None 
    role: List[RoleEnum] = Field(default_factory=list) 

class SetPasswordInput(BaseModel):
    token: str
    password: str
    confirm_password: str

class confirmation_out(OurBaseModel):
    detail: str  
    status_code: int  


class confirm_rest_pasword(OurBaseModel):
    email: EmailStr  


class confirm_rest_pasword_out(OurBaseModel):
    detail: str  
    status_code: int  

class rest_pasword(OurBaseModel):
    token: str  
    password: Optional[str] = Field(None, min_length=6, max_length=100)  
    confirm_password: Optional[str] = Field(None, min_length=6, max_length=100) 

class rest_pasword_out(OurBaseModel):
    detail: str 
    status_code: int  
