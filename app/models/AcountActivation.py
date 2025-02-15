
from sqlalchemy import Column, Integer, String, Date, Enum , ForeignKey

from sqlalchemy.orm import relationship



from ..core.database import Base
from ..enums.TokenStatusEnum import TokenStatusEnum


class Acount_Activation(Base):
    __tablename__ = "Acount_Activation"

    id = Column(Integer, primary_key=True, index=True)
    Employee_id = Column(Integer, ForeignKey("employee.id"), nullable=False) 
    Employee = relationship("Employee", foreign_keys=[Employee_id], lazy="joined")
    Email = Column(String(100), nullable=False)
    token = Column(String(100), nullable=False)
    expired_date = Column(Date, nullable=False)
    token_status_id = Column(Enum(TokenStatusEnum), nullable=False)    

