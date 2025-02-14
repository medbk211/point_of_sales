from sqlalchemy import Column, Integer, String, Date, Enum, CheckConstraint
from sqlalchemy.sql import func
from app.database import Base
from app.enums import ContractTypeEnum, GenderEnum, StatusAccountEnum

class Employee(Base):
    __tablename__ = "employee"

    id = Column(Integer, primary_key=True, index=True)
    first_name = Column(String(50), nullable=False)
    last_name = Column(String(50), nullable=False)
    gender = Column(Enum(GenderEnum), nullable=False)
    number = Column(String(10), unique=True, nullable=False)  # Assurez-vous qu'il est obligatoire
    phone_number = Column(String(10), unique=True, nullable=True)
    email = Column(String(100), unique=True, nullable=False)  # L'email est obligatoire
    birth_date = Column(Date, nullable=True)
    address = Column(String(100), nullable=True)
    contract_type = Column(Enum(ContractTypeEnum), nullable=True)  # Non obligatoire
    status_account = Column(Enum(StatusAccountEnum), nullable=False)
    cnss_number = Column(String(11), nullable=True)  # Format 8 chiffres - 2 chiffres (total 11 caractères)
    created_at = Column(Date, nullable=False, default=func.now())

    __table_args__ = (
        CheckConstraint(
            "(contract_type IN ('CDI', 'CDD') AND cnss_number ~ '^[0-9]{8}-[0-9]{2}$') OR (contract_type NOT IN ('CDI', 'CDD'))",
            name="cnss_required_for_cdi_cdd"
        ),
    )

