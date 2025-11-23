from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.database.connection import engine, Base
from app.models.user import User
from app.models.appointment import Appointment
from app.routes.auth import router as auth_router
from app.routes.appointments import router as appointments_router
from app.routes.admin import router as admin_router
from app.routes.google_meet import router as google_meet_router

# Criar tabelas
Base.metadata.create_all(bind=engine)

app = FastAPI(title="API do Sinergia Pro", version="1.0.0")

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Routers
app.include_router(auth_router)
app.include_router(appointments_router)
app.include_router(admin_router)
app.include_router(google_meet_router)

@app.get("/")
def read_root():
    return {
        "message": "API do Sinergia Pro",
        "version": "1.0.0",
        "docs": "/docs",
        "redoc": "/redoc"
    }
