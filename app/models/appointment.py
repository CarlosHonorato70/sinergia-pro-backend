from sqlalchemy import Column, Integer, String, DateTime, ForeignKey
from datetime import datetime
from app.database.connection import Base

class Appointment(Base):
    __tablename__ = "appointments"

    id = Column(Integer, primary_key=True, index=True)
    therapist_id = Column(Integer, ForeignKey("users.id"))
    patient_id = Column(Integer, ForeignKey("users.id"))
    date = Column(DateTime)
    status = Column(String, default="agendada")
    notes = Column(String, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
