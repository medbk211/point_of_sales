
from pydantic import BaseModel
from typing import List, Optional, Union, Dict

# Enums and Models
from app.enums.ConditionProperty import ConditionProperty
from app.enums.Comparer import Comparer
from app.enums.FieldType import FieldType
from app.enums.RoleEnum import RoleEnum
from app.enums.ContractTypeEnum import ContractTypeEnum
from app.enums.GenderEnum import GenderEnum





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

# ------------------- VALIDATION FUNCTION -------------------

