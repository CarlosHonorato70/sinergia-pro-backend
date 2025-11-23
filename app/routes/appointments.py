from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from app.database.connection import get_db
from app.models.appointment import Appointment

router = APIRouter(prefix="/api/appointments", tags=["appointments"])

@router.get("/")
def list_appointments(db: Session = Depends(get_db)):
    return db.query(Appointment).all()

@router.post("/")
def create_appointment(therapist_id: int, patient_id: int, date: str, db: Session = Depends(get_db)):
    appointment = Appointment(
        therapist_id=therapist_id,
        patient_id=patient_id,
        date=date
    )
    db.add(appointment)
    db.commit()
    db.refresh(appointment)
    return appointment
