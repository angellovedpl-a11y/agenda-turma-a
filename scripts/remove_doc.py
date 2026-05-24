"""Remove um documento da biblioteca por nome (match parcial).
Uso: python3 scripts/remove_doc.py "trecho do nome"
"""
import sys
sys.path.insert(0, '.')
import kvstore

if len(sys.argv) < 2:
    print('Uso: python3 scripts/remove_doc.py "trecho do nome"')
    sys.exit(1)

termo = sys.argv[1]
bib = kvstore.load('sala:biblioteca')
docs = bib.get('documentos', [])

encontrados = [d for d in docs if termo.lower() in d.get('nome', '').lower()]

if not encontrados:
    print(f'Nenhum doc com "{termo}" no nome.')
    sys.exit(1)

print(f'Encontrados {len(encontrados)} doc(s):')
for d in encontrados:
    print(f'  - {d["nome"]} ({len(d.get("chunks",[]))} chunks)')

print(f'\nRemovendo...')
bib['documentos'] = [d for d in docs if d not in encontrados]
kvstore.save('sala:biblioteca', bib)
print(f'OK. Biblioteca agora tem {len(bib["documentos"])} docs.')
