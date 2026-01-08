from sqlalchemy import Column, Integer, String, DateTime
from datetime import datetime
from app.db.base import Base

class RequestHistory(Base):
    __tablename__ = "request_history"

    id = Column(Integer, primary_key=True)
    question = Column(String, nullable=False)
    character = Column(String, nullable=False)
    answer = Column(String, nullable=True)
    latency_ms = Column(Integer, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)
