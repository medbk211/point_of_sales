from sqlalchemy import Column, Integer, String, Date, Enum, CheckConstraint
from sqlalchemy.sql import func
from app.core.database import Base
from app.enums import ContractTypeEnum, GenderEnum, StatusAccountEnum

class Employee(Base):
    __tablename__ = "employee"

    id = Column(Integer, primary_key=True, index=True)
    first_name = Column(String(50), nullable=False)
    last_name = Column(String(50), nullable=False)
    gender = Column(Enum(GenderEnum), nullable=False)
    birth_date = Column(Date, nullable=True)
    number = Column(String(10), unique=True, nullable=False)
    phone_number = Column(String(10), unique=True, nullable=True)
    address = Column(String(100), nullable=True)
    email = Column(String(100), unique=True, nullable=False)
    password = Column(String(100), nullable=True)
    contract_type = Column(Enum(ContractTypeEnum), nullable=True)
    status_account = Column(Enum(StatusAccountEnum), nullable=False, default=StatusAccountEnum.Inactive)
    cnss_number = Column(String(11), nullable=True, unique=True)  # Format attendu : 8 chiffres - 2 chiffres (total 11 caractères)
    created_at = Column(Date, nullable=False, server_default=func.now())

    __table_args__ = (
        CheckConstraint(
            "((contract_type::text IN ('CDI', 'CDD') AND cnss_number IS NOT NULL AND cnss_number ~ '^[0-9]{8}-[0-9]{2}$') "
            "OR (contract_type::text IN ('SIVP', 'APPRENTI') AND cnss_number IS NULL))",
            name="cnss_required_for_cdi_cdd"
        ),
    )
