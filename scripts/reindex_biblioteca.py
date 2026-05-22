#!/usr/bin/env python3
"""Helper pra rodar reindex da biblioteca (Voyage embeddings) localmente.

Uso (no Shell do Replit):
    python3 scripts/reindex_biblioteca.py

Vai pedir matricula e senha do admin (a senha nao aparece no terminal).
Loga via /api/auth/login, pega o token, dispara POST /api/admin/biblioteca/reindex,
e imprime o JSON de resultado. Reindex demora 3-5 min pros 14 docs.
"""
import getpass
import json
import sys
import urllib.request
import urllib.error

BASE = "http://localhost:5000"


def main():
    mat = input("Matricula admin: ").strip()
    sen = getpass.getpass("Senha (nao aparece no terminal): ").strip()

    print("\nFazendo login...")
    req = urllib.request.Request(
        f"{BASE}/api/auth/login",
        data=json.dumps({"matricula": mat, "senha": sen}).encode(),
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    try:
        data = json.loads(urllib.request.urlopen(req, timeout=10).read())
    except urllib.error.HTTPError as e:
        print(f"ERRO login (HTTP {e.code}):", e.read().decode()[:300])
        sys.exit(1)
    except Exception as e:
        print(f"ERRO login: {type(e).__name__}: {e}")
        sys.exit(1)

    token = data.get("token")
    if not token:
        print("Login retornou sem token:", data)
        sys.exit(1)
    print(f"Login OK (token {token[:8]}...). Reindexando 14 PDFs (3-5 min)...\n")
    sys.stdout.flush()

    req = urllib.request.Request(
        f"{BASE}/api/admin/biblioteca/reindex",
        headers={"Authorization": f"Bearer {token}"},
        method="POST",
    )
    try:
        result = json.loads(urllib.request.urlopen(req, timeout=900).read())
    except urllib.error.HTTPError as e:
        print(f"ERRO reindex (HTTP {e.code}):", e.read().decode()[:500])
        sys.exit(1)

    print("=== RESULTADO ===")
    print(json.dumps(result, indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()
