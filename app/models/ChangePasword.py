
from sqlalchemy import Column, Integer, String, Date, Enum , ForeignKey
from sqlalchemy.orm import relationship

# Ajouter le chemin du dossier parent pour résoudre les imports


from ..core.database import Base
from ..enums import TokenStatusEnum

class ChangePasword(Base):
    __tablename__ = "change_password"

    id = Column(Integer, primary_key=True, index=True)
    Employee_id = Column(Integer , ForeignKey("employee.id") , nullable=False)
    expired_date = Column(Date, nullable=True)
    token = Column(String(100), nullable=False)
    token_status_id = Column(Enum(TokenStatusEnum), nullable=False)
    Employee = relationship("Employee", foreign_keys=[Employee_id], lazy="joined")