#!/usr/bin/env python3
"""
Extrator em lote para a biblioteca do Viriato.

Uso:
    python3 extrair_pasta.py [pasta_entrada] [--upload] [--token TOKEN]

- Lê todos os arquivos suportados (PDF, DOCX, PPTX, TXT, MD) da pasta de entrada
- Salva o texto extraído como .md em documentos_extraidos_md/
- Se --upload for passado, envia direto para a biblioteca do app
"""
import os
import sys
import base64
import json
import urllib.request
import urllib.error
from datetime import datetime

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from server import extrair_texto_arquivo

PASTA_ENTRADA_PADRAO = 'documentos_para_extrair'
PASTA_SAIDA = 'documentos_extraidos_md'
EXTENSOES = ('.pdf', '.docx', '.pptx', '.txt', '.md')

MIMETYPES = {
    '.pdf': 'application/pdf',
    '.docx': 'application/vnd.openxmlformats-officedocument.wordprocessingml.document',
    '.pptx': 'application/vnd.openxmlformats-officedocument.presentationml.presentation',
    '.txt': 'text/plain',
    '.md': 'text/markdown',
}


def gerar_markdown(nome_arquivo: str, texto: str) -> str:
    titulo = os.path.splitext(nome_arquivo)[0].replace('_', ' ').replace('-', ' ').strip()
    cabecalho = (
        f"# {titulo}\n\n"
        f"> Arquivo original: `{nome_arquivo}`\n"
        f"> Extraído em: {datetime.now().strftime('%Y-%m-%d %H:%M')}\n"
        f"> Caracteres: {len(texto)}\n\n"
        f"---\n\n"
    )
    return cabecalho + texto.strip() + "\n"


def upload_biblioteca(nome: str, conteudo_md: str, token: str, base_url: str = 'http://localhost:5000') -> dict:
    b64 = base64.b64encode(conteudo_md.encode('utf-8')).decode('ascii')
    payload = json.dumps({
        'nome': nome,
        'data': b64,
        'mimetype': 'text/markdown',
        'temp': False,
    }).encode()
    req = urllib.request.Request(
        f'{base_url}/api/biblioteca/upload',
        data=payload,
        headers={
            'Content-Type': 'application/json',
            'Authorization': f'Bearer {token}',
        },
        method='POST',
    )
    try:
        r = urllib.request.urlopen(req, timeout=120)
        return {'ok': True, 'resp': json.loads(r.read().decode())}
    except urllib.error.HTTPError as e:
        return {'ok': False, 'erro': f'HTTP {e.code}: {e.read().decode()[:200]}'}
    except Exception as e:
        return {'ok': False, 'erro': str(e)}


def processar_arquivo(caminho: str) -> dict:
    nome = os.path.basename(caminho)
    ext = os.path.splitext(nome)[1].lower()
    mimetype = MIMETYPES.get(ext, '')
    try:
        with open(caminho, 'rb') as f:
            raw = f.read()
        b64 = base64.b64encode(raw).decode('ascii')
        texto = extrair_texto_arquivo(b64, mimetype, nome)
        if not texto or len(texto.strip()) < 30:
            return {'nome': nome, 'ok': False, 'erro': 'Texto insuficiente extraído'}
        md = gerar_markdown(nome, texto)
        nome_md = os.path.splitext(nome)[0] + '.md'
        caminho_md = os.path.join(PASTA_SAIDA, nome_md)
        os.makedirs(PASTA_SAIDA, exist_ok=True)
        with open(caminho_md, 'w', encoding='utf-8') as f:
            f.write(md)
        return {'nome': nome, 'ok': True, 'md': caminho_md, 'chars': len(texto), 'conteudo_md': md, 'nome_md': nome_md}
    except Exception as e:
        return {'nome': nome, 'ok': False, 'erro': str(e)}


def main():
    args = sys.argv[1:]
    pasta = PASTA_ENTRADA_PADRAO
    upload = False
    token = None
    i = 0
    while i < len(args):
        a = args[i]
        if a == '--upload':
            upload = True
        elif a == '--token':
            i += 1
            token = args[i] if i < len(args) else None
        elif not a.startswith('--'):
            pasta = a
        i += 1

    if upload and not token:
        token = os.environ.get('VIRIATO_TOKEN')
    if upload and not token:
        print('ERRO: --upload requer --token TOKEN ou env VIRIATO_TOKEN')
        sys.exit(1)

    if not os.path.isdir(pasta):
        print(f'ERRO: pasta "{pasta}" não encontrada')
        sys.exit(1)

    arquivos = sorted([
        os.path.join(pasta, f) for f in os.listdir(pasta)
        if os.path.isfile(os.path.join(pasta, f)) and f.lower().endswith(EXTENSOES)
    ])

    if not arquivos:
        print(f'Nenhum arquivo suportado encontrado em {pasta}')
        print(f'Suportados: {", ".join(EXTENSOES)}')
        return

    print(f'Encontrados {len(arquivos)} arquivo(s) em {pasta}')
    print('=' * 60)

    sucesso, falha, enviados = 0, 0, 0
    for caminho in arquivos:
        r = processar_arquivo(caminho)
        if r['ok']:
            sucesso += 1
            print(f'[OK]   {r["nome"]:<50} {r["chars"]:>7} chars  →  {r["md"]}')
            if upload:
                up = upload_biblioteca(r['nome_md'], r['conteudo_md'], token)
                if up['ok']:
                    enviados += 1
                    info = up['resp']
                    print(f'         ↳ enviado: {info.get("categoria")} / {info.get("chunks")} chunks')
                else:
                    print(f'         ↳ FALHA upload: {up["erro"]}')
        else:
            falha += 1
            print(f'[FAIL] {r["nome"]:<50} {r["erro"]}')

    print('=' * 60)
    print(f'Concluído: {sucesso} extraídos, {falha} falhas, {enviados} enviados à biblioteca')
    print(f'Markdowns salvos em: {PASTA_SAIDA}/')


if __name__ == '__main__':
    main()
