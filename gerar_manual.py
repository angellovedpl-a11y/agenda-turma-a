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
    canvas.drawCentredString(W/2, rodape_h - 1.55*cm, "Maquinista — Turma A   •   Versão 1.0   •   Abril de 2026")

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
    ("3.", "A tela inicial e o que cada coisa faz", "5"),
    ("4.", "A escala 2x2: como ler", "6"),
    ("5.", "Eventos: marcar exames, férias, folgas e trocas", "7"),
    ("6.", "Documentos: ASO, NR-11 e outros vencimentos", "8"),
    ("7.", "Checklist Pré-Jornada", "9"),
    ("8.", "Viriato — o ajudante de bordo", "10"),
    ("9.", "Painel do administrador", "11"),
    ("10.", "Esqueci minha senha — e agora?", "12"),
    ("11.", "Trocar minha senha", "12"),
    ("12.", "Perguntas frequentes", "13"),
    ("13.", "Glossário ferroviário rápido", "14"),
    ("14.", "Créditos e agradecimentos", "15"),
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
    "você a saber, com um toque, qual é o seu turno hoje, quando vence cada documento, qual "
    "exame está chegando e o que precisa ir na mochila para a próxima viagem.", P))
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
story.append(li("<b>Matrícula:</b> seus 6 dígitos da ferrovia."))
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

story.append(Paragraph("2.3. O que cada botão do topo faz", H2))
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
    ["Botão (cor)", "O que faz"],
    [badge("ADMIN", AMARELO, black), "Abre o painel do administrador (só aparece para as 4 pessoas habilitadas a aprovar). É o ícone de coroa amarela no topo do app."],
    [badge("CHAVE", HexColor("#0ea5e9")), "Trocar a sua própria senha. É o ícone de chave azul no topo do app."],
    [badge("SAIR", HexColor("#dc2626")), "Sair (encerra a sessão neste celular). É o ícone de porta vermelha no topo do app."],
    [badge("VIRIATO", AZUL), "Abre o assistente inteligente. É o ícone do trenzinho verde, geralmente na lateral da tela."],
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
    "Logo que entra, você vê a sua <b>semana atual</b> em formato de cartões grandes, fáceis "
    "de bater o olho. Cada cartão mostra:", P))
story.append(li("O <b>dia da semana</b> e a data."))
story.append(li("Se é <b>Trabalho</b> (cor amarela) ou <b>Folga</b> (cor verde)."))
story.append(li("Eventuais <b>marcadores</b> (exame médico, troca, férias, folga extra)."))
story.append(Paragraph(
    "Acima da semana ficam os <b>indicadores rápidos</b>: dias trabalhados no mês, próxima folga, "
    "documentos vencendo nos próximos 30 dias e checklist pendente.", P))
story.append(nota("Toque em qualquer cartão de dia para abrir os detalhes daquele turno e adicionar "
                  "uma observação (por exemplo: 'cobertura do colega João')."))

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
    ["Amarelo", "Dia de trabalho normal"],
    ["Verde", "Folga regular"],
    ["Azul", "Folga extra ou compensação"],
    ["Vermelho", "Atenção: documento ou exame vencendo"],
    ["Cinza", "Férias programadas"],
]
tl = Table(leg, colWidths=[3*cm, 12*cm])
tl.setStyle(TableStyle([
    ("BACKGROUND", (0,0), (-1,0), AZUL),
    ("TEXTCOLOR", (0,0), (-1,0), white),
    ("FONTNAME", (0,0), (-1,0), "Helvetica-Bold"),
    ("FONT", (0,1), (-1,-1), "Helvetica", 10),
    ("BACKGROUND", (0,1), (0,1), AMARELO),
    ("BACKGROUND", (0,2), (0,2), VERDE),
    ("TEXTCOLOR", (0,2), (0,2), white),
    ("BACKGROUND", (0,3), (0,3), HexColor("#3b82f6")),
    ("TEXTCOLOR", (0,3), (0,3), white),
    ("BACKGROUND", (0,4), (0,4), VERMELHO),
    ("TEXTCOLOR", (0,4), (0,4), white),
    ("BACKGROUND", (0,5), (0,5), HexColor("#9ca3af")),
    ("TEXTCOLOR", (0,5), (0,5), white),
    ("ALIGN", (0,0), (0,-1), "CENTER"),
    ("VALIGN", (0,0), (-1,-1), "MIDDLE"),
    ("GRID", (0,0), (-1,-1), 0.4, CINZA_CLARO),
    ("BOTTOMPADDING", (0,0), (-1,-1), 8),
    ("TOPPADDING", (0,0), (-1,-1), 8),
]))
story.append(tl)
story.append(PageBreak())

# 5. Eventos
story.append(Paragraph("5. Eventos: marcar exames, férias, folgas e trocas", H1))
story.append(Paragraph(
    "Toque no botão <b>+</b> (canto inferior) para criar um evento. Os tipos disponíveis são:", P))
story.append(li("<b>Exame médico</b> (ASO periódico, exames complementares)."))
story.append(li("<b>Curso / treinamento</b> (NR, reciclagens, cursos internos)."))
story.append(li("<b>Férias</b> (marca o período inteiro de uma vez)."))
story.append(li("<b>Folga extra</b> (compensações, abonos)."))
story.append(li("<b>Troca de turno</b> (com o nome do colega que está cobrindo)."))
story.append(li("<b>Aniversário</b> — basta cadastrar uma vez, o app repete automaticamente todo ano 🔁."))
story.append(li("<b>Pessoal</b> (consulta, qualquer compromisso seu)."))
story.append(Paragraph(
    "Cada evento aparece direto no cartão do dia e também na lista geral. Você pode editar ou "
    "apagar tocando duas vezes nele.", P))
story.append(nota("As trocas de turno ficam registradas com data e nome — útil quando o supervisor "
                  "pergunta meses depois quem cobriu quem."))

# 6. Documentos
story.append(Paragraph("6. Documentos: ASO, NR-11 e outros vencimentos", H1))
story.append(Paragraph(
    "Na aba <b>Documentos</b>, cadastre tudo que tem prazo de validade na ferrovia:", P))
story.append(li("ASO (Atestado de Saúde Ocupacional) — o principal, exigido por lei"))
story.append(li("Habilitação Ferroviária e certificado de maquinista"))
story.append(li("NR-11 e outras normas regulamentadoras"))
story.append(li("Crachá e certificados internos"))
story.append(Paragraph(
    "Para cada documento, informe o <b>nome</b>, a <b>data de vencimento</b> e, se quiser, anexe "
    "uma observação (por exemplo: 'fazer no posto da Vila Industrial'). O app começa a avisar "
    "<b>60 dias antes</b> e o aviso fica vermelho a partir de 30 dias.", P))
story.append(aviso("Documento vencido = afastamento. Não confie só na memória, deixe o app cuidar."))

# 7. Checklist
story.append(Paragraph("7. Checklist Pré-Jornada", H1))
story.append(Paragraph(
    "Toque no ícone da <b>prancheta 📋</b> no topo da tela para abrir o <b>Checklist</b>. "
    "Ele já vem pronto com o básico da Turma A:", P))
story.append(Paragraph("• <b>ASO</b> — Atestado de Saúde Ocupacional (com data de validade)", P))
story.append(Paragraph("• <b>Prontos 1</b> — confirmação da prontidão pela manhã", P))
story.append(Paragraph("• <b>Prontos 2</b> — confirmação da prontidão pela tarde", P))
story.append(Paragraph(
    "Marque cada item conforme for cumprindo. Para o ASO, dá pra registrar a data de "
    "validade — o app avisa quando estiver perto de vencer. Você também pode adicionar "
    "ou remover itens à vontade (lanterna, garrafa, cobertor, o que precisar).", P))
story.append(nota("Os itens que você adicionar ficam salvos no seu celular. Já o ASO, "
                  "Prontos 1 e Prontos 2 não podem ser apagados — fazem parte do checklist padrão da turma."))
story.append(PageBreak())

# 8. Viriato
story.append(Paragraph("8. Viriato — o ajudante de bordo", H1))
story.append(Paragraph(
    "O <b>Viriato</b> é um agente inteligente <b>criado pelo Angelo Silva</b> "
    "especialmente para esta agenda. Não é um chatbot genérico copiado da internet: ele foi "
    "moldado com a linguagem da turma, com o jeito ferroviário de falar e com o conhecimento "
    "da rotina 2x2.", P))
story.append(Paragraph(
    "Aparece como o trenzinho 🚂 na lateral da tela. Pode perguntar qualquer coisa em "
    "português comum, por exemplo:", P))
story.append(li("<i>“Quando é minha próxima folga?”</i>"))
story.append(li("<i>“Quantos dias trabalhei esse mês?”</i>"))
story.append(li("<i>“Qual o prazo do meu ASO?”</i>"))
story.append(li("<i>“Como faço pra trocar turno com o Pedro?”</i>"))
story.append(li("<i>“Esqueci minha senha, me ajuda?”</i>"))
story.append(Paragraph(
    "Ele responde no jargão ferroviário — se você errar uma senha três vezes, ele diz "
    "<b>“🚦 Parada pelo Governador!”</b> em vez de um chato “erro 401”.", P))
story.append(nota("O Viriato não inventa: se ele não souber, vai dizer que não sabe e sugerir falar "
                  "com o Angelo."))

# 9. Painel admin
story.append(Paragraph("9. Painel do administrador", H1))
story.append(Paragraph(
    "Esta seção interessa <b>apenas às 4 pessoas habilitadas</b> da turma: o "
    "<b>administrador principal</b> (Angelo Silva) e até <b>3 aprovadores</b> indicados por "
    "ele. Somente estes 4 podem aprovar novos usuários — ninguém mais.", P))
story.append(Paragraph("9.1. O que essas 4 pessoas podem fazer", H2))
story.append(li("<b>Aprovar</b> ou <b>Negar</b> novos cadastros (aparecem com badge no 👑)."))
story.append(li("<b>Promover</b> outro usuário a aprovador (somente o admin principal pode fazer isso, e o limite é 3)."))
story.append(li("<b>Resetar a senha</b> de qualquer colega — aparece um código temporário de 4 dígitos para você passar pelo WhatsApp ou pessoalmente."))
story.append(li("<b>Remover</b> usuários que saíram da turma."))
story.append(Paragraph("9.2. Aprovação de cadastros", H2))
story.append(Paragraph(
    "Quando alguém se cadastra, aparece uma bolinha vermelha com o número de pendentes no botão "
    "👑. Toque, confira nome e matrícula com o crachá da pessoa, e clique em <b>Aprovar</b> ou "
    "<b>Negar</b>. Negar é definitivo: a pessoa vai precisar se cadastrar de novo se for engano.", P))
story.append(aviso("Antes de aprovar, confirme pessoalmente que a matrícula bate com a pessoa. "
                   "Quem entra aqui tem acesso à escala e aos eventos da turma."))

# 10. Esqueci a senha
story.append(Paragraph("10. Esqueci minha senha — e agora?", H1))
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
story.append(Paragraph("11. Trocar minha senha", H1))
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
story.append(Paragraph("12. Perguntas frequentes", H1))
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
]
for q, a in faqs:
    story.append(Paragraph("<b>" + q + "</b>", H3))
    story.append(Paragraph(a, P))

story.append(PageBreak())

# 13. Glossario
story.append(Paragraph("13. Glossário ferroviário rápido", H1))
gloss = [
    ["Termo", "Significado"],
    ["Bater asa", "Cometer erros bobos no dia a dia."],
    ["Parada pelo Governador", "Parada no sistema (operação interrompida)."],
    ["Turma A", "Equipe da escala 2x2 deste app."],
    ["Escala 2x2", "Dois dias de trabalho seguidos por dois de folga, sem parar."],
    ["ASO", "Atestado de Saúde Ocupacional — exame periódico obrigatório."],
    ["NR-11", "Norma regulamentadora de transporte e movimentação de cargas."],
    ["Aprovador", "Colega indicado pelo admin para aprovar cadastros. São no máximo 3, totalizando 4 pessoas habilitadas com o admin."],
    ["Senha temporária", "Senha de 4 dígitos gerada pelo Viriato ou pelo admin, válida só até você trocar."],
    ["Viriato", "O trenzinho assistente que ajuda dentro do app."],
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
story.append(Paragraph("14. Créditos e agradecimentos", H1))

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
