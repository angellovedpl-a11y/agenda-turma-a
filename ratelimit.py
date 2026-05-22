"""Rate limiting por matricula via Postgres (kvstore _connect()).

Design:
- Storage compartilhado entre os 2 workers gunicorn (limite preciso, sem 2x).
- Janela fixa de 1 minuto (bucket_min = epoch_seconds // 60).
- Tabela propria `ratelimit_buckets` com PK composta — `INSERT ... ON CONFLICT
  DO UPDATE ... RETURNING count` faz check+increment atomico em 1 round-trip.
- FAIL-OPEN: qualquer erro do banco retorna (allowed=True). Rate limiter NUNCA
  pode derrubar o app — antipadrao classico. Loga warning, deixa passar.
- Cleanup probabilistico (1/N requests) remove buckets > N minutos atras —
  evita crescer infinito sem precisar de cron.
- Desligavel via `RATELIMIT_ENABLED=0` (kill switch operacional).
"""
import os
import time
import threading
from functools import wraps

from flask import request, jsonify

import kvstore

_RL_ENABLED = os.environ.get('RATELIMIT_ENABLED', '1') == '1'

_RL_TABLE_INIT = False
_RL_TABLE_INIT_LOCK = threading.Lock()


def init_schema():
    """Cria a tabela `ratelimit_buckets` se nao existir. Idempotente.
    Chamar uma vez no startup (depois de kvstore.init_schema)."""
    global _RL_TABLE_INIT
    if not _RL_ENABLED:
        print('[ratelimit] desativado via RATELIMIT_ENABLED=0')
        return
    with _RL_TABLE_INIT_LOCK:
        if _RL_TABLE_INIT:
            return
        try:
            with kvstore._connect() as conn, conn.cursor() as cur:
                cur.execute("""
                    CREATE TABLE IF NOT EXISTS ratelimit_buckets (
                        matricula TEXT NOT NULL,
                        rota TEXT NOT NULL,
                        bucket_min BIGINT NOT NULL,
                        count INT NOT NULL DEFAULT 1,
                        PRIMARY KEY (matricula, rota, bucket_min)
                    )
                """)
                cur.execute("""
                    CREATE INDEX IF NOT EXISTS ratelimit_buckets_bucket_idx
                    ON ratelimit_buckets (bucket_min)
                """)
            _RL_TABLE_INIT = True
            print('[ratelimit] schema OK (tabela ratelimit_buckets)')
        except Exception as e:
            print(f'[ratelimit] init_schema falhou (rate limit ficara fail-open): {e}')


def _parse_int_env(name: str, default: int, minimum: int = 1) -> int:
    """Parse int env var com fallback seguro + clamp `>= minimum`. Evita
    ValueError no import e ZeroDivisionError em modulos (`% _CLEANUP_EVERY`).
    Bug pego no code review da ETAPA 4."""
    raw = os.environ.get(name)
    if raw is None or not raw.strip():
        return default
    try:
        v = int(raw)
    except (ValueError, TypeError):
        print(f'[ratelimit] {name}={raw!r} invalido, usando default {default}')
        return default
    if v < minimum:
        print(f'[ratelimit] {name}={v} abaixo do minimo {minimum}, ajustado')
        return minimum
    return v


_cleanup_counter = 0
_cleanup_counter_lock = threading.Lock()
_CLEANUP_EVERY = _parse_int_env('RATELIMIT_CLEANUP_EVERY', 500, minimum=1)
_CLEANUP_KEEP_MIN = _parse_int_env('RATELIMIT_CLEANUP_KEEP_MIN', 10, minimum=1)

# Contador de fail-opens p/ alerta amostrado (loga a cada N pra nao floodar).
# Bug pego no code review: sem isso, "limiter inoperante" passa despercebido.
_failopen_counter = 0
_failopen_counter_lock = threading.Lock()
_FAILOPEN_LOG_EVERY = _parse_int_env('RATELIMIT_FAILOPEN_LOG_EVERY', 100, minimum=1)

# Metricas pra observabilidade (ETAPA 6) — incrementadas em check_and_increment.
# Process-local (cada worker tem o seu); o /api/admin/metrics agrega via getter.
_metrics = {'requests_total': 0, 'blocked_total': 0}
_metrics_lock = threading.Lock()


def _maybe_cleanup(now_bucket):
    """A cada CLEANUP_EVERY chamadas, remove buckets > CLEANUP_KEEP_MIN minutos.
    Probabilistico evita cron e mantem custo amortizado baixo."""
    global _cleanup_counter
    with _cleanup_counter_lock:
        _cleanup_counter += 1
        should = (_cleanup_counter % _CLEANUP_EVERY) == 0
    if not should:
        return
    try:
        threshold = now_bucket - _CLEANUP_KEEP_MIN
        with kvstore._connect() as conn, conn.cursor() as cur:
            cur.execute(
                'DELETE FROM ratelimit_buckets WHERE bucket_min < %s',
                (threshold,)
            )
            removidos = cur.rowcount
        if removidos > 0:
            print(f'[ratelimit] cleanup removeu {removidos} buckets antigos')
    except Exception as e:
        print(f'[ratelimit] cleanup falhou (nao-fatal): {e}')


def check_and_increment(matricula: str, rota: str, max_per_min: int) -> tuple:
    """Retorna (allowed: bool, count: int, retry_after_s: int).

    FAIL-OPEN garantido: qualquer exception (banco fora, schema ausente,
    pool esgotado) retorna (True, 0, 0). Rate limiter NUNCA derruba o app.
    """
    if not _RL_ENABLED or not matricula or max_per_min <= 0:
        return (True, 0, 0)
    with _metrics_lock:
        _metrics['requests_total'] += 1
    now = int(time.time())
    bucket_min = now // 60
    try:
        with kvstore._connect() as conn, conn.cursor() as cur:
            cur.execute(
                """
                INSERT INTO ratelimit_buckets (matricula, rota, bucket_min, count)
                VALUES (%s, %s, %s, 1)
                ON CONFLICT (matricula, rota, bucket_min)
                DO UPDATE SET count = ratelimit_buckets.count + 1
                RETURNING count
                """,
                (matricula, rota, bucket_min)
            )
            row = cur.fetchone()
            count = int(row[0]) if row else 1
        _maybe_cleanup(bucket_min)
        if count > max_per_min:
            retry_after = max(1, 60 - (now % 60))
            with _metrics_lock:
                _metrics['blocked_total'] += 1
            return (False, count, retry_after)
        return (True, count, 0)
    except Exception as e:
        global _failopen_counter
        with _failopen_counter_lock:
            _failopen_counter += 1
            n = _failopen_counter
        # Loga a 1a ocorrencia (alerta inicial) e depois amostrado pra nao floodar.
        if n == 1 or (n % _FAILOPEN_LOG_EVERY) == 0:
            print(f'[ratelimit] ALERTA fail-open #{n} ({matricula}/{rota}): {e}')
        return (True, 0, 0)


def _client_ip() -> str:
    """Resolve IP do cliente atras do proxy do Replit. X-Forwarded-For pode ter
    varios IPs (cliente, proxy1, proxy2) — o primeiro eh o cliente original."""
    xff = request.headers.get('X-Forwarded-For', '').strip()
    if xff:
        return xff.split(',')[0].strip() or 'unknown'
    return request.remote_addr or 'unknown'


def rate_limit_by_request(max_per_min: int, env_var: str = None, route_key: str = None,
                          body_key: str = None):
    """Rate limit para rotas SEM autenticacao (login, recuperar senha).
    Chave eh IP do cliente + opcionalmente um campo do body JSON (ex: 'matricula').

    Por que IP+matricula: bloqueia tanto brute-force de senha (mesmo IP, mesma
    matricula) quanto enumeracao (mesmo IP, varias matriculas) — cada combinacao
    tem seu proprio bucket. Sem isso, brute-force de 10k combinacoes de senha
    de 4 digitos cabe em segundos.

    FAIL-OPEN igual ao rate_limit original: se DB cai, deixa passar (limiter
    NUNCA pode derrubar o app).
    """
    def decorator(fn):
        limite = max_per_min
        if env_var:
            raw = os.environ.get(env_var)
            if raw is not None and raw.strip():
                try:
                    limite = int(raw)
                except (ValueError, TypeError):
                    print(f'[ratelimit] {env_var}={raw!r} invalido, usando default {max_per_min}')
                    limite = max_per_min
        rota = route_key or fn.__name__

        @wraps(fn)
        def wrapped(*a, **kw):
            if not _RL_ENABLED:
                return fn(*a, **kw)
            ip = _client_ip()
            chave_parts = [f'ip:{ip}']
            if body_key:
                try:
                    body = request.get_json(silent=True) or {}
                    valor = (body.get(body_key) or '').strip()[:32]
                    if valor:
                        chave_parts.append(f'{body_key}:{valor}')
                except Exception:
                    pass
            chave = '|'.join(chave_parts)
            allowed, count, retry_after = check_and_increment(chave, rota, limite)
            if not allowed:
                resp = jsonify({
                    'error': 'rate_limited',
                    'mensagem': f'Muitas tentativas. Espere {retry_after}s e tente de novo.',
                    'retry_after': retry_after,
                })
                resp.status_code = 429
                resp.headers['Retry-After'] = str(retry_after)
                resp.headers['X-RateLimit-Limit'] = str(limite)
                resp.headers['X-RateLimit-Remaining'] = '0'
                return resp
            return fn(*a, **kw)
        return wrapped
    return decorator


def rate_limit(max_per_min: int, env_var: str = None, route_key: str = None):
    """Decorator de rate limit por matricula. DEVE vir DEPOIS de @auth.require_auth
    (precisa de request.current_user populado).

    Args:
        max_per_min: limite default por minuto/matricula.
        env_var: nome de variavel de ambiente que sobrescreve o limite (ex:
                 'RATELIMIT_CLAUDE_PER_MIN'). Resolve em import-time — pra
                 mudar, precisa restart do gunicorn. Aceitavel: limites mudam raro.
        route_key: identificador da rota no banco. Se None, usa fn.__name__.
                   Use chave estavel — renomear funcao zera o contador!
    """
    def decorator(fn):
        limite = max_per_min
        if env_var:
            raw = os.environ.get(env_var)
            if raw is not None and raw.strip():
                try:
                    limite = int(raw)
                except (ValueError, TypeError):
                    print(f'[ratelimit] {env_var}={raw!r} invalido, usando default {max_per_min}')
                    limite = max_per_min
        rota = route_key or fn.__name__

        @wraps(fn)
        def wrapped(*a, **kw):
            user = getattr(request, 'current_user', None)
            matricula = user.get('matricula') if user else None
            if matricula and _RL_ENABLED:
                allowed, count, retry_after = check_and_increment(matricula, rota, limite)
                if not allowed:
                    resp = jsonify({
                        'error': 'rate_limited',
                        'mensagem': f'Calma ai! Voce passou de {limite} requests/min nessa rota. Tenta de novo em {retry_after}s.',
                        'limite': limite,
                        'rota': rota,
                        'retry_after': retry_after,
                    })
                    resp.status_code = 429
                    resp.headers['Retry-After'] = str(retry_after)
                    resp.headers['X-RateLimit-Limit'] = str(limite)
                    resp.headers['X-RateLimit-Remaining'] = '0'
                    return resp
            return fn(*a, **kw)
        return wrapped
    return decorator


def get_metrics() -> dict:
    """Snapshot das metricas pra /api/admin/metrics. Process-local — cada
    worker gunicorn tem seu proprio contador (nao tenta agregar entre workers
    pra evitar race condition + custo extra; admin pode chamar 2x e somar
    se quiser, mas pra trend monitoring de 1 worker so ja basta)."""
    with _metrics_lock:
        m = dict(_metrics)
    with _failopen_counter_lock:
        m['failopens_total'] = _failopen_counter
    m['enabled'] = _RL_ENABLED
    m['cleanup_every'] = _CLEANUP_EVERY
    m['cleanup_keep_min'] = _CLEANUP_KEEP_MIN
    return m
