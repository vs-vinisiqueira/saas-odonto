#!/usr/bin/env python3
"""Teste de carga/corrida do agendamento.

Dispara N pedidos CONCORRENTES de agendamento para o MESMO horário e dentista e
verifica que exatamente 1 vence (201) e todos os outros são recusados (409). Isso
valida, sob concorrência real, a dupla proteção anti-overlap:
  - fast-path `find_conflict` (aplicação), e
  - a constraint EXCLUDE gist do Postgres (migration 0012) — o backstop.
De quebra, estressa o pool de conexões (migration/PR de pool) e mede latência.

IMPORTANTE:
  - Rode contra um ambiente de TESTE/STAGING, nunca direto na produção com dados
    reais — ele CRIA um agendamento (o vencedor). Use um paciente/dentista de teste.
  - Passe `--dentist-id`: sem dentista, a constraint EXCLUDE NÃO se aplica (linhas
    com dentist_id NULL não entram no EXCLUDE) e o teste não exercita o backstop.

Requisitos: Python 3.11+, httpx (já é dependência do backend).

Exemplo (o httpx vive no ambiente uv do backend/, então rode de dentro de backend/):
    cd backend && uv run python ../scripts/loadtest/booking_race.py \
        --base-url https://SEU-BACKEND.up.railway.app \
        --email admin@clinica.com --password '***' \
        --patient-id <uuid> --dentist-id <uuid> --count 50
"""
from __future__ import annotations

import argparse
import asyncio
import datetime as dt
import sys

try:
    import httpx
except ImportError:  # pragma: no cover
    sys.exit(
        "httpx não instalado. Rode de dentro de backend/: "
        "`cd backend && uv run python ../scripts/loadtest/booking_race.py ...`"
    )


def _parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser(description="Teste de corrida de agendamento (slot unico -> 409).")
    p.add_argument("--base-url", required=True, help="URL base da API (ex.: https://api.exemplo.com)")
    p.add_argument("--email", required=True, help="E-mail para login")
    p.add_argument("--password", required=True, help="Senha para login")
    p.add_argument("--patient-id", required=True, help="UUID de um paciente de teste")
    p.add_argument("--dentist-id", default=None, help="UUID do dentista (RECOMENDADO — sem ele o EXCLUDE não é testado)")
    p.add_argument("--slot", default=None, help="Início do horário em ISO 8601 (default: amanhã 14:00 UTC)")
    p.add_argument("--duration", type=int, default=30, help="Duração em minutos (default: 30)")
    p.add_argument("--tipo", default="avaliacao", help="Tipo da consulta (default: avaliacao)")
    p.add_argument("--count", type=int, default=50, help="Nº de pedidos concorrentes (default: 50)")
    p.add_argument("--timeout", type=float, default=30.0, help="Timeout HTTP por request (s)")
    return p.parse_args()


async def _login(client: httpx.AsyncClient, email: str, password: str) -> str:
    r = await client.post("/auth/login", json={"email": email, "password": password})
    r.raise_for_status()
    token = r.json().get("access_token")
    if not token:
        sys.exit("Login não retornou access_token.")
    return token


async def _book(client: httpx.AsyncClient, payload: dict) -> tuple[int, float]:
    t0 = asyncio.get_event_loop().time()
    r = await client.post("/scheduling/appointments", json=payload)
    return r.status_code, (asyncio.get_event_loop().time() - t0)


async def main(args: argparse.Namespace) -> int:
    if args.slot:
        starts_at = dt.datetime.fromisoformat(args.slot)
        if starts_at.tzinfo is None:
            starts_at = starts_at.replace(tzinfo=dt.timezone.utc)
    else:
        tomorrow = dt.datetime.now(dt.timezone.utc) + dt.timedelta(days=1)
        starts_at = tomorrow.replace(hour=14, minute=0, second=0, microsecond=0)

    payload = {
        "patient_id": args.patient_id,
        "starts_at": starts_at.isoformat(),
        "duration_min": args.duration,
        "tipo": args.tipo,
    }
    if args.dentist_id:
        payload["dentist_id"] = args.dentist_id
    else:
        print("AVISO: sem --dentist-id, a constraint EXCLUDE NÃO é exercitada.\n")

    async with httpx.AsyncClient(base_url=args.base_url.rstrip("/"), timeout=args.timeout) as client:
        token = await _login(client, args.email, args.password)
        client.headers["Authorization"] = f"Bearer {token}"

        print(f">> Disparando {args.count} agendamentos concorrentes para {starts_at.isoformat()} "
              f"(dentist={args.dentist_id or 'NULL'})...")
        results = await asyncio.gather(*[_book(client, payload) for _ in range(args.count)])

    codes = [c for c, _ in results]
    lats = sorted(l for _, l in results)
    created = codes.count(201)
    conflicts = codes.count(409)
    others = [c for c in codes if c not in (201, 409)]

    def pct(p: float) -> float:
        if not lats:
            return 0.0
        idx = min(len(lats) - 1, int(round(p / 100 * (len(lats) - 1))))
        return lats[idx] * 1000  # ms

    print("\n── Resultado ─────────────────────────────────────────────")
    print(f"  201 Created : {created}")
    print(f"  409 Conflict: {conflicts}")
    if others:
        print(f"  OUTROS      : {others}")
    print(f"  Latência ms : p50={pct(50):.0f}  p95={pct(95):.0f}  p99={pct(99):.0f}  max={max(lats)*1000:.0f}")
    print("──────────────────────────────────────────────────────────")

    # Sucesso: exatamente 1 criado, resto 409, nenhum erro inesperado.
    ok = created == 1 and conflicts == args.count - 1 and not others
    if ok:
        print("PASS ✅  Exatamente 1 agendamento venceu; os demais receberam 409.")
        return 0
    print("FAIL ❌  Esperado 1×201 e o restante 409. Investigue overlap/erros acima.")
    if args.dentist_id and created > 1:
        print("        >1 criado COM dentista → a constraint EXCLUDE pode não estar aplicada "
              "(confira a migration 0012 no ambiente).")
    return 1


if __name__ == "__main__":
    # Windows: força UTF-8 na saída para não estourar com box-drawing/emoji no cp1252.
    for _stream in (sys.stdout, sys.stderr):
        try:
            _stream.reconfigure(encoding="utf-8")
        except Exception:
            pass
    raise SystemExit(asyncio.run(main(_parse_args())))
