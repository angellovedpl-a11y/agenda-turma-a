"""Config do Gunicorn para resolver o bug de SSL "bad record mac" em prod.

PROBLEMA: com `--preload`, o master importa server.py UMA vez antes de fazer
fork dos workers. Esse import dispara `kvstore.init_schema()` (linha 55 do
server.py), que cria o pool de conexoes psycopg2 com sockets SSL abertos.
Quando o master faz os.fork(), os file descriptors SSL sao DUPLICADOS entre
os 2 workers — ambos passam a usar as mesmas conexoes SSL com o mesmo estado
criptografico (chaves de sessao, contadores de bloco). Resultado: erros como
"SSL error: ssl/tls alert bad record mac", "decryption failed or bad record
mac", "SSL SYSCALL error: EOF detected" — o openssl detecta que dois lados
estao escrevendo no mesmo stream com contadores fora de sincronia.

SOLUCAO: o hook `post_fork` roda dentro de cada worker depois do fork. Aqui
descartamos o pool herdado do master e forcamos o `_get_pool()` a recriar um
pool novo (com conexoes SSL frescas, exclusivas do worker). Padrao reconhecido
para psycopg2/redis-py/SQLAlchemy + gunicorn --preload.

NAO REMOVER `--preload`: ele e necessario pra evitar o boot timeout em Reserved
VM (importar server.py leva 30-60s na primeira vez; sem preload os 2 workers
fazem isso em paralelo competindo por CPU e o load balancer marca unhealthy).
"""


def post_fork(server, worker):
    # FAIL-FAST: se nao conseguir resetar o pool, este worker AINDA TEM o pool
    # herdado do master (com sockets SSL compartilhados) e vai reproduzir o bug
    # "bad record mac". Eh muito melhor matar o worker e deixar o gunicorn
    # respawnar do que servir 8 threads x N requests com DB envenenado.
    try:
        import kvstore
        kvstore.close_pool()
        server.log.info(f'[gunicorn] worker {worker.pid} pool DB resetado pos-fork')
    except Exception as e:
        server.log.error(
            f'[gunicorn] worker {worker.pid} FALHA CRITICA ao resetar pool DB pos-fork: {e}. '
            f'Encerrando worker pra evitar servir requests com SSL compartilhado.'
        )
        import sys
        sys.exit(1)
