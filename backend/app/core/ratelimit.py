"""Rate limiting — Redis compartilhado entre instâncias quando REDIS_URL está
definida; fallback in-memory (por processo) caso contrário OU se o Redis
estiver temporariamente inacessível (Mixeng: SNIP - Rate Limiting).

Sliding window log: cada hit é um membro num ZSET (Redis) ou um timestamp numa
deque (memória), com poda dos itens fora da janela a cada chamada.

Degradação: sem REDIS_URL, o comportamento é IDÊNTICO ao anterior (100%
in-memory) — usado em dev/CI/single-instance. Com REDIS_URL definida mas o
Redis fora do ar, cada chamada tenta o Redis, falha rápido (timeout curto) e
cai no in-memory para aquela chamada — nunca libera geral (fail-open) nem
bloqueia geral (fail-closed).
"""

import logging
import time
import uuid
from collections import defaultdict, deque
from threading import Lock

from app.core.config import settings

_log = logging.getLogger("ratelimit")

_lock = Lock()
# chave → deque de timestamps (epoch float) — fallback in-memory, por processo.
_hits: dict[str, deque] = defaultdict(deque)


def _is_allowed_memory(key: str, limit: int, window_seconds: int) -> bool:
    """Implementação original in-memory — usada sempre sem REDIS_URL, e como
    fallback quando o Redis está inacessível."""
    now = time.monotonic()
    cutoff = now - window_seconds
    with _lock:
        dq = _hits[key]
        while dq and dq[0] < cutoff:
            dq.popleft()
        if len(dq) >= limit:
            return False
        dq.append(now)
        return True


# ── Backend Redis (opcional) ──────────────────────────────────────────────

# Replica o sliding-window-log do in-memory numa única viagem atômica (Lua
# roda single-threaded no servidor Redis — fecha a race que existiria se
# ZCARD + decisão + ZADD fossem 3 comandos separados, onde dois requests
# concorrentes na mesma chave poderiam ambos passar pela checagem).
# KEYS[1] = chave do ZSET; ARGV[1] = cutoff (epoch ms); ARGV[2] = limit;
# ARGV[3] = now (epoch ms, score do novo membro); ARGV[4] = membro único;
# ARGV[5] = TTL do ZSET em segundos (janela + folga, evita vazar memória no Redis).
_SLIDING_WINDOW_LUA = """
redis.call('ZREMRANGEBYSCORE', KEYS[1], '-inf', ARGV[1])
local count = redis.call('ZCARD', KEYS[1])
if count >= tonumber(ARGV[2]) then
    return 0
end
redis.call('ZADD', KEYS[1], ARGV[3], ARGV[4])
redis.call('EXPIRE', KEYS[1], ARGV[5])
return 1
"""

_redis_client = None
_redis_script = None


def _get_redis():
    """Cria o client (e registra o script) na primeira chamada, nunca no
    import do módulo — assim, sem REDIS_URL, nenhuma tentativa de
    conexão/DNS acontece, nem durante a coleta de testes."""
    global _redis_client, _redis_script
    if _redis_client is None:
        import redis.asyncio as redis  # import tardio: só ocorre se REDIS_URL existir

        # Timeout curto: o Redis do Railway fica na mesma rede privada (baixa
        # latência no caminho feliz); um timeout de 1s deixaria cada request
        # pagando ~1s extra por tentativa durante uma indisponibilidade, já que
        # o pool não reaproveita uma conexão que falhou.
        _redis_client = redis.from_url(
            settings.redis_url,
            socket_connect_timeout=0.3,
            socket_timeout=0.3,
        )
        _redis_script = _redis_client.register_script(_SLIDING_WINDOW_LUA)
    return _redis_client, _redis_script


async def _is_allowed_redis(key: str, limit: int, window_seconds: int) -> bool:
    _client, script = _get_redis()
    now_ms = time.time() * 1000
    cutoff_ms = now_ms - (window_seconds * 1000)
    # Membro único por chamada: um ZSET é keyed-by-member, então dois hits com
    # o mesmo membro se sobrescreveriam em vez de contar como dois.
    member = f"{now_ms}:{uuid.uuid4().hex}"
    ttl = window_seconds + 5
    result = await script(
        keys=[f"ratelimit:{key}"],
        args=[cutoff_ms, limit, now_ms, member, ttl],
    )
    return bool(result)


async def _dispose_redis() -> None:
    """Fecha a conexão Redis, se existir. Usado pelos testes para evitar
    conexões presas a um event loop finalizado (mesmo cuidado do engine
    SQLAlchemy — ver `_dispose_app_engine` em conftest.py)."""
    global _redis_client, _redis_script
    if _redis_client is not None:
        await _redis_client.aclose()
        _redis_client = None
        _redis_script = None


async def is_allowed(key: str, limit: int = 5, window_seconds: int = 60) -> bool:
    """Retorna True se a requisição pode prosseguir, False se o limite foi
    atingido. Usa Redis se REDIS_URL estiver definida; senão, in-memory. Se o
    Redis falhar (timeout, conexão recusada, etc.), cai no in-memory para
    ESTA chamada e loga um warning — nunca falha aberto nem fechado."""
    if not settings.redis_url:
        return _is_allowed_memory(key, limit, window_seconds)

    try:
        return await _is_allowed_redis(key, limit, window_seconds)
    except Exception as exc:
        _log.warning("ratelimit: Redis indisponível (%s), usando fallback in-memory", exc)
        return _is_allowed_memory(key, limit, window_seconds)
