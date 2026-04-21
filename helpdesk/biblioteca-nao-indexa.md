# Biblioteca não indexa o documento

## Sintomas
- Aparece "📎 Documento anexado!" mas não aparece o "✅ ... indexado".
- Ou aparece "⚠ Biblioteca: Não foi possível extrair texto útil do documento".

## Causa provável
1. PDF é uma **digitalização de imagem** (foto/scanner) — não tem texto, só pixels.
2. PDF está protegido por senha.
3. Arquivo é maior que 5MB.
4. Tipo de arquivo não suportado (Word .docx ainda não — só PDF e TXT).

## Solução
- **Para PDF digitalizado**: usar app de OCR (Adobe Scan, Microsoft Lens) e exportar como PDF "com texto pesquisável".
- **PDF com senha**: abrir num leitor de PDF, usar opção "imprimir como PDF" para gerar versão sem proteção.
- **Tamanho**: comprimir o PDF (ilovepdf.com, smallpdf.com).
- **Word**: por enquanto, exportar como PDF antes de anexar.

## Como o Viriato deve responder
"Esse arquivo provavelmente é uma digitalização sem texto pesquisável. Tenta usar o Adobe Scan ou o Microsoft Lens para gerar um PDF com OCR — aí eu consigo ler."
