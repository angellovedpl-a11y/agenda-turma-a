from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import cm
from reportlab.lib.colors import HexColor, white, black
from reportlab.platypus import (SimpleDocTemplate, Paragraph, Spacer, PageBreak,
                                 Table, TableStyle, KeepTogether, Image)
from reportlab.lib.utils import ImageReader
import os

CAPA_IMG = "attached_assets/imagem_2_1776741704206.jpeg"
ANGELO_IMG = "attached_assets/angelo_imagem_1_1776741704207.jpeg"
VALE_LOGO = "attached_assets/vale.png"

VERDE_VALE = HexColor("#008f83")
VERDE_ESCURO = HexColor("#00564f")
AMARELO_VALE = HexColor("#fdb913")
from reportlab.lib.enums import TA_LEFT, TA_CENTER, TA_JUSTIFY

OUT = "manual_agenda_turma_a.pdf"

AZUL = HexColor("#008f83")  # Verde Vale (rebatizado pra nao quebrar refs)
AMARELO = HexColor("#fdb913")  # Amarelo Vale
CINZA = HexColor("#374151")
CINZA_CLARO = HexColor("#f3f4f6")
VERDE = HexColor("#059669")
VERMELHO = HexColor("#dc2626")

styles = getSampleStyleSheet()
H1 = ParagraphStyle("H1", parent=styles["Heading1"], fontSize=22, textColor=AZUL,
                     spaceAfter=14, spaceBefore=10, fontName="Helvetica-Bold")
H2 = ParagraphStyle("H2", parent=styles["Heading2"], fontSize=15, textColor=AZUL,
                     spaceAfter=8, spaceBefore=14, fontName="Helvetica-Bold")
H3 = ParagraphStyle("H3", parent=styles["Heading3"], fontSize=12, textColor=CINZA,
                     spaceAfter=4, spaceBefore=8, fontName="Helvetica-Bold")
P  = ParagraphStyle("P", parent=styles["BodyText"], fontSize=10.5, textColor=black,
                     leading=15, alignment=TA_JUSTIFY, spaceAfter=6)
LI = ParagraphStyle("LI", parent=P, leftIndent=14, bulletIndent=4, spaceAfter=3)
NOTA = ParagraphStyle("NOTA", parent=P, fontSize=10, textColor=CINZA, fontName="Helvetica-Oblique",
                       leftIndent=12, rightIndent=12, spaceBefore=4, spaceAfter=10)
CAPA_TIT = ParagraphStyle("CAPA_TIT", parent=H1, fontSize=30, alignment=TA_CENTER,
                           textColor=AZUL, spaceAfter=20)
CAPA_SUB = ParagraphStyle("CAPA_SUB", parent=P, fontSize=14, alignment=TA_CENTER,
                           textColor=CINZA, spaceAfter=10)

def header_footer(canvas, doc):
    canvas.saveState()
    canvas.setFillColor(AZUL)
    canvas.rect(0, A4[1]-1.2*cm, A4[0], 1.2*cm, fill=1, stroke=0)
    canvas.setFillColor(white)
    canvas.setFont("Helvetica-Bold", 10)
    canvas.drawString(1.5*cm, A4[1]-0.78*cm, "Agenda Turma A — Escala Ferroviária 2x2")
    canvas.drawRightString(A4[0]-1.5*cm, A4[1]-0.78*cm, "Manual de Instruções")
    canvas.setFillColor(CINZA)
    canvas.setFont("Helvetica", 8)
    canvas.drawCentredString(A4[0]/2, 0.8*cm, f"Página {doc.page}  |  Turma A — Manual do Aplicativo")
    canvas.restoreState()

def capa_canvas(canvas, doc):
    W, H = A4
    canvas.saveState()

    # 1) Foto da turma cobrindo a pagina inteira (plano de fundo)
    if os.path.exists(CAPA_IMG):
        img = ImageReader(CAPA_IMG)
        iw, ih = img.getSize()
        ratio = max(W/iw, H/ih)  # cobre toda a area
        w, h = iw*ratio, ih*ratio
        x = (W-w)/2
        y = (H-h)/2
        canvas.drawImage(img, x, y, width=w, height=h, mask='auto')
    else:
        canvas.setFillColor(VERDE_ESCURO)
        canvas.rect(0, 0, W, H, fill=1, stroke=0)

    # 2) Veu verde escuro semi-transparente para legibilidade
    canvas.setFillColor(VERDE_ESCURO)
    canvas.setFillAlpha(0.55)
    canvas.rect(0, 0, W, H, fill=1, stroke=0)
    canvas.setFillAlpha(1)

    # 3) Faixa superior (verde Vale) com logo
    faixa_top_h = 3.2*cm
    canvas.setFillColor(VERDE_VALE)
    canvas.rect(0, H-faixa_top_h, W, faixa_top_h, fill=1, stroke=0)
    # micro-faixa amarela abaixo
    canvas.setFillColor(AMARELO_VALE)
    canvas.rect(0, H-faixa_top_h-0.18*cm, W, 0.18*cm, fill=1, stroke=0)

    # logo Vale na faixa superior
    if os.path.exists(VALE_LOGO):
        logo = ImageReader(VALE_LOGO)
        liw, lih = logo.getSize()
        target_h = 1.6*cm
        target_w = target_h * (liw/lih)
        canvas.drawImage(logo, 1.5*cm, H-faixa_top_h+0.8*cm,
                         width=target_w, height=target_h,
                         preserveAspectRatio=True, mask='auto')

    # texto "PARCERIA DE QUEM ROLA NOS TRILHOS" no topo direito
    canvas.setFillColor(white)
    canvas.setFont("Helvetica", 9)
    canvas.drawRightString(W-1.5*cm, H-faixa_top_h+1.7*cm, "TURMA A  —  ESCALA FERROVIÁRIA 2x2")
    canvas.setFont("Helvetica-Bold", 10)
    canvas.setFillColor(AMARELO_VALE)
    canvas.drawRightString(W-1.5*cm, H-faixa_top_h+1.0*cm, "CICLO 2026 — 2030")

    # 4) Bloco central com titulo elegante
    centro_y = H/2 + 1.5*cm
    # caixa preta translucida
    box_w = W - 4*cm
    box_h = 6.5*cm
    canvas.setFillColor(black)
    canvas.setFillAlpha(0.35)
    canvas.roundRect(2*cm, centro_y - box_h/2, box_w, box_h, 0.3*cm, fill=1, stroke=0)
    canvas.setFillAlpha(1)
    # borda amarela fina
    canvas.setStrokeColor(AMARELO_VALE)
    canvas.setLineWidth(1.2)
    canvas.roundRect(2*cm, centro_y - box_h/2, box_w, box_h, 0.3*cm, fill=0, stroke=1)

    # texto AGENDA
    canvas.setFillColor(AMARELO_VALE)
    canvas.setFont("Helvetica-Bold", 14)
    canvas.drawCentredString(W/2, centro_y + 2.0*cm, "M A N U A L   D E   I N S T R U Ç Õ E S")

    # divisor
    canvas.setStrokeColor(AMARELO_VALE)
    canvas.setLineWidth(0.5)
    canvas.line(W/2 - 3*cm, centro_y + 1.4*cm, W/2 + 3*cm, centro_y + 1.4*cm)

    # nome do app grande
    canvas.setFillColor(white)
    canvas.setFont("Helvetica-Bold", 38)
    canvas.drawCentredString(W/2, centro_y + 0.1*cm, "Agenda Turma A")

    canvas.setFont("Helvetica", 13)
    canvas.setFillColor(HexColor("#e8f4f3"))
    canvas.drawCentredString(W/2, centro_y - 0.9*cm, "Escala ferroviária 2x2  •  2026 a 2030")

    # selo amarelo
    canvas.setFillColor(AMARELO_VALE)
    canvas.setFont("Helvetica-Bold", 10)
    canvas.drawCentredString(W/2, centro_y - 2.0*cm, "DE MAQUINISTA  PARA  MAQUINISTAS")

    # 5) Rodape elegante (verde com nota de autoria)
    rodape_h = 2.5*cm
    canvas.setFillColor(VERDE_VALE)
    canvas.rect(0, 0, W, rodape_h, fill=1, stroke=0)
    canvas.setFillColor(AMARELO_VALE)
    canvas.rect(0, rodape_h, W, 0.18*cm, fill=1, stroke=0)

    canvas.setFillColor(white)
    canvas.setFont("Helvetica-Bold", 11)
    canvas.drawCentredString(W/2, rodape_h - 1.0*cm, "Criado por Angelo Silva")
    canvas.setFont("Helvetica", 9)
    canvas.setFillColor(HexColor("#e8f4f3"))
    canvas.drawCentredString(W/2, rodape_h - 1.55*cm, "Maquinista — Turma A   •   Versão 2.2   •   Abril de 2026")

    canvas.restoreState()

def li(txt):
    return Paragraph("• " + txt, LI)

def nota(txt):
    return Paragraph("<b>💡 Dica:</b> " + txt, NOTA)

def aviso(txt):
    s = ParagraphStyle("AV", parent=NOTA, textColor=VERMELHO)
    return Paragraph("<b>⚠️ Atenção:</b> " + txt, s)

doc = SimpleDocTemplate(OUT, pagesize=A4,
                        leftMargin=2*cm, rightMargin=2*cm,
                        topMargin=2*cm, bottomMargin=1.8*cm,
                        title="Manual Agenda Turma A",
                        author="Turma A")

story = []

# Capa - desenhada por capa_canvas, primeira pagina vazia
story.append(PageBreak())

# Sumario
story.append(Paragraph("Sumário", H1))
sumario = [
    ("1.", "Boas-vindas", "3"),
    ("2.", "Primeiros passos: cadastro e login", "3"),
    ("3.", "A tela inicial e o menu da Porta", "5"),
    ("4.", "A escala 2x2: como ler", "7"),
    ("5.", "Mural da Turma (com reações)", "8"),
    ("6.", "Chat — conversas e grupos da turma", "9"),
    ("7.", "Acervo (biblioteca) e anexos até 50 MB", "10"),
    ("8.", "Função na ferrovia: Operacional ou Administrativa", "11"),
    ("9.", "Checklist Pré-Jornada", "12"),
    ("10.", "Viriato — o ajudante de bordo", "13"),
    ("11.", "Painel do administrador", "14"),
    ("12.", "Esqueci minha senha — e agora?", "15"),
    ("13.", "Trocar minha senha", "15"),
    ("14.", "Perguntas frequentes", "16"),
    ("15.", "Glossário ferroviário rápido", "17"),
    ("16.", "Créditos e agradecimentos", "18"),
]
data_sum = [[n, t, p] for n, t, p in sumario]
ts = Table(data_sum, colWidths=[1.2*cm, 13*cm, 1.5*cm])
ts.setStyle(TableStyle([
    ("FONT", (0,0), (-1,-1), "Helvetica", 11),
    ("TEXTCOLOR", (0,0), (0,-1), AZUL),
    ("FONTNAME", (0,0), (0,-1), "Helvetica-Bold"),
    ("ALIGN", (2,0), (2,-1), "RIGHT"),
    ("BOTTOMPADDING", (0,0), (-1,-1), 6),
    ("LINEBELOW", (0,0), (-1,-1), 0.3, CINZA_CLARO),
]))
story.append(ts)
story.append(PageBreak())

# 1. Boas-vindas
story.append(Paragraph("1. Boas-vindas", H1))

# Bloco com foto do Angelo ao lado do texto de assinatura
if os.path.exists(ANGELO_IMG):
    angelo_img = Image(ANGELO_IMG, width=3.8*cm, height=5.0*cm, kind="proportional")
    autor_par = Paragraph(
        "<para align='left'><font size='12' color='#008f83'><b>Angelo Silva</b></font><br/>"
        "<font size='10' color='#374151'>Maquinista — Turma A</font><br/>"
        "<font size='9' color='#6b7280'><i>Idealizador e desenvolvedor deste aplicativo "
        "e <b>criador do agente Viriato</b>, o assistente inteligente que conversa com a turma "
        "dentro do app. Esta é a foto que abre o caminho de cada turno: cabine, capacete, "
        "óculos, e a velha confiança na máquina.</i></font></para>", P)
    bloco = Table([[angelo_img, autor_par]], colWidths=[4.2*cm, 11*cm])
    bloco.setStyle(TableStyle([
        ("VALIGN", (0,0), (-1,-1), "MIDDLE"),
        ("LEFTPADDING", (0,0), (-1,-1), 0),
        ("RIGHTPADDING", (0,0), (-1,-1), 0),
        ("TOPPADDING", (0,0), (-1,-1), 6),
        ("BOTTOMPADDING", (0,0), (-1,-1), 6),
        ("LINEBEFORE", (1,0), (1,0), 0.6, AMARELO),
        ("LEFTPADDING", (1,0), (1,0), 12),
    ]))
    story.append(bloco)
    story.append(Spacer(1, 0.4*cm))

story.append(Paragraph(
    "Este aplicativo foi feito sob medida para a <b>Turma A</b> da escala ferroviária 2x2 "
    "(dois dias de trabalho, dois de folga). Ele cobre o ciclo completo de 2026 a 2030 e ajuda "
    "você a saber, com um toque, qual é o seu turno hoje.", P))
story.append(Paragraph(
    "A escala, os eventos, os documentos e o checklist ficam no seu celular e podem ser "
    "consultados a qualquer hora. Já o <b>Viriato (assistente de IA) precisa de internet</b> "
    "para responder, porque ele conversa com um servidor na nuvem. Sem sinal, o restante do app "
    "continua funcionando — só o Viriato fica em silêncio até a internet voltar.", P))
story.append(Paragraph(
    "O app não tem propaganda, não vende seus dados, e os novos cadastros só são liberados "
    "pelas <b>4 pessoas habilitadas</b> da turma (o administrador principal e até 3 aprovadores "
    "indicados por ele).", P))
story.append(nota("Se você está com pressa, pule direto para o capítulo 2 e siga o passo a passo. "
                  "O resto pode ler aos poucos, na hora do cafezinho."))

# 2. Primeiros passos
story.append(Paragraph("2. Primeiros passos: cadastro e login", H1))
story.append(Paragraph("2.1. Criando seu cadastro", H2))
story.append(Paragraph(
    "Quando você abre o app pela primeira vez, aparece a tela do <b>Viriato</b> (o trenzinho "
    "que conversa com você). Toque em <b>Criar cadastro</b> e preencha:", P))
story.append(li("<b>Nome completo:</b> exatamente como está no crachá."))
story.append(li("<b>Função na ferrovia:</b> escolha entre <b>Função Operacional</b> (quem cumpre escala 2x2 de campo, faz Prontos 1 e 2) ou <b>Função Administrativa</b> (escritório, coordenação, suporte)."))
story.append(li("<b>Matrícula:</b> sua matrícula da ferrovia (de 6 a 10 dígitos — empregados mais novos podem ter mais de 6)."))
story.append(li("<b>Senha:</b> 4 dígitos que só você sabe (evite 1234, 0000, sua data de nascimento)."))
story.append(Paragraph(
    "Depois de enviar, o cadastro fica <b>aguardando aprovação</b>. Apenas as <b>4 pessoas "
    "habilitadas</b> da turma (o admin principal e até 3 aprovadores indicados por ele) "
    "podem liberar novos usuários. Assim que uma delas aprovar (geralmente no mesmo dia), "
    "você já pode entrar normalmente.", P))
story.append(aviso("Não compartilhe sua senha com ninguém. Se desconfiar que alguém descobriu, "
                   "use o botão 🔑 no topo do app para trocar imediatamente."))

story.append(Paragraph("2.2. Fazendo login", H2))
story.append(Paragraph(
    "Na tela de entrada, toque em <b>Já tenho cadastro</b>, digite sua matrícula e sua senha "
    "de 4 dígitos. Pronto, está dentro.", P))

story.append(Paragraph("2.3. O que cada item do menu faz", H2))
story.append(Paragraph(
    "Na versão atual (2.2), os botões principais ficam dentro de um <b>popup que abre pelo "
    "ícone da Porta 🚪</b> no topo da tela, ao lado do botão de tema (sol/lua). Toque na "
    "Porta e o menu desce com estes itens:", P))
def badge(label, bg, fg=white):
    s = ParagraphStyle("BG", parent=P, alignment=TA_CENTER, fontName="Helvetica-Bold",
                       fontSize=10, textColor=fg, leading=12)
    p = Paragraph("<b>"+label+"</b>", s)
    t = Table([[p]], colWidths=[2.4*cm], rowHeights=[0.85*cm])
    t.setStyle(TableStyle([
        ("BACKGROUND", (0,0), (-1,-1), bg),
        ("VALIGN", (0,0), (-1,-1), "MIDDLE"),
        ("ALIGN", (0,0), (-1,-1), "CENTER"),
        ("LEFTPADDING", (0,0), (-1,-1), 0),
        ("RIGHTPADDING", (0,0), (-1,-1), 0),
        ("TOPPADDING", (0,0), (-1,-1), 0),
        ("BOTTOMPADDING", (0,0), (-1,-1), 0),
        ("ROUNDEDCORNERS", [4,4,4,4]),
    ]))
    return t

botoes = [
    ["Item do menu (Porta 🚪)", "O que faz"],
    [badge("CALENDÁRIO", AZUL), "Abre o calendário com a escala 2x2 (visões mensal e anual). Tela inicial do app."],
    [badge("MURAL", HexColor("#7c3aed")), "Mural da Turma — onde a turma posta avisos, fotos e arquivos pra todos verem. Inclui reações com emoji."],
    [badge("CHAT", HexColor("#16a34a")), "Conversas privadas e grupos da turma, estilo WhatsApp. Bolinha vermelha mostra mensagens não lidas."],
    [badge("ACERVO", HexColor("#0ea5e9")), "Biblioteca de documentos (PDFs, regulamentos, manuais). É o cérebro de consulta do Viriato."],
    [badge("CONFIG.", HexColor("#64748b")), "Tema claro/escuro, alarme da jornada, auditoria, trocar senha, sair, e (para admins) o painel de aprovação."],
    [badge("PRONTOS", HexColor("#fdb913"), black), "Atalho que abre o portal externo Sistema Prontos numa aba nova (pra fazer o teste antes da jornada)."],
    [badge("MANUAL", HexColor("#dc2626")), "Abre este manual em PDF numa aba nova, pronto pra ler ou imprimir."],
]
tb = Table(botoes, colWidths=[3*cm, 12*cm])
tb.setStyle(TableStyle([
    ("BACKGROUND", (0,0), (-1,0), AZUL),
    ("TEXTCOLOR", (0,0), (-1,0), white),
    ("FONTNAME", (0,0), (-1,0), "Helvetica-Bold"),
    ("FONT", (0,1), (-1,-1), "Helvetica", 10),
    ("ALIGN", (0,0), (0,-1), "CENTER"),
    ("VALIGN", (0,0), (-1,-1), "MIDDLE"),
    ("GRID", (0,0), (-1,-1), 0.4, CINZA_CLARO),
    ("ROWBACKGROUNDS", (0,1), (-1,-1), [white, CINZA_CLARO]),
    ("BOTTOMPADDING", (0,0), (-1,-1), 8),
    ("TOPPADDING", (0,0), (-1,-1), 8),
    ("LEFTPADDING", (1,0), (1,-1), 10),
]))
story.append(tb)
story.append(PageBreak())

# 3. Tela inicial
story.append(Paragraph("3. A tela inicial e o que cada coisa faz", H1))
story.append(Paragraph(
    "Logo que entra, você cai no <b>Calendário</b>. No topo ficam três coisas importantes:", P))
story.append(li("À esquerda, a marca <b>AGENDA TURMA A — Escala 2x2</b> com o símbolo da Vale."))
story.append(li("No meio, dois botões para alternar entre <b>MENSAL</b> e <b>ANUAL</b>."))
story.append(li("À direita, dois ícones pequenos: <b>🌗 Tema</b> (claro/escuro) e <b>🚪 Porta</b> "
                "(abre o menu com Calendário, Mural, Chat, Acervo, Configurações, Prontos e Manual)."))
story.append(Paragraph(
    "Logo abaixo do mês, aparece a caixa <b>ESTA SEMANA</b>: sete cartões pequenos (Dom a Sáb) "
    "mostrando se o dia é <b>TRAB</b> (trabalho) ou <b>FOLGA</b>. O dia de hoje vem destacado "
    "em <b>amarelo neon</b> com uma borda viva — bater o olho e já saber.", P))
story.append(Paragraph(
    "Mais abaixo entra o calendário do mês inteiro, depois a <b>lista de eventos</b> da turma, e "
    "por fim o <b>banner do Viriato</b> — uma faixa colorida que convida a abrir uma conversa com "
    "o assistente. Quando o banner está visível, o trenzinho 🚂 flutuante some pra não atrapalhar.", P))
story.append(nota("Toque em qualquer dia do calendário para abrir os detalhes daquele turno e "
                  "adicionar uma observação (por exemplo: 'cobertura do colega João')."))

# 4. Escala 2x2
story.append(Paragraph("4. A escala 2x2: como ler", H1))
story.append(Paragraph(
    "A regra é simples: <b>2 dias trabalha, 2 dias folga</b>, sem parar, ano após ano. O app já "
    "vem com a escala da Turma A pronta de <b>2026 até 2030</b>. Você não precisa configurar nada.", P))
story.append(Paragraph(
    "Para enxergar mais longe que a semana atual, role a tela para baixo: aparecem as próximas "
    "semanas, o mês inteiro e até o calendário anual com as cores da escala.", P))

leg = [
    ["Cor", "Significado"],
    ["Azul", "Dia de Serviço (escala 2x2)"],
    ["Amarelo", "Dia de Folga"],
    ["Verde", "Feriado nacional"],
    ["Vermelho", "Hoje (destaque) ou aviso de documento vencendo"],
]
tl = Table(leg, colWidths=[3*cm, 12*cm])
tl.setStyle(TableStyle([
    ("BACKGROUND", (0,0), (-1,0), AZUL),
    ("TEXTCOLOR", (0,0), (-1,0), white),
    ("FONTNAME", (0,0), (-1,0), "Helvetica-Bold"),
    ("FONT", (0,1), (-1,-1), "Helvetica", 10),
    ("BACKGROUND", (0,1), (0,1), HexColor("#3b9eff")),
    ("TEXTCOLOR", (0,1), (0,1), white),
    ("BACKGROUND", (0,2), (0,2), AMARELO),
    ("BACKGROUND", (0,3), (0,3), VERDE),
    ("TEXTCOLOR", (0,3), (0,3), white),
    ("BACKGROUND", (0,4), (0,4), VERMELHO),
    ("TEXTCOLOR", (0,4), (0,4), white),
    ("ALIGN", (0,0), (0,-1), "CENTER"),
    ("VALIGN", (0,0), (-1,-1), "MIDDLE"),
    ("GRID", (0,0), (-1,-1), 0.4, CINZA_CLARO),
    ("BOTTOMPADDING", (0,0), (-1,-1), 8),
    ("TOPPADDING", (0,0), (-1,-1), 8),
]))
story.append(tl)
story.append(PageBreak())

# 5. Mural de Eventos
story.append(Paragraph("5. Mural da Turma", H1))
story.append(Paragraph(
    "O <b>Mural</b> (item do menu da Porta 🚪) é onde a turma deixa avisos que <b>todo mundo "
    "precisa ver</b>: comunicados da coordenação, fotos da equipe, escalas extras, troca de turno "
    "combinada, etc. Não é conversa privada — é o quadro de avisos compartilhado.", P))
story.append(li("Toque em <b>+ NOVO EVENTO</b> para postar uma nova mensagem com título, data, "
                "hora e descrição."))
story.append(li("Posts ficam ordenados pela data do evento."))
story.append(li("Cada post mostra o nome de quem postou e a data."))

story.append(Paragraph("5.1. Reações com emoji", H2))
story.append(Paragraph(
    "Embaixo de cada post existe uma <b>barra de reações</b> com 8 emojis para você responder "
    "rapidinho, sem precisar escrever:", P))
story.append(li("<b>👍 Joia</b> — concordo, beleza, anotado."))
story.append(li("<b>❤️ Coração</b> — gostei, valeu, me emocionou."))
story.append(li("<b>😂 Risada</b> — pra brincadeira, foto engraçada do pátio."))
story.append(li("<b>😮 Surpresa</b> — pra notícia inesperada."))
story.append(li("<b>🎉 Festa</b> — comemoração, conquista, aniversário."))
story.append(li("<b>🙏 Agradecimento</b> — valeu pela cobertura, obrigado pelo aviso."))
story.append(li("<b>👏 Palmas</b> — parabéns, mandou bem."))
story.append(li("<b>🚂 Trenzinho</b> — assunto ferroviário, simbólico da turma."))
story.append(Paragraph(
    "Toque uma vez para reagir; toque de novo no mesmo emoji para retirar sua reação. Quando "
    "alguém reage, aparece o <b>contador</b> ao lado do emoji. Sua reação fica destacada em "
    "<b>amarelo neon</b> pra você lembrar onde já reagiu.", P))

story.append(nota("Conversas pessoais ou em pequeno grupo não vão aqui — vão no <b>Chat</b> (capítulo 6)."))

# 5.2 Eventos no calendário (mantido)
story.append(Paragraph("5.2. Eventos no calendário (médico, viagem, hora extra)", H2))
story.append(Paragraph(
    "Independente do Mural, cada dia do calendário aceita os seus <b>eventos pessoais</b>. "
    "Toque em qualquer dia (no mês ou no calendário anual) para abrir o detalhe do dia e criar "
    "um evento. Os tipos disponíveis são:", P))
story.append(li("🎂 <b>Aniversário</b> — basta cadastrar uma vez; o app repete automaticamente todo ano 🔁."))
story.append(li("🏥 <b>Médico</b> — consultas, ASO periódico, exames complementares."))
story.append(li("✈ <b>Viagem</b> — viagens pessoais ou a serviço."))
story.append(li("📋 <b>Compromisso</b> — qualquer compromisso pessoal (cartório, escola dos filhos, reunião)."))
story.append(li("⏰ <b>Hora Extra</b> — registro de horas trabalhadas além da escala."))
story.append(li("⭐ <b>Outro</b> — para o que não se encaixa nos demais."))
story.append(Paragraph(
    "Cada evento aparece direto no cartão do dia e também na lista geral (botão "
    "<b>📋 Eventos</b>). Você pode editar ou apagar tocando nele.", P))
story.append(nota("Para registrar troca de turno ou cobertura de colega, use o tipo <b>Compromisso</b> "
                  "ou <b>Outro</b> e descreva no texto (ex.: 'Cobertura do João'). Útil quando o "
                  "supervisor pergunta meses depois quem cobriu quem."))

# 6. Chat
story.append(Paragraph("6. Chat — conversas e grupos da turma", H1))
story.append(Paragraph(
    "O <b>Chat</b> (ícone do balão de fala na barra lateral) funciona parecido com o WhatsApp, "
    "mas <b>dentro do app da turma</b>. Serve pra conversa privada (1 pra 1) ou em grupos pequenos "
    "(escala da semana, churrasco do mês, troca de cobertura, etc).", P))
story.append(li("Toque em <b>+ Nova conversa</b>, escolha um colega aprovado e pronto — começa "
                "uma conversa privada."))
story.append(li("Para criar um <b>grupo</b>, marque dois ou mais colegas e dê um nome ao grupo "
                "(ex.: 'Turma A — Avisos rápidos')."))
story.append(li("Você pode mandar <b>texto</b> e <b>anexos</b> (foto, PDF, áudio, vídeo curto) "
                "até <b>50 MB</b> por arquivo. Imagens aparecem direto na bolha; PDFs viram link "
                "pra abrir."))
story.append(li("Toque na <b>★ estrela</b> embaixo de uma mensagem pra marcá-la como importante. "
                "Mensagens com estrela ficam <b>pra sempre</b>; as outras são apagadas "
                "automaticamente após <b>30 dias</b> pra não pesar o app."))
story.append(li("A <b>bolinha vermelha</b> em cima do ícone do Chat conta quantas mensagens não "
                "lidas você tem em todas as conversas."))
story.append(li("Pra sair de um grupo (ou apagar uma conversa privada do seu lado), toque no "
                "botão <b>Sair</b> dentro da conversa."))
story.append(nota("Conversas e grupos só enxergam <b>colegas aprovados</b> pelos administradores. "
                  "Cadastros pendentes não aparecem na lista."))
story.append(aviso("Não use o Chat pra avisos que <b>todos da turma</b> precisam ver — esses vão no "
                   "<b>Mural</b> (capítulo 5). Chat é pra conversa direta."))

# 7. Acervo
story.append(Paragraph("7. Acervo (biblioteca) e anexos até 50 MB", H1))
story.append(Paragraph(
    "O <b>Acervo</b> (item do menu da Porta 🚪) é a <b>biblioteca de documentos</b> da turma. "
    "É também o <b>cérebro de consulta do Viriato</b>: tudo que você anexa aqui, ele pode ler e "
    "usar pra responder perguntas.", P))
story.append(li("<b>📎 Anexar documento</b> — para arquivos <b>permanentes</b>: regulamentos, "
                "manuais técnicos, acordos coletivos, normas de segurança."))
story.append(li("<b>📌 Marcar como TEMP</b> — para arquivos que <b>mudam com frequência</b> "
                "(boletins da semana, escalas reajustadas). Toque no 📌 antes de anexar; ele acende "
                "em <b>laranja</b>; depois toque no 📎."))
story.append(li("<b>Limite de tamanho:</b> até <b>50 MB</b> por arquivo, em qualquer canto do app "
                "(Acervo, Mural ou Chat). Acima disso o app recusa antes de subir."))

story.append(Paragraph("7.1. O que o Viriato consegue ler de cada formato", H2))
story.append(Paragraph(
    "Nem todo arquivo é igual. Veja o que acontece quando você sobe cada tipo no Acervo:", P))
formatos = [
    ["Formato", "O Viriato lê o conteúdo?"],
    ["PDF com texto (digitado)", "✅ Sim. Texto extraído na hora."],
    ["PDF escaneado / foto de papel virada PDF", "✅ Sim. O servidor faz OCR automático usando inteligência artificial (Vision)."],
    ["DOCX (Word) / TXT", "✅ Sim. Texto extraído na hora."],
    ["PPTX (PowerPoint)", "✅ Sim. Texto dos slides é extraído."],
    ["Imagem solta (JPG, PNG)", "❌ Não. O documento entra com o nome, mas o Viriato não enxerga o que está escrito na imagem."],
]
tf = Table(formatos, colWidths=[5*cm, 10*cm])
tf.setStyle(TableStyle([
    ("BACKGROUND", (0,0), (-1,0), AZUL),
    ("TEXTCOLOR", (0,0), (-1,0), white),
    ("FONTNAME", (0,0), (-1,0), "Helvetica-Bold"),
    ("FONT", (0,1), (-1,-1), "Helvetica", 10),
    ("FONTNAME", (0,1), (0,-1), "Helvetica-Bold"),
    ("VALIGN", (0,0), (-1,-1), "TOP"),
    ("GRID", (0,0), (-1,-1), 0.4, CINZA_CLARO),
    ("ROWBACKGROUNDS", (0,1), (-1,-1), [white, CINZA_CLARO]),
    ("BOTTOMPADDING", (0,0), (-1,-1), 7),
    ("TOPPADDING", (0,0), (-1,-1), 7),
    ("LEFTPADDING", (0,0), (-1,-1), 8),
]))
story.append(tf)
story.append(nota("Vai fotografar uma escala ou um boletim impresso? Salve como <b>PDF</b> antes de subir "
                  "(qualquer aplicativo de scanner do celular faz isso). Aí o OCR roda automaticamente "
                  "e o Viriato passa a enxergar o conteúdo. Subir como JPG/PNG só serve para guardar a "
                  "imagem; o Viriato não vai conseguir responder perguntas sobre o que está escrito nela."))

# 8. Função na ferrovia
story.append(Paragraph("8. Função na ferrovia: Operacional ou Administrativa", H1))
story.append(Paragraph(
    "No cadastro, e também ao entrar pela primeira vez depois de uma atualização, o app pergunta "
    "qual é a sua <b>função na ferrovia</b>. Existem duas opções:", P))
story.append(li("<b>Função Operacional</b> — quem trabalha na escala 2x2 de campo, faz cabine, pátio "
                "ou inspeção. Vê os itens <b>Prontos 1</b> e <b>Prontos 2</b> no Checklist e recebe "
                "lembretes automáticos pela manhã (a partir das 06:00) e à tarde (após 14:30) nos "
                "dias de serviço."))
story.append(li("<b>Função Administrativa</b> — quem trabalha em escritório, coordenação ou suporte. "
                "Não precisa fazer Prontos, então o Checklist mostra só o ASO e os itens pessoais "
                "que você cadastrar."))
story.append(Paragraph(
    "Você pode mudar sua função a qualquer momento, mas isso normalmente só acontece se você for "
    "transferido entre operação e administração. Se errar na hora do cadastro, peça pro Angelo "
    "(ou um aprovador) corrigir.", P))
story.append(aviso("Quem é da Função Operacional <b>não pode esquecer dos Prontos</b>. O app avisa, "
                   "mas a responsabilidade de fazer o teste antes de assumir a jornada continua sendo "
                   "sua. Banner laranja no topo = teste pendente."))

# 7. Checklist
story.append(Paragraph("9. Checklist Pré-Jornada", H1))
story.append(Paragraph(
    "Toque no ícone da <b>prancheta 📋</b> no topo da tela para abrir o <b>Checklist</b>. "
    "Ele já vem pronto com o básico da Turma A:", P))
story.append(Paragraph("• <b>ASO</b> — Atestado de Saúde Ocupacional (com data de validade)", P))
story.append(Paragraph("• <b>Prontos 1</b> — teste psicotécnico antes da jornada da manhã <i>(só Função Operacional)</i>", P))
story.append(Paragraph("• <b>Prontos 2</b> — teste psicotécnico antes da jornada da tarde <i>(só Função Operacional)</i>", P))
story.append(Paragraph(
    "Marque cada item conforme for cumprindo. Para o ASO, dá pra registrar a data de "
    "validade — o app avisa quando estiver perto de vencer. Você também pode adicionar "
    "ou remover itens à vontade (lanterna, garrafa, cobertor, o que precisar).", P))
story.append(nota("Os itens Prontos 1 e Prontos 2 só aparecem para quem se cadastrou como "
                  "<b>Função Operacional</b>. Se você é Administrativa, vai ver só o ASO no Checklist. "
                  "Os itens extras que você adicionar ficam salvos no seu celular."))
story.append(PageBreak())

# 8. Viriato
story.append(Paragraph("10. Viriato — o ajudante de bordo", H1))
story.append(Paragraph(
    "O <b>Viriato</b> é um agente inteligente <b>criado pelo Angelo Silva</b> "
    "especialmente para esta agenda. Não é um chatbot genérico copiado da internet: ele foi "
    "moldado com a linguagem da turma, com o jeito ferroviário de falar e com o conhecimento "
    "da rotina 2x2.", P))

story.append(Paragraph("10.1. Como abrir o Viriato", H2))
story.append(Paragraph(
    "O Viriato aparece em três lugares — o caminho que estiver mais à mão:", P))
story.append(li("<b>Banner colorido no Calendário</b> (faixa roxa-verde abaixo dos eventos): "
                "toque para abrir a tela cheia de conversa. O banner volta toda vez que você "
                "abre o Calendário."))
story.append(li("<b>Trenzinho flutuante 🚂</b> no canto inferior direito: arrastável, sempre à "
                "mão em qualquer aba. Some sozinho quando o banner do Viriato está visível, pra "
                "não atrapalhar."))
story.append(li("<b>Janelinha pop-up</b>: tocar no trenzinho abre uma janela menor por cima da "
                "tela, sem precisar sair de onde você está."))

story.append(Paragraph("10.2. Como conversar com ele", H2))
story.append(Paragraph(
    "Pode perguntar qualquer coisa em português comum, por exemplo:", P))
story.append(li("<i>“Quando é minha próxima folga?”</i>"))
story.append(li("<i>“Quantos dias trabalhei esse mês?”</i>"))
story.append(li("<i>“Qual o prazo do meu ASO?”</i>"))
story.append(li("<i>“Como faço pra trocar turno com o Pedro?”</i>"))
story.append(li("<i>“Resume pra mim o ACT 2025/2027.”</i>"))
story.append(Paragraph(
    "Ele responde no jargão ferroviário — se você errar uma senha três vezes, ele diz "
    "<b>“🚦 Parada pelo Governador!”</b> em vez de um chato “erro 401”.", P))
story.append(nota("O Viriato não inventa: se ele não souber, vai dizer que não sabe e sugerir falar "
                  "com o Angelo."))

story.append(Paragraph("10.3. O Viriato precisa de internet", H2))
story.append(Paragraph(
    "O resto do app (escala, eventos, checklist, mural) funciona offline. O Viriato precisa "
    "de internet porque conversa com um servidor de inteligência artificial na nuvem. Sem sinal, "
    "ele fica em silêncio até a conexão voltar — o restante do app continua normal.", P))

story.append(Paragraph("10.4. Quero que o Viriato leia um documento meu", H2))
story.append(Paragraph(
    "O chat do Viriato hoje não tem botão de anexar arquivo. O caminho correto é:", P))
story.append(li("Abra o <b>Acervo</b> (item Acervo no menu da Porta 🚪)."))
story.append(li("Toque em <b>📎 Anexar documento</b> e escolha o arquivo (PDF, DOCX, PPTX, TXT)."))
story.append(li("Espere processar (alguns segundos). Pronto: o Viriato passa a poder consultar "
                "esse conteúdo nas próximas perguntas."))
story.append(aviso("Imagens soltas (JPG/PNG) <b>não</b> são lidas. Se for uma foto de papel, salve "
                   "como PDF antes de subir — assim o OCR é acionado automaticamente. Detalhes na "
                   "tabela do capítulo 7.1."))

# 9. Painel admin
story.append(Paragraph("11. Painel do administrador", H1))
story.append(Paragraph(
    "Esta seção interessa <b>apenas às 4 pessoas habilitadas</b> da turma: o "
    "<b>administrador principal</b> (Angelo Silva) e até <b>3 aprovadores</b> indicados por "
    "ele. Somente estes 4 podem aprovar novos usuários — ninguém mais.", P))
story.append(Paragraph("11.1. O que essas 4 pessoas podem fazer", H2))
story.append(li("<b>Aprovar</b> ou <b>Negar</b> novos cadastros (aparecem com badge no 👑)."))
story.append(li("<b>Promover</b> outro usuário a aprovador (somente o admin principal pode fazer isso, e o limite é 3)."))
story.append(li("<b>Resetar a senha</b> de qualquer colega — aparece um código temporário de 4 dígitos para você passar pelo WhatsApp ou pessoalmente."))
story.append(li("<b>Remover</b> usuários que saíram da turma."))
story.append(Paragraph("11.2. Aprovação de cadastros", H2))
story.append(Paragraph(
    "Quando alguém se cadastra, aparece uma bolinha vermelha com o número de pendentes no botão "
    "👑. Toque, confira nome e matrícula com o crachá da pessoa, e clique em <b>Aprovar</b> ou "
    "<b>Negar</b>. Negar é definitivo: a pessoa vai precisar se cadastrar de novo se for engano.", P))
story.append(aviso("Antes de aprovar, confirme pessoalmente que a matrícula bate com a pessoa. "
                   "Quem entra aqui tem acesso à escala e aos eventos da turma."))

# 10. Esqueci a senha
story.append(Paragraph("12. Esqueci minha senha — e agora?", H1))
story.append(Paragraph(
    "Calma, sem stress. Tem dois caminhos:", P))
story.append(Paragraph("<b>Caminho 1 — Pelo Viriato (mais rápido):</b>", P))
story.append(li("Na tela de login, toque em <b>“Esqueci minha senha”</b>."))
story.append(li("Informe sua <b>matrícula</b> e seu <b>nome completo cadastrado</b>."))
story.append(li("O Viriato gera uma <b>senha temporária de 4 dígitos</b> e mostra na tela."))
story.append(li("Anote, faça login com ela e troque imediatamente no botão 🔑."))
story.append(Paragraph("<b>Caminho 2 — Pelo administrador:</b>", P))
story.append(li("Chame o Angelo (ou um aprovador) pessoalmente ou por WhatsApp."))
story.append(li("Ele entra no painel admin, toca em <b>🔑 Reset</b> ao lado do seu nome e te passa o código de 4 dígitos."))
story.append(li("Você entra com esse código e troca pela sua senha definitiva."))
story.append(aviso("Toda vez que sua senha for resetada ou trocada, todas as sessões antigas em "
                   "outros celulares são canceladas automaticamente. Quem estava logado é deslogado."))

# 11. Trocar senha
story.append(Paragraph("13. Trocar minha senha", H1))
story.append(Paragraph(
    "A qualquer momento, dentro do app, toque no <b>🔑</b> no topo. O sistema vai pedir:", P))
story.append(li("Sua <b>senha atual</b> (4 dígitos)"))
story.append(li("Sua <b>nova senha</b> (4 dígitos novos)"))
story.append(Paragraph(
    "Pronto. A senha antiga deixa de funcionar e qualquer outro celular onde você estava logado "
    "vai cair na tela de login.", P))
story.append(nota("Se aparecer um aviso laranja no topo dizendo <b>“Senha temporária ativa”</b>, "
                  "é porque você entrou com uma senha gerada pelo Viriato ou pelo admin. Troque "
                  "logo para uma senha sua de verdade."))
story.append(PageBreak())

# 12. FAQ
story.append(Paragraph("14. Perguntas frequentes", H1))
faqs = [
    ("Funciona sem internet?",
     "Em parte. A escala, os eventos, os documentos e o checklist funcionam no celular mesmo sem sinal. "
     "Já o <b>Viriato precisa de internet</b> para responder, porque ele conversa com um servidor de "
     "inteligência artificial na nuvem. Sem internet, o resto do app continua normal, só o Viriato fica "
     "indisponível até o sinal voltar."),
    ("Posso instalar como aplicativo de verdade no celular?",
     "Pode. Abra no Chrome (Android) ou Safari (iPhone), toque no menu e escolha "
     "“Adicionar à tela inicial”. Vira ícone igual a qualquer app."),
    ("Meus dados ficam onde?",
     "Os dados pessoais (cadastro, eventos seus) ficam no servidor da Turma A. "
     "Senhas são guardadas embaralhadas — nem o Angelo consegue ver a sua."),
    ("Quantas pessoas podem usar?",
     "A turma toda. As aprovações de novos cadastros ficam restritas a 4 pessoas habilitadas: "
     "o admin principal (Angelo) e até 3 aprovadores indicados por ele."),
    ("Esqueci a senha e o Angelo tá viajando, e agora?",
     "Use o Viriato (capítulo 10, caminho 1). Ele gera uma senha temporária na hora, "
     "sem precisar do admin."),
    ("Posso usar o app no celular do colega?",
     "Pode, mas lembre de sair (botão 🚪) ao terminar. Senão ele vai ver suas coisas."),
    ("Quanto custa?",
     "Nada para a turma. O Angelo banca o custo de servidor. Não tem propaganda nem cobrança."),
    ("E se eu mudar de celular?",
     "É só baixar o app no novo (mesmo endereço) e fazer login com matrícula + senha. "
     "Tudo aparece igualzinho."),
    ("Posso jogar uma foto no Acervo e perguntar ao Viriato sobre o que está escrito?",
     "Não diretamente, se a foto for JPG/PNG. O Viriato só lê texto extraído de PDF, DOCX, "
     "PPTX ou TXT. Para ele entender uma foto de papel (boletim, escala, regulamento impresso), "
     "salve antes como <b>PDF</b> — qualquer app de scanner do celular faz isso. Aí o servidor "
     "roda OCR automático e o conteúdo passa a ser consultável. Detalhes na tabela do capítulo 7.1."),
    ("Onde encontro este manual depois?",
     "No menu da <b>Porta 🚪</b>, item <b>📕 Manual</b>. Abre o PDF numa aba nova, dá pra ler ou imprimir."),
]
for q, a in faqs:
    story.append(Paragraph("<b>" + q + "</b>", H3))
    story.append(Paragraph(a, P))

story.append(PageBreak())

# 13. Glossario
story.append(Paragraph("15. Glossário ferroviário rápido", H1))
gloss = [
    ["Termo", "Significado"],
    ["Bater asa", "Cometer erros bobos no dia a dia."],
    ["Parada pelo Governador", "Parada no sistema (operação interrompida)."],
    ["Turma A", "Equipe da escala 2x2 deste app."],
    ["Escala 2x2", "Dois dias de trabalho seguidos por dois de folga, sem parar."],
    ["ASO", "Atestado de Saúde Ocupacional — exame periódico obrigatório."],
    ["Prontos 1 / Prontos 2", "Testes psicotécnicos feitos antes de iniciar a jornada (manhã e tarde). Obrigatórios para a Função Operacional."],
    ["Função Operacional", "Quem cumpre escala 2x2 de campo (cabine, pátio, inspeção). Faz Prontos 1 e 2."],
    ["Função Administrativa", "Quem trabalha no escritório, coordenação ou suporte. Não faz Prontos."],
    ["Aprovador", "Colega indicado pelo admin para aprovar cadastros. São no máximo 3, totalizando 4 pessoas habilitadas com o admin."],
    ["Senha temporária", "Senha de 4 dígitos gerada pelo Viriato ou pelo admin, válida só até você trocar."],
    ["TEMP (📌)", "Pasta separada da biblioteca para arquivos que mudam com frequência (boletins, escalas reajustadas, avisos). Marque com 📌 antes de anexar com 📎."],
    ["Viriato", "O trenzinho assistente que ajuda dentro do app."],
    ["Porta (🚪)", "Ícone no topo da tela. Abre o menu com Calendário, Mural, Chat, Acervo, Configurações, Prontos e Manual."],
    ["Banner do Viriato", "Faixa colorida que aparece no Calendário convidando a conversar com o Viriato. Volta toda vez que você abre essa aba."],
    ["FAB / Trenzinho 🚂", "Botão flutuante e arrastável do Viriato no canto inferior direito. Some quando o banner do Viriato está visível, pra não atrapalhar."],
    ["Reações (Mural)", "Os 8 emojis sob cada post do mural (👍 ❤️ 😂 😮 🎉 🙏 👏 🚂). Toque para reagir; toque de novo no mesmo emoji para retirar."],
    ["OCR", "Reconhecimento Óptico de Caracteres. O servidor faz OCR automático em PDF escaneado para extrair o texto. Em imagem solta (JPG/PNG) o OCR não roda — salve antes como PDF."],
]
tg = Table(gloss, colWidths=[4*cm, 11*cm])
tg.setStyle(TableStyle([
    ("BACKGROUND", (0,0), (-1,0), AZUL),
    ("TEXTCOLOR", (0,0), (-1,0), white),
    ("FONTNAME", (0,0), (-1,0), "Helvetica-Bold"),
    ("FONT", (0,1), (-1,-1), "Helvetica", 10),
    ("FONTNAME", (0,1), (0,-1), "Helvetica-Bold"),
    ("VALIGN", (0,0), (-1,-1), "TOP"),
    ("GRID", (0,0), (-1,-1), 0.3, CINZA_CLARO),
    ("ROWBACKGROUNDS", (0,1), (-1,-1), [white, CINZA_CLARO]),
    ("BOTTOMPADDING", (0,0), (-1,-1), 7),
    ("TOPPADDING", (0,0), (-1,-1), 7),
    ("LEFTPADDING", (0,0), (-1,-1), 8),
]))
story.append(tg)

story.append(PageBreak())

# 14. Creditos e agradecimentos
story.append(Paragraph("16. Créditos e agradecimentos", H1))

story.append(Paragraph("Idealização, projeto e desenvolvimento", H2))
story.append(Paragraph(
    "<b>Angelo Silva</b> — Maquinista da Turma A. Criador, idealizador e "
    "desenvolvedor deste aplicativo, e também <b>criador do agente Viriato</b>, o assistente "
    "inteligente embarcado no app, treinado para falar a língua da turma e ajudar nas dúvidas "
    "do dia a dia ferroviário.", P))

story.append(Paragraph("Sobre o esforço por trás do app", H2))
story.append(Paragraph(
    "Este aplicativo nasceu da rotina de quem vive a escala 2x2 na pele. Foram <b>muitos dias</b> "
    "de trabalho — entre turnos, folgas que viraram noites de código, ideias rabiscadas no caderno "
    "durante a viagem e ajustes feitos depois de conversar com os colegas no pátio. Cada tela, "
    "cada cor, cada botão deste app foi pensado para resolver uma dor real da turma: a escala que "
    "ninguém lembra de cor, o documento que vence sem avisar, a troca de turno que fica solta no "
    "WhatsApp, o checklist que esquecemos no fim do dia.", P))
story.append(Paragraph(
    "Foi um projeto feito <b>de maquinista para maquinistas</b>, sem ajuda de empresa, sem "
    "patrocínio, sem prazo. Só com vontade de deixar a vida da turma um pouquinho mais "
    "organizada — e, quem sabe, servir de exemplo de que dá pra ir além do volante.", P))

story.append(Paragraph("Agradecimentos especiais", H2))

story.append(Paragraph(
    "Em primeiro lugar, ao <b>Nosso Eterno Criador</b>, que nos deu forma e nos capacitou "
    "para liderarmos sobre todas as espécies da terra.", P))

story.append(Paragraph(
    "Ao meu filho <b>Angelo Guilherme</b>, que despertou em mim o interesse pela programação "
    "e pelo <i>vibe coding</i> — sem ele, este aplicativo simplesmente não existiria.", P))

story.append(Paragraph(
    "À <b>Coordenação</b>, na pessoa da <b>Jéssica</b>, pela confiança, pelo apoio e por "
    "acreditar que uma boa ideia pode vir de qualquer lugar — inclusive da cabine.", P))

story.append(Paragraph(
    "Aos amigos que doaram tempo, ouvido e crítica construtiva ao longo do caminho:", P))

amigos = ["Ivana Viegas", "Glória Mulato", "Geidher Aurélio", "Rafael Melo",
          "Carlos Deleon", "Bruno Anderson", "Micael Viana", "Marcos Lima", "Arthur Diniz"]
for nome in amigos:
    story.append(li("<b>" + nome + "</b>"))

story.append(Spacer(1, 0.2*cm))
story.append(Paragraph(
    "E a <b>todos os amigos da Turma</b> que, de alguma forma, contribuíram com disponibilidade "
    "para ouvir a ideia, dar palpites, apontar o que não fazia sentido e sugerir o que ficaria "
    "melhor. Sem vocês, este app seria só um arquivo esquecido no celular.", P))

story.append(Spacer(1, 0.6*cm))
story.append(Paragraph(
    "🚂  O App tá pronto, gente. Espero que gostem.  🚂",
    ParagraphStyle("FINAL", parent=P, alignment=TA_CENTER, textColor=AZUL,
                   fontName="Helvetica-Bold", fontSize=14, spaceAfter=18)))

story.append(Paragraph(
    "<i>— Angelloti, com carinho, para toda nossa turma. Abril de 2026.</i>",
    ParagraphStyle("ASS", parent=P, alignment=TA_CENTER, textColor=CINZA,
                   fontName="Helvetica-Oblique", fontSize=11)))

story.append(Spacer(1, 0.4*cm))
story.append(Paragraph(
    "<i>Boa viagem, Turma A. Que a escala seja sempre clara e os documentos sempre em dia.</i>",
    ParagraphStyle("FIM", parent=P, alignment=TA_CENTER, textColor=AZUL,
                   fontName="Helvetica-Oblique", fontSize=11)))

def first_page(canvas, doc_):
    capa_canvas(canvas, doc_)

def later_pages(canvas, doc_):
    header_footer(canvas, doc_)

doc.build(story, onFirstPage=first_page, onLaterPages=later_pages)
print("OK:", OUT)
