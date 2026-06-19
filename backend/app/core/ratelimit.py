"""Rate limiting in-memory — padrão instância única (Mixeng: SNIP - Rate Limiting).

Sliding window simples: conta hits por chave dentro de uma janela de tempo.
Para múltiplas instâncias (produção horizontal), trocar por Redis/Upstash.
"""

import time
from collections import defaultdict, deque
from threading import Lock

_lock = Lock()
# chave → deque de timestamps (epoch float)
_hits: dict[str, deque] = defaultdict(deque)


def is_allowed(key: str, limit: int = 5, window_seconds: int = 60) -> bool:
    """Retorna True se a requisição pode prosseguir, False se o limite foi atingido."""
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
