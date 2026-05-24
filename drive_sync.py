"""Sync de documentos do Google Drive → Biblioteca do Viriato.

Lê PDFs de uma pasta compartilhada via Service Account,
extrai texto, chunka e indexa no pgvector — igual ao upload manual,
mas com a fonte sendo o Drive.

Uso: importar drive_sync() no server.py e chamar via endpoint admin.
"""

import os
import io
import re
import json
import time
import base64
import threading

PASTA_RAIZ_ID = os.environ.get(
    'DRIVE_ACERVO_FOLDER_ID',
    '1S326rElTZYAGM6amSeldiQnEf7xYQG1-'
)

CATEGORIA_POR_PASTA = {
    'normas': 'norma_tecnica',
    'act-vale': 'acordo_coletivo',
    'manuais': 'manual',
    'layout-patios': 'ferroviario',
    'treinamentos': 'seguranca',
    'outros': 'outros',
}

_sync_lock = threading.Lock()
_sync_running = False


def _get_drive_service():
    from google.oauth2 import service_account
    from googleapiclient.discovery import build

    creds_json = os.environ.get('GOOGLE_SERVICE_ACCOUNT_JSON', '')
    if not creds_json:
        raise RuntimeError('GOOGLE_SERVICE_ACCOUNT_JSON nao configurada')
    creds_data = json.loads(creds_json)
    creds = service_account.Credentials.from_service_account_info(
        creds_data, scopes=['https://www.googleapis.com/auth/drive.readonly']
    )
    return build('drive', 'v3', credentials=creds, cache_discovery=False)


def _listar_subpastas(service, pasta_pai_id: str) -> list:
    """Lista subpastas imediatas. Retorna [(id, nome)]."""
    resp = service.files().list(
        q=f"'{pasta_pai_id}' in parents and mimeType='application/vnd.google-apps.folder' and trashed=false",
        fields='files(id,name)',
        pageSize=50
    ).execute()
    return [(f['id'], f['name']) for f in resp.get('files', [])]


def _listar_pdfs(service, pasta_id: str) -> list:
    """Lista PDFs dentro de uma pasta. Retorna [{id, name, modifiedTime, size}]."""
    pdfs = []
    page_token = None
    while True:
        resp = service.files().list(
            q=f"'{pasta_id}' in parents and mimeType='application/pdf' and trashed=false",
            fields='nextPageToken,files(id,name,modifiedTime,size)',
            pageSize=100,
            pageToken=page_token
        ).execute()
        pdfs.extend(resp.get('files', []))
        page_token = resp.get('nextPageToken')
        if not page_token:
            break
    return pdfs


def _baixar_pdf(service, file_id: str) -> bytes:
    """Baixa conteúdo de um arquivo do Drive."""
    from googleapiclient.http import MediaIoBaseDownload
    request = service.files().get_media(fileId=file_id)
    buf = io.BytesIO()
    downloader = MediaIoBaseDownload(buf, request)
    done = False
    while not done:
        _, done = downloader.next_chunk()
    return buf.getvalue()


def _docs_existentes_drive(biblioteca: dict) -> dict:
    """Mapeia drive_file_id → doc existente na biblioteca."""
    mapa = {}
    for doc in biblioteca.get('documentos', []):
        dfid = doc.get('drive_file_id')
        if dfid:
            mapa[dfid] = doc
    return mapa


def drive_sync(
    extrair_texto_fn,
    fazer_chunks_fn,
    categorizar_doc_fn,
    mem_palace_load_fn,
    mem_palace_save_fn,
    indexar_batch_fn,
):
    """Sincroniza PDFs do Google Drive → biblioteca do Viriato.

    Recebe as funções do server.py como parâmetros pra não criar
    imports circulares.

    Retorna dict com resultado: {novos, atualizados, erros, detalhes}.
    """
    global _sync_running
    if not _sync_lock.acquire(blocking=False):
        return {'erro': 'Sync já em andamento'}
    try:
        _sync_running = True
        t0 = time.time()
        print('[drive_sync] INICIO', flush=True)

        service = _get_drive_service()
        subpastas = _listar_subpastas(service, PASTA_RAIZ_ID)
        print(f'[drive_sync] {len(subpastas)} subpastas encontradas', flush=True)

        biblioteca = mem_palace_load_fn('biblioteca')
        existentes = _docs_existentes_drive(biblioteca)

        novos = 0
        atualizados = 0
        erros = []
        detalhes = []

        for pasta_id, pasta_nome in subpastas:
            categoria = CATEGORIA_POR_PASTA.get(pasta_nome.lower(), 'outros')
            pdfs = _listar_pdfs(service, pasta_id)
            print(f'[drive_sync] pasta={pasta_nome} categoria={categoria} pdfs={len(pdfs)}', flush=True)

            for pdf in pdfs:
                fid = pdf['id']
                fname = pdf['name']
                fmod = pdf.get('modifiedTime', '')

                doc_existente = existentes.get(fid)
                if doc_existente:
                    if doc_existente.get('drive_modified') == fmod:
                        continue
                    print(f'[drive_sync] ATUALIZAR {fname} (modified changed)', flush=True)
                else:
                    print(f'[drive_sync] NOVO {fname}', flush=True)

                try:
                    raw = _baixar_pdf(service, fid)
                    b64_data = base64.b64encode(raw).decode()
                    texto = extrair_texto_fn(b64_data, 'application/pdf', fname)

                    if not texto or len(texto.strip()) < 30:
                        erros.append(f'{fname}: texto insuficiente ({len(texto or "")} chars)')
                        continue

                    chunks = fazer_chunks_fn(texto)

                    doc_id = re.sub(r'[^a-z0-9]+', '-', fname.lower())[:60].strip('-')
                    doc_id += '-drive-' + str(int(time.time()))

                    if doc_existente:
                        docs = biblioteca.get('documentos', [])
                        biblioteca['documentos'] = [
                            d for d in docs if d.get('drive_file_id') != fid
                        ]
                        atualizados += 1
                    else:
                        novos += 1

                    novo_doc = {
                        'id': doc_id,
                        'nome': fname,
                        'categoria': categoria,
                        'resumo': '',
                        'palavras_chave': [],
                        'caracteres': len(texto),
                        'chunks': chunks,
                        'data_envio': time.strftime('%Y-%m-%d %H:%M'),
                        'fonte': 'google_drive',
                        'drive_file_id': fid,
                        'drive_modified': fmod,
                        'drive_pasta': pasta_nome,
                    }

                    try:
                        meta = categorizar_doc_fn(fname, texto)
                        novo_doc['resumo'] = meta.get('resumo', '')
                        novo_doc['palavras_chave'] = meta.get('palavras_chave', [])
                    except Exception:
                        pass

                    biblioteca.setdefault('documentos', []).append(novo_doc)
                    mem_palace_save_fn('biblioteca', biblioteca)

                    indexar_batch_fn(doc_id, chunks)
                    detalhes.append(f'{fname}: {len(chunks)} chunks, {categoria}')
                    print(f'[drive_sync] OK {fname} chunks={len(chunks)}', flush=True)

                except Exception as e:
                    erros.append(f'{fname}: {e}')
                    print(f'[drive_sync] ERRO {fname}: {e}', flush=True)

        elapsed = time.time() - t0
        print(f'[drive_sync] FIM em {elapsed:.1f}s novos={novos} atualizados={atualizados} erros={len(erros)}', flush=True)
        return {
            'novos': novos,
            'atualizados': atualizados,
            'erros': erros,
            'detalhes': detalhes,
            'tempo_s': round(elapsed, 1),
        }
    finally:
        _sync_running = False
        _sync_lock.release()


def is_sync_running():
    return _sync_running
