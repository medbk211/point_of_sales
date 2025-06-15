# models.py

from sqlalchemy import Column, Integer, String, ForeignKey, DateTime
from datetime import datetime
from ..core.database import Base

class EmailChangeToken(Base):
    __tablename__ = "email_change_tokens"

    id = Column(Integer, primary_key=True, index=True)
    Employee_id = Column(Integer , ForeignKey("employee.id") , nullable=False)
    new_email = Column(String, nullable=False)
    token = Column(String, unique=True, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)
