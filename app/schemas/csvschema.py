from fastapi import HTTPException, status
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field
from typing import List, Optional, Union, Dict
from sqlalchemy import select
from datetime import datetime, timezone
from passlib.context import CryptContext
import uuid
import time
import asyncio

# Enums and Models
from app.enums.ConditionProperty import ConditionProperty
from app.enums.Comparer import Comparer
from app.enums.FieldType import FieldType
from app.enums.RoleEnum import RoleEnum
from app.enums.ContractTypeEnum import ContractTypeEnum
from app.enums.GenderEnum import GenderEnum
from app.enums.TokenStatusEnum import TokenStatusEnum
from app.models.Employee import Employee
from app.models.EmployeeRole import Employee_role
from app.models.AcountActivation import Acount_Activation
from app.service.Sending_email import send_email_with_template
from app.utils.helpers import (
    is_positive_int,
    is_valid_date,
    check_cnss_contract_consistency,
    is_valid_phone_number,
    are_roles_valid,
    is_valid_email,
    is_cdi_or_cdd,
    get_error_message
)


pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# ------------------- MODELS -------------------
class OurBaseModel(BaseModel):
    class Config:
        from_attributes = True
class   BaseOut(BaseModel):
    details : str
    status_code : int 


class Condition(OurBaseModel):
    property: ConditionProperty
    value: Union[int, float, str, List[str]]
    comparer: Comparer
    custom_fail_message: Optional[str] = None

class Option(OurBaseModel):
    display_value: str
    value: Optional[str] = None
    mandatory: Optional[bool] = False
    type: FieldType
    conditions: Optional[List[Condition]] = []

class Matchycell(OurBaseModel):
    value: str
    rowIndex: int
    columnIndex: int

class CSVSchema(OurBaseModel):
    possible_fields: List[Option]

class Matchyworngcell(OurBaseModel):
    errorMessage: str
    rowIndex: int
    colIndex: int

class uploadCSV(OurBaseModel):
    lines: List[Dict[str, Matchycell]]
    forceUpload: Optional[bool] = False

class uploadCSVResponse(BaseOut):
    wrongCells: List[Matchyworngcell] 
    errors: str
    warnings: str

# ------------------- FIELD CHECK -------------------
fields_check = {
    "email": (
        lambda employee, field: is_valid_email(field),
        "Wrong Email format"
    ),
    "gender": (
        lambda employee, field: GenderEnum.is_valid(field),
        f"Possible values are: {GenderEnum.get_possiblevalue()}"
    ),
    "contract_type": (
        lambda employee, field: ContractTypeEnum.is_valid(field),
        f"Possible values are: {ContractTypeEnum.get_possiblevalue()}"
    ),
    "number": (
        lambda employee, field: is_positive_int(field),
        "It should be an integer >= 0"
    ),
    "birth_date": (
        lambda employee, field: is_valid_date(field),
        "Date format should be dd/mm/yyyy"
    ),
    "cnss_number": (
        lambda employee, field: check_cnss_contract_consistency(employee, field),
        "CNSS number is required and must match format 'XXXXXXXX-XX' for CDI or CDD contracts. For SIVP or APPRNTI, it must be empty."
    ),
    "phone_number": (
        lambda employee, field: is_valid_phone_number(field),
        "Phone number is not valid for Tunisia. It should be of 8 digits"
    ),
    "employee_roles": (
        lambda employee, field: are_roles_valid(field),
        f"Possible values are: {RoleEnum.get_possiblevalue()}"
    ),
    "job_position": (
        lambda employee, field: RoleEnum.is_valid(field),
        f"Possible values are: {RoleEnum.get_possiblevalue()}"
    ),
}

# ------------------- OPTIONS DEFINITION -------------------
options = [
    Option(display_value="First Name", value="first_name", mandatory=True, type=FieldType.string),
    Option(display_value="Last Name", value="last_name", mandatory=True, type=FieldType.string),
    Option(display_value="Email", value="email", mandatory=True, type=FieldType.string, conditions=[
        Condition(property=ConditionProperty.regex, comparer=Comparer.e, value=r"^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$")
    ]),
    Option(display_value="Address", value="address", mandatory=False, type=FieldType.string),
    Option(display_value="Phone Number", value="phone_number", mandatory=False, type=FieldType.string, conditions=[
        Condition(property=ConditionProperty.regex, comparer=Comparer.e, value=r"^\+216[24579]\d{7}$")
    ]),
    Option(display_value="Job Position", value="job_position", mandatory=True, type=FieldType.string, conditions=[
        Condition(property=ConditionProperty.value, comparer=Comparer.in_, value=RoleEnum.get_possiblevalue())
    ]),
    Option(display_value="Birth Date", value="birth_date", mandatory=False, type=FieldType.string, conditions=[
        Condition(property=ConditionProperty.regex, comparer=Comparer.e, value=r"^\d{4}-\d{2}-\d{2}$")
    ]),
    Option(display_value="Contract Type", value="contract_type", mandatory=True, type=FieldType.string, conditions=[
        Condition(property=ConditionProperty.value, comparer=Comparer.in_, value=ContractTypeEnum.get_possiblevalue())
    ]),
    Option(display_value="CNSS Number", value="cnss_number", mandatory=False, type=FieldType.string, conditions=[
        Condition(property=ConditionProperty.regex, comparer=Comparer.e, value=r"^[0-9]{8}-[0-9]{2}$")
    ]),
    Option(display_value="Gender", value="gender", mandatory=True, type=FieldType.string, conditions=[
        Condition(property=ConditionProperty.value, comparer=Comparer.in_, value=GenderEnum.get_possiblevalue())
    ]),
    Option(display_value="Employee Number", value="number", mandatory=True, type=FieldType.integer, conditions=[
        Condition(property=ConditionProperty.regex, comparer=Comparer.e, value=r"^\d{1,10}$")
    ]),
]

mandatory_fields = {opt.value: opt.display_value for opt in options if opt.mandatory}
optional_fields = {opt.value: opt.display_value for opt in options if not opt.mandatory}
mandatory_with_conditions = {
    "cnss_number": (
        True,
        # employee here is the cleaned dict passed from validate_employee_data
        lambda emp: emp.get("contract_type") in {ContractTypeEnum.CDI.value, ContractTypeEnum.CDD.value}
    )
}

possible_fields = {**mandatory_fields, **optional_fields, **mandatory_with_conditions}
unique_fields = {
    "email": Employee.email,
    "number": Employee.number,
    "phone_number": Employee.phone_number,
    "cnss_number": Employee.cnss_number
}

# ------------------- VALIDATION FUNCTION -------------------
def is_field_mandatory(employee, field):
    return field in mandatory_fields or (
        field in mandatory_with_conditions and mandatory_with_conditions[field][1](employee)
    )

def validate_employee_data(employee):
    errors, warnings, wrong_cells = [], [], []
    # Build cleaned dict first
    employee_to_add = {
        field: (cell.value.strip() if isinstance(cell.value, str) else cell.value)
        for field, cell in employee.items()
    }

    for field in possible_fields:
        # Determine if mandatory using cleaned dict
        if field not in employee_to_add:
            if is_field_mandatory(employee_to_add, field):
                msg = f"Missing mandatory field: {possible_fields[field]}"
                errors.append(msg)
                wrong_cells.append(Matchyworngcell(errorMessage=msg, rowIndex=cell.rowIndex,  colIndex=cell.columnIndex))

            employee_to_add[field] = None
            continue

        cell = employee[field]
        value = employee_to_add[field]

        # Empty string handling
        if value == '':
            if is_field_mandatory(employee_to_add, field):
                msg = f"Missing mandatory field: {possible_fields[field]}"
                errors.append(msg)
                wrong_cells.append(Matchyworngcell(errorMessage=msg, rowIndex=cell.rowIndex,  colIndex=cell.columnIndex))
            else:
                employee_to_add[field] = None

        # Field checks
        elif field in fields_check:
            valid = fields_check[field][0](employee_to_add, value)
            if valid is None:
                msg = fields_check[field][1]
                if is_field_mandatory(employee_to_add, field):
                    errors.append(msg)
                else:
                    warnings.append(msg)
                wrong_cells.append(Matchyworngcell(errorMessage=msg, rowIndex=cell.rowIndex,  colIndex=cell.columnIndex))
            else:
                employee_to_add[field] = valid

    return employee_to_add, errors, warnings, wrong_cells


# ------------------- MAIN VALIDATE & UPLOAD -------------------
async def valid_employees_data_and_upload(employees: list, force_upload: bool, db):
    errors, warnings, wrong_cells = [], [], []
    employees_to_add = []
    roles_anchor = {}

    for line_index, employee in enumerate(employees):
        # نتحقق من كل صفّ باستعمال دالة مخصصة
        emp_data, emp_errors, emp_warnings, emp_wrong_cells = validate_employee_data(employee)

        if emp_errors:
            errors.append(f"Line {line_index + 1}: " + "; ".join(emp_errors))
        if emp_warnings:
            warnings.append(f"Line {line_index + 1}: " + "; ".join(emp_warnings))
        if emp_wrong_cells:
            wrong_cells.extend(emp_wrong_cells)

        # ربط الإيميل بخطة العمل (job_position)
        email = emp_data.get("email")
        if email and "job_position" in emp_data:
            raw_positions = emp_data.pop("job_position")
            if raw_positions:
                roles_anchor[email] = [pos.strip() for pos in raw_positions.split(",")]

        employees_to_add.append(emp_data)

    # التحقق من القيم المكررة في الحقول الفريدة
    for field in unique_fields:
        seen_values = set()
        for line_index, employee in enumerate(employees):
            cell = employee.get(field)
            if not cell:
                continue
            value = cell.value.strip()
            if value == "":
                continue
            if value in seen_values:
                msg = f"{field.capitalize()} '{value}' is duplicated"
                errors.append(f"Line {line_index + 1}: {msg}")
                wrong_cells.append(
                    Matchyworngcell(
                        errorMessage=msg,
                        rowIndex=cell.rowIndex,
                        colIndex=cell.columnIndex
                    )
                )
            else:
                seen_values.add(value)

    # إذا فما أخطاء أو تحذيرات ومافماش forceUpload
    if errors or (warnings and not force_upload):
            return JSONResponse(
            status_code=400,
            content={
                "errors": "\n".join(errors),
                "warnings": "\n".join(warnings),
                "wrongCells": [c.model_dump() for c in wrong_cells],
                "details": "CSV file is not valid"
            }
        )

        
        
    

    # إذا البيانات سليمة، نواصل (إدخال قاعدة البيانات، إرسال الإيميلات...)
    try:
        emails_with_tokens = []  # Initialize the list to store email and token pairs
        start_time = time.perf_counter()
        db.bulk_insert_mappings(Employee, employees_to_add)
        db.flush()
        elapsed = time.perf_counter() - start_time
        print(f"✅ Inserted {len(employees_to_add)} employees in {elapsed:.4f} seconds.")

        anchors = list(roles_anchor.keys())
        stmt = select(Employee).where(Employee.email.in_(anchors))
        inserted_emps = db.execute(stmt).scalars().all()

        value_map = {member.value.lower(): member.value for member in RoleEnum}

        def normalize_position(raw_position: str):
            if not raw_position:
                return None
            return value_map.get(raw_position.strip().lower())

        roles_to_insert = []
        for emp in inserted_emps:
            raw_positions = roles_anchor.get(emp.email, [])
            for raw_pos in raw_positions:
                proper_role = normalize_position(raw_pos)
                if proper_role:
                    roles_to_insert.append({
                        "Employee_id": emp.id,
                        "role": proper_role
                    })

        if roles_to_insert:
            db.bulk_insert_mappings(Employee_role, roles_to_insert)

        # Insert account activations
        for emp in inserted_emps:
            token = str(uuid.uuid4())
            activation = Acount_Activation(
                Employee_id=emp.id,
                Email=emp.email,
                token=token,
                created_on=datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S"),
                token_status_id=TokenStatusEnum.Valid
            )
            db.add(activation)
            emails_with_tokens.append({"email": emp.email, "token": token})

        # db.commit()

        # # Function to send one email
        # async def send_single_email(email, token):
        #     await send_email_with_template([email], {"token": token})

        # # Create all tasks
        # tasks = [send_single_email(entry["email"], entry["token"]) for entry in emails_with_tokens]

        # # Run all tasks concurrently
        # await asyncio.gather(*tasks)

    except Exception as e:
        db.rollback()
        msg = get_error_message(str(e))
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=msg)
