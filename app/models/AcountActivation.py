
from sqlalchemy import Column, Integer, String, Date, Enum , ForeignKey
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship

# Ajouter le chemin du dossier parent pour résoudre les imports


from ..database import Base
from ..enums.TokenStatusEnum import TokenStatusEnum


class Acount_Activation(Base):
    __tablename__ = "Acount_Activation"

    id = Column(Integer, primary_key=True, index=True)
    Employee_id = Column(Integer, ForeignKey("employee.id"), nullable=False)  # Changed 'Employee.id' to 'employee.id'
    Employee = relationship("Employee", foreign_keys=[Employee_id], lazy="joined")
    Email = Column(String(100), nullable=False)
    token = Column(String(100), nullable=True)
    expired_date = Column(Date, nullable=True)
    token_status_id = Column(Enum(TokenStatusEnum), nullable=False)    

