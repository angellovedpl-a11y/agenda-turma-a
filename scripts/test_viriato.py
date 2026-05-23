#!/usr/bin/env python3
"""Teste isolado do /api/claude — bate direto em localhost:5000 sem passar pelo
proxy do Replit dev (*.replit.dev). Serve pra distinguir bug no server vs bug
no proxy/browser.

Uso (no Shell do Replit, com MAT e SEN exportados):
    python3 scripts/test_viriato.py

Output esperado:
    [login]  OK em 0.15s
    [claude] OK em 3.42s, resposta: "Olá! ..."

Se der erro de conexao ou timeout, mostra o stack trace.
"""
import os
import sys
import time
import json
import urllib.request
import urllib.error

BASE = "http://localhost:5000"
MAT = os.environ.get("MAT") or sys.exit("ERRO: exporta MAT antes (read -p 'mat: ' MAT && export MAT)")
SEN = os.environ.get("SEN") or sys.exit("ERRO: exporta SEN antes (read -s -p 'sen: ' SEN && export SEN)")


def main():
    # 1. Login
    t0 = time.time()
    try:
        req = urllib.request.Request(
            f"{BASE}/api/auth/login",
            data=json.dumps({"matricula": MAT, "senha": SEN}).encode(),
            headers={"Content-Type": "application/json"},
            method="POST",
        )
        resp = urllib.request.urlopen(req, timeout=15).read()
        token = json.loads(resp).get("token")
    except Exception as e:
        print(f"[login]  FALHOU em {time.time()-t0:.2f}s: {type(e).__name__}: {e}")
        sys.exit(1)
    print(f"[login]  OK em {time.time()-t0:.2f}s")

    # 2. /api/claude com "ola"
    t1 = time.time()
    body = json.dumps({
        "message": "ola",
        "conversation_history": [],
        "messages": [{"role": "user", "content": "ola"}],
    }).encode()
    try:
        req = urllib.request.Request(
            f"{BASE}/api/claude",
            data=body,
            headers={
                "Content-Type": "application/json",
                "Authorization": f"Bearer {token}",
            },
            method="POST",
        )
        resp = urllib.request.urlopen(req, timeout=120).read()
        data = json.loads(resp)
        texto = data.get("text") or data.get("error") or "(sem text/error)"
        print(f"[claude] OK em {time.time()-t1:.2f}s")
        print(f"         resposta ({len(texto)} chars): {texto[:300]!r}")
        if data.get("trechos_usados") is not None:
            print(f"         trechos_usados: {data['trechos_usados']}")
    except urllib.error.HTTPError as e:
        body_err = e.read().decode("utf-8", errors="replace")[:500]
        print(f"[claude] HTTP {e.code} em {time.time()-t1:.2f}s")
        print(f"         body: {body_err}")
    except Exception as e:
        print(f"[claude] FALHOU em {time.time()-t1:.2f}s: {type(e).__name__}: {e}")


if __name__ == "__main__":
    main()
