"""Normaliza URLs de conexão para o driver asyncpg (Neon-friendly).

O asyncpg NÃO entende parâmetros no estilo libpq (`sslmode`, `channel_binding`)
que o Neon coloca na connection string — eles precisam virar `connect_args`.
Além disso, o endpoint com PgBouncer do Neon (host com sufixo `-pooler`) opera
em modo *transaction*, que não suporta prepared statements nomeados; nesse caso
desligamos o cache de prepared statements do asyncpg.

Uso:
    url, connect_args = prepare_asyncpg(settings.database_url)
    engine = create_async_engine(url, connect_args=connect_args, ...)
"""

from __future__ import annotations

from typing import Any

from sqlalchemy.engine import URL, make_url

# Parâmetros que só o libpq entende; o asyncpg quebra se recebê-los na URL.
_LIBPQ_ONLY = ("sslmode", "channel_binding", "options")


def prepare_asyncpg(url: str | URL) -> tuple[URL, dict[str, Any]]:
    """Retorna (URL limpa, connect_args) prontos para create_async_engine."""
    u = make_url(url)
    connect_args: dict[str, Any] = {}

    # SSL: o Neon exige TLS. Traduzimos sslmode -> kwarg `ssl` do asyncpg.
    # Os certificados do Neon são válidos publicamente, então a verificação
    # padrão (ssl=True) passa sem precisar de CA custom.
    if any(key in u.query for key in ("sslmode", "channel_binding")):
        connect_args["ssl"] = True

    # Remove sempre os parâmetros libpq-only (mesmo que não haja SSL declarado).
    if any(key in u.query for key in _LIBPQ_ONLY):
        u = u.difference_update_query(_LIBPQ_ONLY)

    # PgBouncer (endpoint -pooler) não suporta prepared statements nomeados.
    if "-pooler" in (u.host or ""):
        connect_args["statement_cache_size"] = 0

    return u, connect_args
