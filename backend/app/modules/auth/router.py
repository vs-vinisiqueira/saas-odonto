from fastapi import APIRouter, Depends, Request, status
from fastapi.responses import JSONResponse
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_session
from app.core.ratelimit import is_allowed
from app.core.security_log import login_failed, login_ok, login_rate_limited
from app.modules.auth import service
from app.modules.auth.schemas import LoginRequest, RefreshRequest, TokenResponse

router = APIRouter(prefix="/auth", tags=["auth"])

# 5 tentativas por minuto por IP (Mixeng: SNIP - Rate Limiting)
_LOGIN_LIMIT = 5
_LOGIN_WINDOW = 60


def _client_ip(request: Request) -> str:
    forwarded = request.headers.get("x-forwarded-for")
    return forwarded.split(",")[0].strip() if forwarded else (request.client.host or "unknown")


@router.post("/login", response_model=TokenResponse)
async def login(
    request: Request,
    body: LoginRequest,
    session: AsyncSession = Depends(get_session),
):
    ip = _client_ip(request)
    if not is_allowed(f"login:{ip}", limit=_LOGIN_LIMIT, window_seconds=_LOGIN_WINDOW):
        login_rate_limited(ip)
        return JSONResponse(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            content={"detail": "Muitas tentativas. Tente novamente em 1 minuto."},
            headers={"Retry-After": str(_LOGIN_WINDOW)},
        )
    try:
        tokens = await service.authenticate(session, body.email, body.password)
        login_ok(str(tokens.get("access_token", "")[:8]))  # só prefixo, nunca token completo
        return tokens
    except Exception:
        login_failed(ip)
        raise


@router.post("/refresh", response_model=TokenResponse)
async def refresh(request: Request, body: RefreshRequest):
    ip = _client_ip(request)
    if not is_allowed(f"refresh:{ip}", limit=10, window_seconds=60):
        login_rate_limited(ip)
        return JSONResponse(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            content={"detail": "Muitas tentativas. Tente novamente em 1 minuto."},
            headers={"Retry-After": "60"},
        )
    return await service.refresh_tokens(body.refresh_token)
