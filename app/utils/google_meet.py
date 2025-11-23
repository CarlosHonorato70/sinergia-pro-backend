import os
import json
from google.oauth2 import service_account
from google.auth.transport.requests import Request
from googleapiclient.discovery import build
from datetime import datetime, timedelta

# Carregar credenciais
CREDENTIALS_PATH = os.path.join(os.path.dirname(__file__), '../../google-credentials.json')

def get_google_credentials():
    """Obter credenciais do Google"""
    credentials = service_account.Credentials.from_service_account_file(
        CREDENTIALS_PATH,
        scopes=['https://www.googleapis.com/auth/calendar']
    )
    return credentials

def create_google_meet_event(therapist_email: str, patient_email: str, appointment_datetime: str, title: str = "Teleatendimento"):
    """
    Criar um evento no Google Calendar com Google Meet integrado
    
    Args:
        therapist_email: Email do terapeuta
        patient_email: Email do paciente
        appointment_datetime: Data/hora do atendimento (formato: "2024-11-23T10:00:00")
        title: Título do evento
    
    Returns:
        dict com detalhes do evento e link do Google Meet
    """
    try:
        credentials = get_google_credentials()
        service = build('calendar', 'v3', credentials=credentials)
        
        # Converter string para datetime
        appointment_time = datetime.fromisoformat(appointment_datetime)
        end_time = appointment_time + timedelta(hours=1)  # 1 hora de duração
        
        event = {
            'summary': title,
            'description': f'Teleatendimento entre {therapist_email} e {patient_email}',
            'start': {
                'dateTime': appointment_time.isoformat(),
                'timeZone': 'America/Sao_Paulo'
            },
            'end': {
                'dateTime': end_time.isoformat(),
                'timeZone': 'America/Sao_Paulo'
            },
            'attendees': [
                {'email': therapist_email},
                {'email': patient_email}
            ],
            'conferenceData': {
                'createRequest': {
                    'requestId': f'sinergia-{datetime.now().timestamp()}',
                    'conferenceSolutionKey': {
                        'type': 'hangoutsMeet'
                    }
                }
            }
        }
        
        # Criar evento
        created_event = service.events().insert(
            calendarId='primary',
            body=event,
            conferenceDataVersion=1
        ).execute()
        
        return {
            'event_id': created_event.get('id'),
            'title': created_event.get('summary'),
            'start': created_event.get('start'),
            'end': created_event.get('end'),
            'meet_link': created_event.get('conferenceData', {}).get('entryPoints', [{}])[0].get('uri'),
            'hangout_link': created_event.get('hangoutLink')
        }
    
    except Exception as e:
        print(f"Erro ao criar evento do Google Meet: {str(e)}")
        raise

def get_google_meet_link(event_id: str):
    """
    Obter o link do Google Meet de um evento existente
    
    Args:
        event_id: ID do evento no Google Calendar
    
    Returns:
        Link do Google Meet
    """
    try:
        credentials = get_google_credentials()
        service = build('calendar', 'v3', credentials=credentials)
        
        event = service.events().get(
            calendarId='primary',
            eventId=event_id
        ).execute()
        
        return event.get('hangoutLink')
    
    except Exception as e:
        print(f"Erro ao obter link do Google Meet: {str(e)}")
        raise

def delete_google_meet_event(event_id: str):
    """
    Deletar um evento do Google Calendar
    
    Args:
        event_id: ID do evento no Google Calendar
    """
    try:
        credentials = get_google_credentials()
        service = build('calendar', 'v3', credentials=credentials)
        
        service.events().delete(
            calendarId='primary',
            eventId=event_id
        ).execute()
        
        return {"message": "Evento deletado com sucesso"}
    
    except Exception as e:
        print(f"Erro ao deletar evento do Google Meet: {str(e)}")
        raise
