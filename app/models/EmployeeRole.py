import sys
import os
from sqlalchemy import Column, Integer, String, Date, Enum , ForeignKey
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship

# Ajouter le chemin du dossier parent pour résoudre les imports


from ..database import Base
from ..enums import RoleEnum

class Employee_role(Base):
    __tablename__ = "employee_role"

    id = Column(Integer, primary_key=True, index=True)
    Employee_id = Column(Integer , ForeignKey("employee.id") , nullable=False)
    Employee = relationship("Employee", foreign_keys=[Employee_id], lazy="joined") 
    role = Column(Enum(RoleEnum), nullable=False)