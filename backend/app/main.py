import logging

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from app.core.config import settings
from app.modules.ai_agent.router import router as ai_agent_router
from app.modules.auth.router import router as auth_router
from app.modules.billing.router import router as billing_router
from app.modules.clinics.router import router as clinics_router
from app.modules.conversations.router import router as conversations_router
from app.modules.patients.router import router as patients_router
from app.modules.scheduling.router import router as scheduling_router
from app.modules.users.router import router as users_router
from app.modules.whatsapp.router import router as whatsapp_router

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(name)s — %(message)s",
)

_is_prod = settings.environment == "production"

app = FastAPI(
    title=settings.app_name,
    # Em produção, esconde docs e schema (Mixeng: A05 — Security Misconfiguration)
    docs_url=None if _is_prod else "/docs",
    redoc_url=None if _is_prod else "/redoc",
    openapi_url=None if _is_prod else "/openapi.json",
)

# ── CORS restrito aos origens configurados (Mixeng: checklist rede) ───────────
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ── Security headers em todas as respostas (Mixeng: SNIP - Security Headers) ──
@app.middleware("http")
async def security_headers(request: Request, call_next):
    response = await call_next(request)
    response.headers["X-Content-Type-Options"] = "nosniff"
    response.headers["X-Frame-Options"] = "DENY"
    response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
    response.headers["Permissions-Policy"] = "camera=(), microphone=(), geolocation=()"
    # HSTS só em produção com HTTPS estável
    if _is_prod:
        response.headers["Strict-Transport-Security"] = "max-age=63072000; includeSubDomains"
    return response


# ── Suprime stack trace em produção (Mixeng: A05 / "falhe de forma segura") ───
@app.exception_handler(Exception)
async def generic_error_handler(request: Request, exc: Exception):
    if _is_prod:
        logging.getLogger("app").error("Unhandled error: %s", type(exc).__name__)
        return JSONResponse(
            status_code=500,
            content={"detail": "Erro interno. Nossa equipe foi notificada."},
        )
    raise exc


@app.get("/health", tags=["health"])
async def health():
    return {"status": "ok", "app": settings.app_name, "env": settings.environment}


app.include_router(auth_router)
app.include_router(clinics_router)
app.include_router(users_router)
app.include_router(patients_router)
app.include_router(scheduling_router)
app.include_router(billing_router)
app.include_router(ai_agent_router)
app.include_router(whatsapp_router)
app.include_router(conversations_router)
