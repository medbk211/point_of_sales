from typing import List
from fastapi import APIRouter, Depends, HTTPException
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.orm import Session
from passlib.context import CryptContext

from app import auth
from app.core.database import get_db
from app.models import Employee, Acount_Activation, ChangePasword, EmailChangeToken, Employee_role
from app.schemas.employee import (
    EmployeeOut, EmployeeCreate, EmployeeProfile,
    SetPasswordInput, confirmation_out,
    confirm_rest_pasword, confirm_rest_pasword_out,
    rest_pasword, rest_pasword_out,
    EmailChangeRequest, passwordChangeRequest,AdminEmployeeUpdateRequest
)
from app.schemas.csvschema import options, CSVSchema, uploadCSV, mandatory_fields, valid_employees_data_and_upload
from app.enums import TokenStatusEnum, StatusAccountEnum, RoleEnum
from app.service.Sending_email import send_email_with_template
from app.crud.employee import (
    get_employee_id, get_all_employee, add_employee,
    update_employee, delete_employee,
    get_employee_email, get_confirmation_code,
    confirmation_change_password, get_confirmation_code_change_password,get_employee_role
)

router = APIRouter()
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="login")
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# Get all employees
@router.get("/employees", response_model=List[EmployeeOut])
def read_employees(db: Session = Depends(get_db)):
    return get_all_employee(db)

# Get employee by ID
@router.get("/employees/{employee_id}", response_model=EmployeeOut)
def read_employee(employee_id: int, db: Session = Depends(get_db)):
    employee = get_employee_id(db, employee_id)
    if not employee:
        raise HTTPException(status_code=404, detail="Employee not found")
    return employee

# Create new employee
@router.post("/employees", response_model=EmployeeOut, status_code=201)
async def create_employee(employee_data: EmployeeCreate, db: Session = Depends(get_db)):
    if employee_data.password != employee_data.confirm_password:
        raise HTTPException(status_code=400, detail="Passwords do not match")
    return await add_employee(db, employee_data)

# Send reset password email
@router.post("/employees/reset_password", response_model=confirm_rest_pasword_out, status_code=201)
async def reset_password(confirmation_data: confirm_rest_pasword, db: Session = Depends(get_db)):
    employee_data = get_employee_email(db, email=confirmation_data.email)
    if not employee_data:
        raise HTTPException(status_code=404, detail="Employee not found")
    await confirmation_change_password(db, employee_data)
    return confirm_rest_pasword_out(status_code="200", detail="Reset password email sent")

# Confirm password reset
@router.patch("/employees/confirm_reset_password", response_model=rest_pasword_out, status_code=200)
def confirmation_reset_password(confirmation_input: rest_pasword, db: Session = Depends(get_db)):
    confirmation_code = get_confirmation_code_change_password(db, confirmation_input.token)
    if not confirmation_code:
        raise HTTPException(status_code=404, detail="Confirmation code not found")
    if confirmation_code.token_status_id == TokenStatusEnum.Expired:
        raise HTTPException(status_code=400, detail="Confirmation code expired")
    if confirmation_input.password != confirmation_input.confirm_password:
        raise HTTPException(status_code=400, detail="Passwords do not match")

    hashed_password = pwd_context.hash(confirmation_input.password)
    db.query(ChangePasword).filter(ChangePasword.id == confirmation_code.id).update({"token_status_id": TokenStatusEnum.Expired})
    db.query(Employee).filter(Employee.id == confirmation_code.Employee_id).update({"password": hashed_password})
    db.commit()
    return confirmation_out(status_code="200", detail="Password changed successfully")

# Confirm account activation and set password
@router.post("/employees/set_password", response_model=confirmation_out, status_code=200)
def set_password(input: SetPasswordInput, db: Session = Depends(get_db)):
    confirmation_code = get_confirmation_code(db, input.token)
    if not confirmation_code:
        raise HTTPException(status_code=404, detail="Confirmation code not found")
    if confirmation_code.token_status_id == TokenStatusEnum.Expired:
        raise HTTPException(status_code=400, detail="Confirmation code expired")
    if input.password != input.confirm_password:
        raise HTTPException(status_code=400, detail="Passwords do not match")

    hashed_pw = pwd_context.hash(input.password)
    db.query(Employee).filter(Employee.id == confirmation_code.Employee_id).update({
        "password": hashed_pw,
        "status_account": StatusAccountEnum.Active
    })
    db.query(Acount_Activation).filter(Acount_Activation.id == confirmation_code.id).update({
        "token_status_id": TokenStatusEnum.Expired
    })
    db.commit()
    return confirmation_out(status_code="200", detail="Password set, account activated.")

# Update employee
@router.put("/employees/{employee_id}", response_model=EmployeeOut)
def update_employee_route(employee_id: int, employee_data: EmployeeCreate, db: Session = Depends(get_db)):
    employee = update_employee(db, employee_id, employee_data)
    if not employee:
        raise HTTPException(status_code=404, detail="Employee not found")
    return employee

# Update profile
@router.put("/employees/profile")
def update_employee_profile(employee_data: EmployeeProfile, token: str = Depends(oauth2_scheme), db: Session = Depends(get_db)):
    employee = auth.get_current_user(token, db)
    if not employee:
        raise HTTPException(status_code=401, detail="Invalid or expired token")
    target_employee = db.query(Employee).filter(Employee.id == employee.id).first()
    if not target_employee:
        raise HTTPException(status_code=404, detail="Employee not found")

    update_data = employee_data.model_dump(exclude_unset=True)
    for key, value in update_data.items():
        setattr(target_employee, key, value)

    db.commit()
    db.refresh(target_employee)
    return {"message": "Profile updated successfully", "updated_fields": update_data}

# Request email change
@router.put("/employees/email")
async def request_email_change(data: EmailChangeRequest, db: Session = Depends(get_db), token: str = Depends(oauth2_scheme)):
    employee = auth.get_current_user(token, db)
    employee = db.query(Employee).filter(Employee.id == employee.id).first()
    if not employee:
        raise HTTPException(status_code=404, detail="Employee not found")
    if not auth.verify_password(data.current_password, employee.password):
        raise HTTPException(status_code=401, detail="Incorrect password")

    confirmation_token = auth.generate_token()
    token_entry = EmailChangeToken(Employee_id=employee.id, new_email=data.new_email, token=confirmation_token)
    db.add(token_entry)
    db.commit()
    await send_email_with_template(emails=[data.new_email], body={"token": confirmation_token}, subject="Email Change Confirmation", template_name="reset_password.html")
    return {"message": "Confirmation email sent to new address."}

# Confirm email change
@router.get("/confirm-email-change")
def confirm_email_change(token: str, db: Session = Depends(get_db)):
    token_entry = db.query(EmailChangeToken).filter(EmailChangeToken.token == token).first()
    if not token_entry:
        raise HTTPException(status_code=404, detail="Invalid or expired token")
    employee = db.query(Employee).filter(Employee.id == token_entry.Employee_id).first()
    if employee:
        employee.email = token_entry.new_email
        db.commit()
    db.delete(token_entry)
    db.commit()
    return {"message": "Email updated successfully."}

# Change password
@router.put("/employees/change-password")
def password_change_request(data_entry: passwordChangeRequest, db: Session = Depends(get_db), token: str = Depends(oauth2_scheme)):
    employee = auth.get_current_user(token, db)
    if not employee:
        raise HTTPException(status_code=401, detail="Invalid or expired token")
    employee_in_db = db.query(Employee).filter(Employee.id == employee.id).first()
    if not employee_in_db:
        raise HTTPException(status_code=404, detail="Employee not found")
    if not auth.verify_password(data_entry.current_password, employee_in_db.password):
        raise HTTPException(status_code=400, detail="Incorrect current password")
    if data_entry.new_password != data_entry.confirm_new_password:
        raise HTTPException(status_code=400, detail="New passwords do not match")

    hashed_password = pwd_context.hash(data_entry.new_password)
    employee_in_db.password = hashed_password
    db.commit()
    return {"message": "Password updated successfully."}

@router.put("/employees/{employee_id}/admin-update")
def admin_update_employee(employee_id: int, data_entry: AdminEmployeeUpdateRequest,db: Session = Depends(get_db), token: str = Depends(oauth2_scheme)):
    current_user = auth.get_current_user(token, db)
    if not current_user:
        raise HTTPException(status_code=401, detail="Invalid or expired token")
    role_record = get_employee_role(db, current_user.id)
    if not role_record or role_record.role !=  RoleEnum.admin:
        raise HTTPException(status_code=403, detail="Accès refusé. Admin uniquement.")
    target_employee = db.query(Employee).filter(Employee.id == employee_id).first()
    if not target_employee:
        raise HTTPException(status_code=404, detail="Employé introuvable.")
    update_data = data_entry.model_dump(exclude_unset=True)
    for field in ["contract_type", "cnss_number", "number"]:
        if field in update_data:
            setattr(target_employee, field, update_data[field])
    if "role" in update_data:
        
        db.query(Employee_role).filter(Employee_role.Employee_id == employee_id).delete()
        for role in update_data["role"]:
            new_role = Employee_role(Employee_id=employee_id, role=role)
            db.add(new_role)

        db.commit()
        db.refresh(target_employee)
        return {
        "message": f"Les informations de l'employé ID {employee_id} ont été mises à jour avec succès.",
        "updated_fields": update_data
    }    
        


# Delete employee
@router.delete("/employees/{employee_id}", status_code=204)
def delete_employee_route(employee_id: int, db: Session = Depends(get_db)):
    if not delete_employee(db, employee_id):
        raise HTTPException(status_code=404, detail="Employee not found")
    return {"message": "Employee deleted successfully"}

# Get possible fields for CSV
@router.get("/possibleFilds", response_model=CSVSchema)
def get_csv_options(db: Session = Depends(get_db)):
    return CSVSchema(possible_fields=options)

# Upload CSV
@router.post("/uploadCSV")
async def upload_csv(entry: uploadCSV, db: Session = Depends(get_db)):
    employees = entry.lines
    if not employees:
        raise HTTPException(status_code=400, detail="CSV file is empty")
    first_row_keys = set(employees[0].keys())
    missing_fields = set(mandatory_fields.keys()) - first_row_keys
    if missing_fields:
        raise HTTPException(status_code=400, detail=f"Missing mandatory fields: {', '.join(missing_fields)}")
    return await valid_employees_data_and_upload(employees, entry.forceUpload, db)