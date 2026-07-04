import logging
import uuid
from contextvars import ContextVar

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from sqlalchemy import text

from app.core.config import settings
from app.core.database import async_session_maker
from app.modules.ai_agent.router import router as ai_agent_router
from app.modules.auth.router import router as auth_router
from app.modules.billing.router import router as billing_router
from app.modules.clinics.router import router as clinics_router
from app.modules.conversations.router import router as conversations_router
from app.modules.integrations.router import router as integrations_router
from app.modules.patients.router import router as patients_router
from app.modules.scheduling.router import router as scheduling_router
from app.modules.users.router import router as users_router
from app.modules.whatsapp.router import router as whatsapp_router

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(name)s — %(message)s",
)

_is_prod = settings.environment == "production"

# B2: em produção, o ideal é uma CREDENTIALS_SECRET dedicada. Sem ela, os
# segredos de integração são cifrados com uma chave derivada do JWT_SECRET —
# rotacionar o JWT tornaria todos ilegíveis. Avisamos (sem quebrar o boot).
if _is_prod and settings.credentials_secret is None:
    logging.getLogger("app").warning(
        "CREDENTIALS_SECRET não definida em produção: segredos de integração "
        "usam a chave derivada do JWT_SECRET. Defina uma secret dedicada e fixa."
    )

# B4: id de correlação por request, incluído nos logs de erro e no header.
_request_id: ContextVar[str] = ContextVar("request_id", default="-")

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


# ── ID de correlação por request (B4: observabilidade) ───────────────────────
@app.middleware("http")
async def request_id_middleware(request: Request, call_next):
    rid = request.headers.get("X-Request-ID") or uuid.uuid4().hex[:12]
    _request_id.set(rid)
    response = await call_next(request)
    response.headers["X-Request-ID"] = rid
    return response


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
        logging.getLogger("app").error(
            "Unhandled error [%s]: %s", _request_id.get(), type(exc).__name__
        )
        return JSONResponse(
            status_code=500,
            content={"detail": "Erro interno. Nossa equipe foi notificada."},
        )
    raise exc


@app.get("/health", tags=["health"])
async def health():
    # M6: health check real — confirma que o banco responde (não só 200 fixo).
    # Um SELECT 1 também "acorda" o Neon (scale-to-zero) sem falhar.
    db_ok = True
    try:
        async with async_session_maker() as s:
            await s.execute(text("SELECT 1"))
    except Exception:
        db_ok = False
        logging.getLogger("app").error("Health check: banco indisponível")
    body = {
        "status": "ok" if db_ok else "degraded",
        "app": settings.app_name,
        "env": settings.environment,
        "db": db_ok,
    }
    return JSONResponse(status_code=200 if db_ok else 503, content=body)


app.include_router(auth_router)
app.include_router(clinics_router)
app.include_router(users_router)
app.include_router(integrations_router)
app.include_router(patients_router)
app.include_router(scheduling_router)
app.include_router(billing_router)
app.include_router(whatsapp_router)
app.include_router(conversations_router)

# O webhook mock (/ai/webhook) confia no `tenant_id` vindo do corpo, SEM auth —
# escrita cross-tenant e abuso do WhatsApp/Gemini reais da clínica. Só faz sentido
# em dev/CI. Em produção, o único ponto de entrada do agente é /ai/whatsapp/webhook,
# que resolve o tenant pelo banco (não pelo cliente).
if not _is_prod:
    app.include_router(ai_agent_router)
