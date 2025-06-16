from typing import List
from fastapi import APIRouter, Depends, HTTPException, Response
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.orm import Session
from passlib.context import CryptContext

from app.routes import auth
from app.core.database import get_db
from app.models import Employee, EmailChangeToken, Employee_role
from app.schemas.employee import (
    EmployeeOut, EmployeeCreate, EmployeeProfile,
    EmailChangeRequest, AdminEmployeeUpdateRequest
)
from app.schemas.csvschema import options, CSVSchema, uploadCSV
from app.repositories.uploadcsv import mandatory_fields,valid_employees_data_and_upload
from app.enums import  RoleEnum
from app.service.Sending_email import send_email_with_template
from app.repositories.employee import (
    get_employee_id, get_all_employee, add_employee,
    update_employee, delete_employee,
    get_employee_role
)

router = APIRouter()
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="login")
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# Get all employees
@router.get("/employees", response_model=List[EmployeeOut])
def read_employees(db: Session = Depends(get_db)):
    return get_all_employee(db)

# Get a single employee by ID
@router.get("/employees/{employee_id}", response_model=EmployeeOut)
def read_employee(employee_id: int, db: Session = Depends(get_db)):
    employee = get_employee_id(db, employee_id)
    if not employee:
        raise HTTPException(status_code=404, detail="Employee not found")
    return employee

# Create a new employee
@router.post("/employees", response_model=EmployeeOut, status_code=201)
def create_employee(employee_data: EmployeeCreate, db: Session = Depends(get_db)):
    if employee_data.password != employee_data.confirm_password:
        raise HTTPException(status_code=400, detail="Passwords do not match")
    return add_employee(db, employee_data)


# Update full employee info (admin)
@router.put("/employees/{employee_id}", response_model=EmployeeOut)
def update_employee(employee_id: int, employee_data: EmployeeCreate, db: Session = Depends(get_db)):
    employee = update_employee(db, employee_id, employee_data)
    if not employee:
        raise HTTPException(status_code=404, detail="Employee not found")
    return employee

# Employee updates his profile
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

# Request to change email (confirmation link sent)
@router.put("/employees/email")
def request_email_change(data: EmailChangeRequest, db: Session = Depends(get_db), token: str = Depends(oauth2_scheme)):
    employee = auth.get_current_user(token, db)
    employee = db.query(Employee).filter(Employee.id == employee.id).first()
    if not employee:
        raise HTTPException(status_code=404, detail="Employee not found")
    if not auth.verify_password(data.current_password, employee.password):
        raise HTTPException(status_code=401, detail="Incorrect password")

    existing_email = db.query(Employee).filter(Employee.email == data.new_email).first()
    if existing_email:
        raise HTTPException(status_code=400, detail="Email already in use")

    confirmation_token = auth.generate_token()
    token_entry = EmailChangeToken(Employee_id=employee.id, new_email=data.new_email, token=confirmation_token)
    db.add(token_entry)
    db.commit()
    send_email_with_template(emails=[data.new_email], body={"token": confirmation_token}, subject="Email Change Confirmation", template_name="reset_password.html")
    return {"message": "Confirmation email sent to new address."}

# Confirm email change via token
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



# Admin updates employee fields (role, contract_type, etc.)
@router.put("/employees/{employee_id}/admin-update")
def admin_update_employee(employee_id: int, data_entry: AdminEmployeeUpdateRequest, db: Session = Depends(get_db), token: str = Depends(oauth2_scheme)):
    current_user = auth.get_current_user(token, db)
    if not current_user:
        raise HTTPException(status_code=401, detail="Invalid or expired token")
    role_record = get_employee_role(db, current_user.id)
    if not role_record or role_record.role != RoleEnum.admin:
        raise HTTPException(status_code=403, detail="Access denied. Admin only.")

    target_employee = db.query(Employee).filter(Employee.id == employee_id).first()
    if not target_employee:
        raise HTTPException(status_code=404, detail="Employee not found.")

    update_data = data_entry.model_dump(exclude_unset=True)
    updated = False
    for field in ["contract_type", "cnss_number", "number"]:
        if field in update_data:
            setattr(target_employee, field, update_data[field])
            updated = True
    if "role" in update_data:
        db.query(Employee_role).filter(Employee_role.Employee_id == employee_id).delete()
        for role in update_data["role"]:
            new_role = Employee_role(Employee_id=employee_id, role=role)
            db.add(new_role)
        updated = True

    if updated:
        db.commit()
        db.refresh(target_employee)

    return {
        "message": f"Employee ID {employee_id} updated successfully.",
        "updated_fields": update_data
    }

# Delete employee
@router.delete("/employees/{employee_id}", status_code=204)
def delete_employee_route(employee_id: int, db: Session = Depends(get_db)):
    if not delete_employee(db, employee_id):
        raise HTTPException(status_code=404, detail="Employee not found")
    return Response(status_code=204)

# Get allowed fields in CSV
@router.get("/possibleFilds", response_model=CSVSchema)
def get_csv_options(db: Session = Depends(get_db)):
    return CSVSchema(possible_fields=options)

# Upload and validate CSV employees
@router.post("/uploadCSV")
def upload_csv(entry: uploadCSV, db: Session = Depends(get_db)):
    employees = entry.lines
    if not employees:
        raise HTTPException(status_code=400, detail="CSV file is empty")
    first_row_keys = set(employees[0].keys())
    missing_fields = set(mandatory_fields.keys()) - first_row_keys
    if missing_fields:
        raise HTTPException(status_code=400, detail=f"Missing mandatory fields: {', '.join(missing_fields)}")
    return valid_employees_data_and_upload(employees, entry.forceUpload, db)
