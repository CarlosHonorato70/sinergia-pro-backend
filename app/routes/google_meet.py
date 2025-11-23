from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from pydantic import BaseModel
from app.database.connection import get_db
from app.models.appointment import Appointment
from app.models.user import User
from app.utils.auth import get_current_user
from app.utils.google_meet import create_google_meet_event, get_google_meet_link, delete_google_meet_event
from datetime import datetime

router = APIRouter(prefix="/api/google-meet", tags=["google-meet"])

class CreateMeetRequest(BaseModel):
    appointment_id: int
    title: str = "Teleatendimento Sinergia Pro"

class MeetResponse(BaseModel):
    event_id: str
    title: str
    meet_link: str
    hangout_link: str

@router.post("/create", response_model=dict)
def create_meet(
    request: CreateMeetRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Criar Google Meet para um atendimento"""
    
    # Buscar agendamento
    appointment = db.query(Appointment).filter(
        Appointment.id == request.appointment_id
    ).first()
    
    if not appointment:
        raise HTTPException(status_code=404, detail="Atendimento não encontrado")
    
    # Verificar permissões (apenas terapeuta ou admin)
    if current_user.role == "therapist" and appointment.therapist_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Sem permissão para criar meet neste atendimento"
        )
    
    # Buscar dados do terapeuta e paciente
    therapist = db.query(User).filter(User.id == appointment.therapist_id).first()
    patient = db.query(User).filter(User.id == appointment.patient_id).first()
    
    if not therapist or not patient:
        raise HTTPException(status_code=404, detail="Terapeuta ou paciente não encontrado")
    
    try:
        # Criar evento no Google Calendar com Meet
        meet_event = create_google_meet_event(
            therapist_email=therapist.email,
            patient_email=patient.email,
            appointment_datetime=appointment.date.isoformat(),
            title=request.title
        )
        
        # Atualizar agendamento com o ID do evento
        appointment.google_meet_event_id = meet_event['event_id']
        appointment.google_meet_link = meet_event.get('hangout_link') or meet_event.get('meet_link')
        db.commit()
        
        return {
            "message": "Google Meet criado com sucesso",
            "event_id": meet_event['event_id'],
            "title": meet_event['title'],
            "meet_link": meet_event.get('hangout_link') or meet_event.get('meet_link'),
            "start": meet_event['start'],
            "end": meet_event['end']
        }
    
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Erro ao criar Google Meet: {str(e)}"
        )

@router.get("/link/{appointment_id}")
def get_meet_link(
    appointment_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Obter link do Google Meet de um atendimento"""
    
    appointment = db.query(Appointment).filter(
        Appointment.id == appointment_id
    ).first()
    
    if not appointment:
        raise HTTPException(status_code=404, detail="Atendimento não encontrado")
    
    # Verificar permissões
    if current_user.role == "therapist" and appointment.therapist_id != current_user.id:
        if current_user.role == "patient" and appointment.patient_id != current_user.id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Sem permissão para acessar este atendimento"
            )
    
    if not appointment.google_meet_link:
        raise HTTPException(status_code=404, detail="Google Meet não foi criado para este atendimento")
    
    return {
        "appointment_id": appointment.id,
        "meet_link": appointment.google_meet_link,
        "event_id": appointment.google_meet_event_id
    }

@router.delete("/delete/{appointment_id}")
def delete_meet(
    appointment_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Deletar Google Meet de um atendimento"""
    
    appointment = db.query(Appointment).filter(
        Appointment.id == appointment_id
    ).first()
    
    if not appointment:
        raise HTTPException(status_code=404, detail="Atendimento não encontrado")
    
    # Verificar permissões
    if current_user.role == "therapist" and appointment.therapist_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Sem permissão"
        )
    
    try:
        if appointment.google_meet_event_id:
            delete_google_meet_event(appointment.google_meet_event_id)
        
        appointment.google_meet_event_id = None
        appointment.google_meet_link = None
        db.commit()
        
        return {"message": "Google Meet deletado com sucesso"}
    
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Erro ao deletar Google Meet: {str(e)}"
        )
