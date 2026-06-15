from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.core.config import settings
from app.modules.ai_agent.router import router as ai_agent_router
from app.modules.auth.router import router as auth_router
from app.modules.billing.router import router as billing_router
from app.modules.clinics.router import router as clinics_router
from app.modules.patients.router import router as patients_router
from app.modules.scheduling.router import router as scheduling_router
from app.modules.whatsapp.router import router as whatsapp_router

app = FastAPI(title=settings.app_name)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],  # painel React (Vite) em dev
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/health", tags=["health"])
async def health():
    return {"status": "ok", "app": settings.app_name, "env": settings.environment}


app.include_router(auth_router)
app.include_router(clinics_router)
app.include_router(patients_router)
app.include_router(scheduling_router)
app.include_router(billing_router)
app.include_router(ai_agent_router)
app.include_router(whatsapp_router)
