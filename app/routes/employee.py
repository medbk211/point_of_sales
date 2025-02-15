from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from app.schemas.employee import Employee, EmployeeCreate  # Import correct
from app.models import Employee as EmployeeModel
from app.core.database import get_db

router = APIRouter()

@router.post("/employees", response_model=Employee)  # Correction ici
def create_employee(employee: EmployeeCreate, db: Session = Depends(get_db)):
    db_employee = EmployeeModel(**employee.dict())  # Conversion correcte
    db.add(db_employee)
    db.commit()
    db.refresh(db_employee)
    return db_employee
