from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from pydantic import BaseModel, EmailStr
from app.database.connection import get_db
from app.models.user import User
from app.utils.auth import hash_password, get_current_user
import secrets
import string

router = APIRouter(prefix="/api/admin", tags=["admin"])

# ====== SCHEMAS ======
class ProfessionalCreate(BaseModel):
    email: EmailStr
    name: str
    specialization: str  # "Psicólogo", "Médico", "Psiquiatra"
    crm_or_crp: str

class ProfessionalResponse(BaseModel):
    id: int
    email: str
    name: str
    role: str
    specialization: str
    crm_or_crp: str

# ====== FUNÇÃO PARA VERIFICAR ADMIN ======
def check_admin(current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    if current_user.role != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Acesso restrito a administradores"
        )
    return current_user

# ====== FUNÇÃO GERAR SENHA TEMPORÁRIA ======
def generate_temp_password(length=12):
    characters = string.ascii_letters + string.digits + "!@#$%"
    return ''.join(secrets.choice(characters) for _ in range(length))

# ====== ENDPOINTS ======

@router.post("/profissionais", response_model=dict)
def create_professional(
    prof_data: ProfessionalCreate,
    admin: User = Depends(check_admin),
    db: Session = Depends(get_db)
):
    """Criar um novo profissional (Psicólogo/Médico)"""
    
    # Verificar se email já existe
    existing_user = db.query(User).filter(User.email == prof_data.email).first()
    if existing_user:
        raise HTTPException(status_code=400, detail="Email já registrado")
    
    # Gerar senha temporária
    temp_password = generate_temp_password()
    
    # Criar novo usuário
    new_user = User(
        email=prof_data.email,
        password=hash_password(temp_password),
        name=prof_data.name,
        role="therapist",
        specialization=prof_data.specialization,
        crm_or_crp=prof_data.crm_or_crp
    )
    
    db.add(new_user)
    db.commit()
    db.refresh(new_user)
    
    return {
        "message": "Profissional criado com sucesso",
        "id": new_user.id,
        "email": prof_data.email,
        "name": prof_data.name,
        "temporary_password": temp_password,
        "note": "O profissional deve trocar a senha no primeiro login"
    }

@router.get("/profissionais")
def list_professionals(
    admin: User = Depends(check_admin),
    db: Session = Depends(get_db)
):
    """Listar todos os profissionais"""
    professionals = db.query(User).filter(User.role == "therapist").all()
    return professionals

@router.get("/profissionais/{professional_id}")
def get_professional(
    professional_id: int,
    admin: User = Depends(check_admin),
    db: Session = Depends(get_db)
):
    """Obter detalhes de um profissional"""
    user = db.query(User).filter(User.id == professional_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="Profissional não encontrado")
    return user

@router.delete("/profissionais/{professional_id}")
def delete_professional(
    professional_id: int,
    admin: User = Depends(check_admin),
    db: Session = Depends(get_db)
):
    """Deletar um profissional"""
    user = db.query(User).filter(User.id == professional_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="Profissional não encontrado")
    
    if user.role != "therapist":
        raise HTTPException(status_code=400, detail="Usuário não é um profissional")
    
    db.delete(user)
    db.commit()
    
    return {"message": "Profissional deletado com sucesso"}

@router.get("/pacientes")
def list_patients(
    admin: User = Depends(check_admin),
    db: Session = Depends(get_db)
):
    """Listar todos os pacientes"""
    patients = db.query(User).filter(User.role == "patient").all()
    return patients

@router.delete("/pacientes/{patient_id}")
def delete_patient(
    patient_id: int,
    admin: User = Depends(check_admin),
    db: Session = Depends(get_db)
):
    """Deletar um paciente"""
    user = db.query(User).filter(User.id == patient_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="Paciente não encontrado")
    
    if user.role != "patient":
        raise HTTPException(status_code=400, detail="Usuário não é um paciente")
    
    db.delete(user)
    db.commit()
    
    return {"message": "Paciente deletado com sucesso"}

@router.get("/estatisticas")
def get_statistics(
    admin: User = Depends(check_admin),
    db: Session = Depends(get_db)
):
    """Obter estatísticas do sistema"""
    total_users = db.query(User).count()
    total_therapists = db.query(User).filter(User.role == "therapist").count()
    total_patients = db.query(User).filter(User.role == "patient").count()
    total_admins = db.query(User).filter(User.role == "admin").count()
    
    return {
        "total_users": total_users,
        "total_therapists": total_therapists,
        "total_patients": total_patients,
        "total_admins": total_admins
    }
