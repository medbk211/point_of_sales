import re
from datetime import datetime
from typing import Any, Optional
from app.enums.ContractTypeEnum import ContractTypeEnum
from app import enums

# --- Regex-based field matchers ------------------------------------------------

def is_regex_matched(pattern: str, field: Any) -> Optional[str]:
    """Return the field if it matches the regex, else None."""
    if isinstance(field, str) and re.match(pattern, field):
        return field
    return None


def is_valid_email(field: Any) -> Optional[str]:
    return is_regex_matched(
        r"^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$", field
    )


def is_valid_phone_number(field: Any) -> Optional[str]:
    # Tunisian phone numbers: +216 followed by 8 digits starting with 2,4,5,7,9
    return is_regex_matched(r"^\+216[24579]\d{7}$", field)


def check_cnss_contract_consistency(employee: dict, field: Any):

    ct = employee.get("contract_type")
    cnss = str(field).strip() if field not in (None, "") else ""

  
    if ct in {ContractTypeEnum.CDI.value, ContractTypeEnum.CDD.value}:
        if cnss == "":
            return None
        if not re.match(r"^[0-9]{8}-[0-9]{2}$", cnss):
            return None
        return cnss

    # SIVP or APPRNTI: must be empty
    if ct in {ContractTypeEnum.SIVP.value, ContractTypeEnum.APPRNTI.value}:
        return "" if cnss == "" else None

    # Other contracts: allow empty or valid
    if cnss == "":
        return ""
    return cnss if re.match(r"^[0-9]{8}-[0-9]{2}$", cnss) else None

# --- Date / Integer checks ----------------------------------------------------

def is_valid_date(field: Any):
   
    if not isinstance(field, str):
        return None
    try:
        datetime.strptime(field, "%Y-%m-%d")
        return field
    except ValueError:
        return None


def is_positive_int(field: Any):
    
    try:
        i = int(field)
        return i if i >= 0 else None
    except (ValueError, TypeError):
        return None

# --- Enum / Business-logic checks ---------------------------------------------

def are_roles_valid(field: Any) :
    """Accepts a comma-separated string or list of roles, returns True if valid."""
    if isinstance(field, str):
        roles = [r.strip() for r in field.split(",")]
    elif isinstance(field, list):
        roles = field
    else:
        return False

    valid = enums.RoleEnum.get_possiblevalue()
    return all(r in valid for r in roles)


def is_cdi_or_cdd(employee: dict):
    """Returns True if employee['contract_type'] is CDI or CDD."""
    ct = employee.get("contract_type")
    return ct in {ContractTypeEnum.CDI.value, ContractTypeEnum.CDD.value}

# --- Error-message mapping ----------------------------------------------------

error_keys = {
    "cnss_required_for_cdi_cdd":        "CNSS number is required for CDI and CDD contracts.",
    "employee_cnss_number_key":         "CNSS number already exists.",
    "employee_email_key":               "Email already exists.",
    "employee_number_key":              "Employee number already exists.",
    "employee_phone_number_key":        "Phone number already exists.",
    "employee_pkey":                    "Employee ID already exists.",
}

def get_error_message(error_message: str):
    for key, msg in error_keys.items():
        if key in error_message:
            return msg
    return "Unknown error occurred."
