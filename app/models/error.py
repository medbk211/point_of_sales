
from sqlalchemy import Column, Integer, String, Date
from sqlalchemy.sql import func


from ..core.database import Base


class Error(Base):
    __tablename__ = "error"

    id = Column(Integer, primary_key=True, index=True)
    error_message = Column(String(255), nullable=False)
    created_at = Column(Date, nullable=False, server_default=func.now())
