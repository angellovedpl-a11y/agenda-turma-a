
console.log("%c[Agenda Turma A] Build: 2026-04-28 v3.4 (menu enxuto + Diario/MeusEventos no clique do dia)", "background:#00e676;color:#001a0c;padding:3px 8px;border-radius:6px;font-weight:700");
// ===== Constantes =====
const FER={"2026-01-01":"Confraternizacao Universal","2026-04-03":"Paixao de Cristo","2026-04-05":"Pascoa","2026-04-21":"Tiradentes","2026-05-01":"Dia do Trabalho","2026-06-04":"Corpus Christi","2026-09-07":"Independencia do Brasil","2026-10-12":"N.Sra.Aparecida","2026-11-02":"Finados","2026-11-15":"Proclamacao da Republica","2026-11-20":"Consciencia Negra","2026-12-25":"Natal"};
const MESES=["Janeiro","Fevereiro","Março","Abril","Maio","Junho","Julho","Agosto","Setembro","Outubro","Novembro","Dezembro"];
const MESES3=["Jan","Fev","Mar","Abr","Mai","Jun","Jul","Ago","Set","Out","Nov","Dez"];
const DOW=["DOM","SEG","TER","QUA","QUI","SEX","SAB"];
const EVENTO_TIPOS={
  aniversario:{emoji:"🎂",label:"Aniversário",cor:"#ec4899",rec:true},
  medico:     {emoji:"🏥",label:"Médico",     cor:"#ef4444"},
  viagem:     {emoji:"✈️",label:"Viagem",     cor:"#3b82f6"},
  compromisso:{emoji:"📋",label:"Compromisso",cor:"#14b8a6"},
  hora_extra: {emoji:"⏰",label:"Hora Extra", cor:"#fbbf24"},
  dss:        {emoji:"🛡️",label:"DSS",        cor:"#f5a623"},
  outro:      {emoji:"⭐",label:"Outro",      cor:"#94a3b8"}
};
function evTipoInfo(t){return EVENTO_TIPOS[t]||EVENTO_TIPOS.outro;}
let EVENTOS_CACHE=[];
let EVENTOS_PESS_CACHE=[];
async function carregarEventosCache(){
  try{const r=await apiFetch("/api/mem/eventos");const d=await r.json();EVENTOS_CACHE=d.eventos||[];}catch(e){EVENTOS_CACHE=[];}
  try{const r=await apiFetch("/api/eventos-pessoais");const d=await r.json();EVENTOS_PESS_CACHE=(d.eventos||[]).map(e=>Object.assign({},e,{_pessoal:true}));}catch(e){EVENTOS_PESS_CACHE=[];}
}
function eventosNoDia(k){
  // k = "YYYY-MM-DD" — junta mural + pessoais
  const [a,m,d]=k.split("-");
  const mmdd=`${m}-${d}`;
  const filtra=e=>{
    if(!e.data)return false;
    if(e.data===k)return true;
    if(e.tipo==="aniversario"&&e.data.slice(5)===mmdd)return true;
    return false;
  };
  return EVENTOS_CACHE.filter(filtra).concat(EVENTOS_PESS_CACHE.filter(filtra));
}
const DOW_FULL=["Domingo","Segunda-feira","Terça-feira","Quarta-feira","Quinta-feira","Sexta-feira","Sábado"];
const DOW_MINI=["D","S","T","Q","Q","S","S"];

// REF: 22/04/2026 = 1º dia de TRABALHO do par. Ciclo: trab,trab,folga,folga (2x2).
const REF=new Date(2026,3,22);
function toKey(d){return d.getFullYear()+"-"+String(d.getMonth()+1).padStart(2,"0")+"-"+String(d.getDate()).padStart(2,"0")}
function isFolga(d){
  const dt=new Date(d.getFullYear(),d.getMonth(),d.getDate());
  const diff=Math.round((dt-REF)/86400000);
  return ((diff%4)+4)%4>=2;
}

const HOJE=new Date();
const HOJE_KEY=toKey(HOJE);

// ===== Estado + LocalStorage =====
const LS_KEY="turmaA_pierre_state";
const S={
  view:"mensal",
  curMes:HOJE.getMonth(),
  curAno:HOJE.getFullYear(),
  viriatoOpen:false,
  history:[],
  evFilter:[],
};
function saveLS(){
  try{
    localStorage.setItem(LS_KEY,JSON.stringify({
      view:S.view,curMes:S.curMes,curAno:S.curAno,
      evFilter:Array.isArray(S.evFilter)?S.evFilter:[]
    }));
  }catch(e){}
}
function loadLS(){
  try{
    const raw=localStorage.getItem(LS_KEY);
    if(!raw)return;
    const d=JSON.parse(raw);
    if(d.view)S.view=d.view;
    if(typeof d.curMes==="number")S.curMes=d.curMes;
    if(typeof d.curAno==="number")S.curAno=d.curAno;
    if(Array.isArray(d.evFilter))S.evFilter=d.evFilter.filter(t=>EVENTO_TIPOS[t]);
  }catch(e){}
}
loadLS();
function passaFiltroEv(e){
  if(!S.evFilter||!S.evFilter.length)return true;
  const t=e&&e.tipo;
  const efetivo=(t&&EVENTO_TIPOS[t])?t:"outro";
  return S.evFilter.includes(efetivo);
}
function toggleEvFilter(t){
  if(!Array.isArray(S.evFilter))S.evFilter=[];
  const i=S.evFilter.indexOf(t);
  if(i>=0)S.evFilter.splice(i,1);
  else S.evFilter.push(t);
  saveLS();
}
function clearEvFilter(){
  S.evFilter=[];
  saveLS();
}
function tipoEfetivoEv(t){return (t&&EVENTO_TIPOS[t])?t:"outro";}

// ===== Cálculos =====
function diffDias(de,ate){
  const a=new Date(de.getFullYear(),de.getMonth(),de.getDate());
  const b=new Date(ate.getFullYear(),ate.getMonth(),ate.getDate());
  return Math.round((b-a)/86400000);
}
function proxData(predicate){
  for(let i=0;i<60;i++){
    const d=new Date(HOJE);d.setDate(d.getDate()+i);
    if(predicate(d))return d;
  }
  return null;
}
// Lista de próximos eventos (mural + pessoais), respeitando S.evFilter.
// Retorna até `limit` itens dentro dos próximos `maxDias` dias.
function proxEventos(maxDias,limit){
  maxDias=maxDias||60;limit=limit||5;
  const lista=[];
  const seen=new Set();
  const base=new Date(HOJE.getFullYear(),HOJE.getMonth(),HOJE.getDate());
  for(let i=0;i<maxDias;i++){
    const d=new Date(base);d.setDate(base.getDate()+i);
    const k=toKey(d);
    eventosNoDia(k).filter(passaFiltroEv).forEach(e=>{
      const uid=(e._pessoal?"p:":"m:")+(e.id!=null?e.id:e.titulo+"|"+e.data)+"@"+k;
      if(seen.has(uid))return;
      seen.add(uid);
      lista.push({ev:e,dt:d,k});
    });
    if(lista.length>=limit)break;
  }
  return lista.slice(0,limit);
}
function calcResumoAnual(ano){
  let f=0,t=0;
  for(let m=0;m<12;m++){
    const max=new Date(ano,m+1,0).getDate();
    for(let d=1;d<=max;d++){
      const dt=new Date(ano,m,d);
      if(isFolga(dt))f++;else t++;
    }
  }
  return{f,t,total:f+t};
}

// ===== Render Mensal =====
function getLegendOpen(){
  try{return localStorage.getItem("turmaA_legendOpen")==="1";}catch(e){return false;}
}
function setLegendOpen(v){
  try{localStorage.setItem("turmaA_legendOpen",v?"1":"0");}catch(e){}
}
function renderMensal(){
  const ano=S.curAno,mes=S.curMes;
  const primeiro=new Date(ano,mes,1);
  const startOffset=primeiro.getDay();
  const diasMes=new Date(ano,mes+1,0).getDate();
  const diasMesAnt=new Date(ano,mes,0).getDate();
  const filterAtivo=Array.isArray(S.evFilter)&&S.evFilter.length>0;
  const legendOpen=getLegendOpen()||filterAtivo;

  let html=`
    <div class="dss-banner" role="button" tabindex="0" onclick="setSection('dss')" onkeydown="if(event.key==='Enter'||event.key===' '){event.preventDefault();setSection('dss')}">
      <div class="dss-banner-ic"><svg width="24" height="24" fill="none" stroke="currentColor" stroke-width="1.9" viewBox="0 0 24 24"><path d="M12 22s8-4 8-10V5l-8-3-8 3v7c0 6 8 10 8 10z"/><path d="M9 12l2 2 4-4"/></svg></div>
      <div class="dss-banner-txt">
        <div class="dss-banner-tit">Programa Mensal de Aderência ao DSS</div>
      </div>
      <svg class="dss-banner-arrow" width="22" height="22" fill="none" stroke="currentColor" stroke-width="2.2" viewBox="0 0 24 24"><polyline points="9 18 15 12 9 6"/></svg>
    </div>
    <div class="month-bar">
      <div class="month-nav">
        <button class="nav-arrow" id="prevMes" aria-label="Mês anterior">
          <svg width="18" height="18" fill="none" stroke="currentColor" stroke-width="2" viewBox="0 0 24 24"><polyline points="15 18 9 12 15 6"/></svg>
        </button>
        <div class="month-title">${MESES[mes]} ${ano}</div>
        <button class="nav-arrow" id="nextMes" aria-label="Próximo mês">
          <svg width="18" height="18" fill="none" stroke="currentColor" stroke-width="2" viewBox="0 0 24 24"><polyline points="9 18 15 12 9 6"/></svg>
        </button>
      </div>
      <div class="month-actions">
        <button class="btn-legend ${legendOpen?"on":""} ${filterAtivo?"has-filter":""}" id="btnLegend" aria-label="${filterAtivo?'Filtro ativo — abrir legenda':'Legenda das cores dos eventos'}" aria-expanded="${legendOpen?"true":"false"}" aria-controls="calLegend" title="${filterAtivo?'Filtro ativo — toque para ajustar':'Legenda e filtro de tipos'}">?</button>
        <button class="btn-hoje" id="btnHoje">HOJE</button>
      </div>
    </div>
    <div class="cal-wrap">
      <div class="cal-dow">${DOW.map(d=>`<div>${d}</div>`).join("")}</div>
      <div class="cal-grid">`;

  // dias mês anterior
  for(let i=startOffset-1;i>=0;i--){
    const dnum=diasMesAnt-i;
    const dt=new Date(ano,mes-1,dnum);
    const fol=isFolga(dt);
    html+=`<div class="day outside ${fol?"folga":"trab"}"><span class="num">${dnum}</span><span class="lbl">${fol?"FOLGA":"TRAB"}</span></div>`;
  }
  // dias mês atual
  for(let d=1;d<=diasMes;d++){
    const dt=new Date(ano,mes,d);
    const k=toKey(dt);
    const fol=isFolga(dt);
    const today=k===HOJE_KEY;
    const fer=FER[k]?"fer":"";
    const ferNome=FER[k]||"";
    const evs=eventosNoDia(k).filter(passaFiltroEv);
    const evDots=evs.length?`<span class="evs">${evs.slice(0,5).map(e=>`<span class="evdot" style="background:${evTipoInfo(e.tipo).cor}" title="${escapeHtml(evTipoInfo(e.tipo).label)}: ${escapeHtml(e.titulo||"")}"></span>`).join("")}</span>`:"";
    const titParts=[ferNome,...evs.map(e=>`${evTipoInfo(e.tipo).emoji} ${e.titulo||""}`)].filter(Boolean);
    html+=`<div class="day ${fol?"folga":"trab"} ${today?"today":""} ${fer}" data-k="${k}" role="button" tabindex="0" title="${escapeHtml(titParts.join(" • "))}"><span class="num">${d}</span><span class="lbl">${fol?"FOLGA":"TRAB"}</span>${evDots}</div>`;
  }
  // completar grid
  const total=startOffset+diasMes;
  const resto=(7-(total%7))%7;
  for(let i=1;i<=resto;i++){
    const dt=new Date(ano,mes+1,i);
    const fol=isFolga(dt);
    html+=`<div class="day outside ${fol?"folga":"trab"}"><span class="num">${i}</span><span class="lbl">${fol?"FOLGA":"TRAB"}</span></div>`;
  }
  const chipsHtml=Object.entries(EVENTO_TIPOS).map(([key,t])=>{
    const ativo=S.evFilter&&S.evFilter.includes(key);
    const desligado=filterAtivo&&!ativo;
    const cls=`cal-legend-item legend-btn${ativo?" active":""}${desligado?" off":""}`;
    return `<button type="button" class="${cls}" data-tipo="${key}" aria-pressed="${ativo?"true":"false"}" title="${ativo?'Remover filtro: ':'Filtrar por: '}${escapeHtml(t.label)}"><span class="cl-dot" style="background:${t.cor}"></span><span class="cl-emo">${t.emoji}</span><span class="cl-lbl">${escapeHtml(t.label)}</span></button>`;
  }).join("");
  const filterCount=filterAtivo?S.evFilter.length:0;
  const hint=filterAtivo
    ?`<span class="cal-legend-hint">Mostrando ${filterCount} de ${Object.keys(EVENTO_TIPOS).length} tipos</span>`
    :`<span class="cal-legend-hint">Toque em um tipo para filtrar</span>`;
  const clearBtn=filterAtivo?`<button type="button" class="cal-legend-clear" id="calLegendClear" title="Mostrar todos os tipos">Limpar filtro</button>`:"";
  html+=`</div>
    <div class="cal-legend" id="calLegend"${legendOpen?"":" hidden"}>
      <div class="cal-legend-head">
        <div class="cal-legend-tit">Cores dos eventos</div>
        ${hint}
        ${clearBtn}
      </div>
      <div class="cal-legend-items">
        ${chipsHtml}
      </div>
    </div>
  </div>`;
  // Caixa "ESTA SEMANA" — 7 dias da semana corrente
  {
    const dow=HOJE.getDay();
    const ws=new Date(HOJE);ws.setDate(HOJE.getDate()-dow);
    let wk=`<div class="week-box"><div class="week-tit">ESTA SEMANA</div><div class="week-grid">`;
    for(let i=0;i<7;i++){
      const dt=new Date(ws);dt.setDate(ws.getDate()+i);
      const fol=isFolga(dt);
      const today=toKey(dt)===HOJE_KEY;
      wk+=`<div class="wk ${fol?"folga":"trab"} ${today?"today":""}"><span class="wd">${DOW[i]}</span><span class="wn">${dt.getDate()}</span><span class="wl">${fol?"FOLGA":"TRAB"}</span></div>`;
    }
    wk+=`</div></div>`;
    html+=wk;
  }
  // Banner reflexivo do Viriato (logo abaixo do calendario, com botao integrado)
  html+=`<div class="viriato-banner" id="viriatoBanner">
    <button class="vb-bot" id="vbOpenViriato" aria-label="Abrir Viriato" title="Falar com o Viriato">🤖</button>
    <span class="vb-txt"><i>Vc Já viu como é Linda a Vista da Lagoa Mapaúra, pela Janela de Uma Locomotiva?</i></span>
    <button class="vb-close" id="vbClose" aria-label="Fechar">×</button>
  </div>`;
  return html;
}

// ===== Render Anual =====
function renderAnual(){
  const ano=S.curAno;
  let html=`<div class="month-bar">
    <div class="month-nav">
      <button class="nav-arrow" id="prevAno" aria-label="Ano anterior">
        <svg width="18" height="18" fill="none" stroke="currentColor" stroke-width="2" viewBox="0 0 24 24"><polyline points="15 18 9 12 15 6"/></svg>
      </button>
      <div class="month-title">${ano}</div>
      <button class="nav-arrow" id="nextAno" aria-label="Próximo ano">
        <svg width="18" height="18" fill="none" stroke="currentColor" stroke-width="2" viewBox="0 0 24 24"><polyline points="9 18 15 12 9 6"/></svg>
      </button>
    </div>
    <button class="btn-hoje" id="btnHoje">HOJE</button>
  </div><div class="year-wrap">`;
  for(let m=0;m<12;m++){
    const primeiro=new Date(ano,m,1);
    const offset=primeiro.getDay();
    const dias=new Date(ano,m+1,0).getDate();
    let cells="";
    for(let i=0;i<offset;i++)cells+=`<div class="mini-day outside"></div>`;
    for(let d=1;d<=dias;d++){
      const dt=new Date(ano,m,d);
      const k=toKey(dt);
      const fol=isFolga(dt);
      const today=k===HOJE_KEY?"today":"";
      cells+=`<div class="mini-day ${fol?"folga":"trab"} ${today}" data-k="${k}" role="button" tabindex="0">${d}</div>`;
    }
    html+=`<div class="mini-mes">
      <h4>${MESES3[m]}</h4>
      <div class="mini-dow">${DOW_MINI.map(x=>`<span>${x}</span>`).join("")}</div>
      <div class="mini-grid">${cells}</div>
    </div>`;
  }
  html+=`</div>`;
  return html;
}

// ===== Render Painel direito =====
function renderRight(){
  const fol=isFolga(HOJE);
  const dataStr=HOJE.getDate().toString().padStart(2,"0")+" "+MESES3[HOJE.getMonth()]+" "+HOJE.getFullYear();
  const dow=DOW_FULL[HOJE.getDay()];
  // Próximo dia de trabalho/folga (a partir de amanhã)
  const proxTrabReal=proxData(d=>toKey(d)!==HOJE_KEY && !isFolga(d));
  const proxFolga=proxData(d=>toKey(d)!==HOJE_KEY && isFolga(d));

  const ptDias=proxTrabReal?diffDias(HOJE,proxTrabReal):0;
  const pfDias=proxFolga?diffDias(HOJE,proxFolga):0;

  const resumo=calcResumoAnual(S.curAno);
  const pctF=Math.round(resumo.f/resumo.total*100);
  const pctT=100-pctF;

  // Lista de próximos eventos (mural + pessoais), respeitando o filtro do calendário
  const filterAtivoR=Array.isArray(S.evFilter)&&S.evFilter.length>0;
  const proxEvs=proxEventos(60,5);
  const filterHintR=filterAtivoR
    ?`<div class="panel-filter-hint"><span>🔎 Filtro ativo (${S.evFilter.length}/${Object.keys(EVENTO_TIPOS).length})</span><button type="button" id="rightClearFilter" title="Mostrar todos os tipos">Limpar</button></div>`
    :"";
  const proxEvsHtml=proxEvs.length
    ? proxEvs.map(({ev,dt,k})=>{
        const ti=evTipoInfo(ev.tipo);
        const dias=diffDias(HOJE,dt);
        const diasLbl=dias===0?"HOJE":dias===1?"AMANHÃ":dias+" DIAS";
        const dataLbl=dt.getDate().toString().padStart(2,"0")+" "+MESES3[dt.getMonth()];
        const pessTag=ev._pessoal?'<span class="ev-priv" title="Evento pessoal">🔒</span>':"";
        return `<div class="prox-ev-row" data-k="${k}" role="button" tabindex="0" title="${escapeHtml(ti.label)}: ${escapeHtml(ev.titulo||"")}">
          <span class="prox-ev-dot" style="background:${ti.cor}"></span>
          <div class="prox-ev-info">
            <div class="prox-ev-tit">${ti.emoji} ${escapeHtml(ev.titulo||ti.label)} ${pessTag}</div>
            <div class="prox-ev-data">${dataLbl} · ${diasLbl}</div>
          </div>
        </div>`;
      }).join("")
    : `<div class="prox-ev-empty">${filterAtivoR?"Nenhum evento futuro com este filtro.":"Nenhum evento futuro nos próximos 60 dias."}</div>`;

  return `
    <div class="panel">
      <div class="panel-tit">Status Hoje</div>
      <div class="status-row">
        <div class="status-icon ${fol?"folga":"trab"}">${fol?"🌙":"☀️"}</div>
        <div>
          <div class="status-tipo ${fol?"folga":"trab"}">${fol?"FOLGA":"TRABALHO"}</div>
          <div class="status-data">${dow} · ${dataStr}</div>
        </div>
      </div>
    </div>

    <div class="panel">
      <div class="panel-tit">Próximos Eventos</div>
      <div class="event-row">
        <div class="ev-info">
          <span class="ev-tipo">Próx. Trabalho</span>
          <span class="ev-data">${proxTrabReal?proxTrabReal.getDate().toString().padStart(2,"0")+" "+MESES3[proxTrabReal.getMonth()]:"—"}</span>
        </div>
        <div class="ev-count trab">${ptDias}<small>DIAS</small></div>
      </div>
      <div class="event-row">
        <div class="ev-info">
          <span class="ev-tipo">Próx. Folga</span>
          <span class="ev-data">${proxFolga?proxFolga.getDate().toString().padStart(2,"0")+" "+MESES3[proxFolga.getMonth()]:"—"}</span>
        </div>
        <div class="ev-count folga">${pfDias}<small>DIAS</small></div>
      </div>
      <div class="prox-ev-sep">Compromissos</div>
      ${filterHintR}
      <div class="prox-ev-list">${proxEvsHtml}</div>
    </div>

    <div class="panel">
      <div class="panel-tit">Resumo ${S.curAno}</div>
      <div class="resumo-grid">
        <div class="resumo-cell t"><div class="v">${resumo.t}</div><div class="l">Trabalho</div></div>
        <div class="resumo-cell f"><div class="v">${resumo.f}</div><div class="l">Folga</div></div>
      </div>
      <div class="resumo-bar">
        <div class="b-t" style="width:${pctT}%"></div>
        <div class="b-f" style="width:${pctF}%"></div>
      </div>
      <div class="resumo-leg">
        <span>${pctT}% TRAB</span>
        <span>TOTAL ${resumo.total}</span>
        <span>${pctF}% FOLGA</span>
      </div>
    </div>

    <div class="panel legal-panel">
      <div class="panel-tit">Documentos</div>
      <div class="legal-links">
        <a href="/termos-de-uso.html">Termos de Uso</a>
        <a href="/politica-de-seguranca.html">Segurança e Privacidade</a>
      </div>
    </div>
  `;
}

// ===== Render geral =====
function render(){
  const c=document.getElementById("content");
  if(S.section && S.section!=="calendario"){
    document.getElementById("rightPanel").style.display="none";
    if(S.section==="eventos")renderEventos(c);
    else if(S.section==="dss")renderDSS(c);
    else if(S.section==="pessoais")renderPessoais(c);
    else if(S.section==="diario")renderDiario(c);
    else if(S.section==="acervo")renderAcervo(c);
    else if(S.section==="chat")renderChat(c);
    else if(S.section==="viriato")renderViriatoFull(c);
    return;
  }
  document.getElementById("rightPanel").style.display="";
  c.innerHTML=S.view==="mensal"?renderMensal():renderAnual();
  document.getElementById("rightPanel").innerHTML=renderRight();
  attachViriatoBanner();
  if(CURRENT_USER){
    carregarEventosCache().then(()=>{
      if(S.section==="calendario"||!S.section){
        const c2=document.getElementById("content");
        if(c2)c2.innerHTML=S.view==="mensal"?renderMensal():renderAnual();
        const rp=document.getElementById("rightPanel");
        if(rp)rp.innerHTML=renderRight();
        bindCalNav();
        attachViriatoBanner();
      }
    });
  }

  // tabs
  document.querySelectorAll(".tab").forEach(t=>{
    t.classList.toggle("active",t.dataset.view===S.view);
  });

  bindCalNav();
}
function bindCalNav(){
  const pm=document.getElementById("prevMes");
  if(pm)pm.onclick=()=>{S.curMes--;if(S.curMes<0){S.curMes=11;S.curAno--;}saveLS();render();};
  const nm=document.getElementById("nextMes");
  if(nm)nm.onclick=()=>{S.curMes++;if(S.curMes>11){S.curMes=0;S.curAno++;}saveLS();render();};
  const pa=document.getElementById("prevAno");
  if(pa)pa.onclick=()=>{S.curAno--;saveLS();render();};
  const na=document.getElementById("nextAno");
  if(na)na.onclick=()=>{S.curAno++;saveLS();render();};
  const bh=document.getElementById("btnHoje");
  if(bh)bh.onclick=()=>{S.curMes=HOJE.getMonth();S.curAno=HOJE.getFullYear();saveLS();render();};
  const bl=document.getElementById("btnLegend");
  const lg=document.getElementById("calLegend");
  if(bl&&lg)bl.onclick=()=>{
    const open=lg.hasAttribute("hidden");
    if(open){lg.removeAttribute("hidden");bl.classList.add("on");bl.setAttribute("aria-expanded","true");}
    else{lg.setAttribute("hidden","");bl.classList.remove("on");bl.setAttribute("aria-expanded","false");}
    setLegendOpen(open);
  };
  document.querySelectorAll(".legend-btn[data-tipo]").forEach(b=>{
    b.addEventListener("click",(e)=>{
      e.preventDefault();
      const t=b.dataset.tipo;
      if(!EVENTO_TIPOS[t])return;
      toggleEvFilter(t);
      setLegendOpen(true);
      render();
    });
  });
  const cc=document.getElementById("calLegendClear");
  if(cc)cc.onclick=(e)=>{e.preventDefault();clearEvFilter();render();};
  const rcf=document.getElementById("rightClearFilter");
  if(rcf)rcf.onclick=(e)=>{e.preventDefault();clearEvFilter();render();};
  document.querySelectorAll(".prox-ev-row[data-k]").forEach(r=>{
    r.onclick=()=>openDia(r.dataset.k);
    r.onkeydown=(e)=>{if(e.key==="Enter"||e.key===" "){e.preventDefault();openDia(r.dataset.k);}};
  });
  document.querySelectorAll(".mini-day[data-k],.day[data-k]").forEach(d=>{
    d.style.cursor="pointer";
    d.onclick=()=>openDia(d.dataset.k);
    d.onkeydown=(e)=>{if(e.key==="Enter"||e.key===" "){e.preventDefault();openDia(d.dataset.k);}};
  });
}

document.querySelectorAll(".tab").forEach(t=>{
  t.addEventListener("click",()=>{
    S.view=t.dataset.view;S.section="calendario";
    document.querySelectorAll(".mp-item[data-sec]").forEach(b=>b.classList.toggle("active",b.dataset.sec==="calendario"));
    saveLS();render();
  });
});

// ===== Tema claro/escuro =====
function applyTheme(t){
  document.documentElement.setAttribute("data-theme",t);
  try{localStorage.setItem("turmaA_theme",t);}catch(e){}
}
applyTheme(localStorage.getItem("turmaA_theme")||"dark");
document.getElementById("themeToggle").addEventListener("click",()=>{
  const cur=document.documentElement.getAttribute("data-theme")||"dark";
  applyTheme(cur==="dark"?"light":"dark");
});
// Banner reflexivo do Viriato — attach handlers a cada render do calendario
function attachViriatoBanner(){
  const banner=document.getElementById("viriatoBanner");
  if(!banner){document.body.classList.remove("banner-visible");return;}
  try{localStorage.removeItem("turmaA_vbHidden");}catch(e){}
  document.body.classList.add("banner-visible");
  const cls=document.getElementById("vbClose");
  if(cls)cls.onclick=()=>{
    banner.classList.add("hidden");
    document.body.classList.remove("banner-visible");
  };
  const ob=document.getElementById("vbOpenViriato");
  if(ob)ob.onclick=()=>{setSection("viriato");};
}

// ===== Viriato em tela cheia (aba dedicada) =====
function renderViriatoFull(c){
  const msgs=S.history.length?S.history:[{role:"assistant",content:"Olá! Sou o Viriato, assistente ferroviário. Como posso ajudar?"}];
  c.innerHTML=`
    <div class="viriato-full">
      <div class="vf-head">
        <button class="vf-back" id="vfBack" aria-label="Voltar ao menu" title="Voltar ao menu">
          <svg width="20" height="20" fill="none" stroke="currentColor" stroke-width="2.2" viewBox="0 0 24 24"><polyline points="15 18 9 12 15 6"/></svg>
        </button>
        <div class="vf-avatar">🤖</div>
        <div style="flex:1;min-width:0">
          <div class="vf-name">VIRIATO</div>
          <div class="vf-sub">Assistente Ferroviário</div>
        </div>
        <button class="vf-clear" id="vfClear" title="Limpar conversa">🗑️</button>
      </div>
      <div class="vf-body" id="vfBody">
        ${msgs.map((m,i)=>{
          const isLastBot=m.role==="assistant"&&i===msgs.length-1;
          const pdfBtn=isLastBot&&S._pendingPdf?`<button class="vf-pdf-btn" id="vfPdfDl">📄 Baixar PDF</button>`:"";
          return `<div class="msg ${m.role==="user"?"user":"bot"}">${escapeHtml(m.content)}${pdfBtn}</div>`;
        }).join("")}
        ${S.viriatoTyping?'<div class="msg bot typing">Viriato digitando…</div>':""}
      </div>
      <div class="vf-input">
        <textarea id="vfInput" placeholder="Digite sua mensagem para o Viriato…" rows="2"></textarea>
        <button class="vf-send" id="vfSend" aria-label="Enviar">➤</button>
      </div>
    </div>`;
  const inp=document.getElementById("vfInput");
  const send=document.getElementById("vfSend");
  const body=document.getElementById("vfBody");
  body.scrollTop=body.scrollHeight;
  setTimeout(()=>inp&&inp.focus(),50);
  document.getElementById("vfBack").onclick=()=>setSection("calendario");
  document.getElementById("vfClear").onclick=()=>{
    if(confirm("Limpar toda a conversa com o Viriato?")){S.history=[];S._pendingPdf=null;renderViriatoFull(c);}
  };
  const pdfDl=document.getElementById("vfPdfDl");
  if(pdfDl&&S._pendingPdf){
    pdfDl.onclick=()=>{downloadViriatoPdf(S._pendingPdf);S._pendingPdf=null;};
  }
  const doSend=async()=>{
    const txt=(inp.value||"").trim();
    if(!txt||S.viriatoTyping)return;
    S.history.push({role:"user",content:txt});
    inp.value="";
    S.viriatoTyping=true;
    renderViriatoFull(c);
    try{
      const token=localStorage.getItem("turmaA_authToken")||"";
      const headers={"Content-Type":"application/json"};
      if(token)headers["Authorization"]="Bearer "+token;
      const conversation_history=S.history.slice(0,-1).map(m=>({role:m.role,content:m.content}));
      const messages=conversation_history.concat([{role:"user",content:txt}]);
      const r=await fetch("/api/claude",{method:"POST",headers,body:JSON.stringify({message:txt,conversation_history,messages})});
      if(r.status===401){
        localStorage.removeItem("turmaA_authToken");
        S.history.push({role:"assistant",content:"Sessão expirada. Faça login no app para continuar nossa conversa."});
      }else{
        const d=await r.json();
        const reply=d.text||d.reply||d.error||"Sem resposta.";
        S.history.push({role:"assistant",content:reply});
        if(d.memoria_salva && d.memoria_salva.length){
          const pe=d.memoria_salva.filter(x=>x.status==="pendente").length;
          const ok=d.memoria_salva.length-pe;
          if(ok)showToast("✅ "+ok+" item(s) salvo(s) na memória");
          if(pe)showToast("⏳ "+pe+" sugestão(ões) enviada(s) para aprovação do admin");
        }
        if(d.eventos_criados && d.eventos_criados.length){
          showToast("📅 "+d.eventos_criados.length+" evento(s) adicionado(s) à agenda");
          await carregarEventosCache();
        }
        if(d.pdf && d.pdf.titulo && d.pdf.conteudo){
          S._pendingPdf=d.pdf;
        }
      }
    }catch(e){S.history.push({role:"assistant",content:"Erro de conexão: "+e.message});}
    S.viriatoTyping=false;
    renderViriatoFull(c);
  };
  send.onclick=doSend;
  inp.addEventListener("keydown",e=>{
    if(e.key==="Enter"&&!e.shiftKey){e.preventDefault();doSend();}
  });
}

async function downloadViriatoPdf(pdf){
  try{
    const token=getToken();
    const r=await fetch("/api/gerar-pdf",{
      method:"POST",
      headers:{"Content-Type":"application/json","Authorization":"Bearer "+token},
      body:JSON.stringify({titulo:pdf.titulo,conteudo:pdf.conteudo})
    });
    if(!r.ok){const d=await r.json().catch(()=>({}));showToast("❌ "+(d.error||"Erro ao gerar PDF"));return;}
    const blob=await r.blob();
    const url=URL.createObjectURL(blob);
    const a=document.createElement("a");
    a.href=url;
    a.download=r.headers.get("content-disposition")?.split("filename=")[1]?.replace(/"/g,"")||"viriato.pdf";
    document.body.appendChild(a);
    a.click();
    document.body.removeChild(a);
    URL.revokeObjectURL(url);
    showToast("📄 PDF baixado!");
  }catch(e){showToast("❌ Erro: "+e.message);}
}

// ===== Viriato =====
function renderViriato(){
  const w=document.getElementById("viriatoWin");
  if(!S.viriatoOpen){w.innerHTML="";return;}
  const msgs=S.history.length?S.history:[{role:"assistant",content:"Olá! Sou o Viriato, assistente ferroviário. Como posso ajudar?"}];
  w.innerHTML=`
    <div class="viriato-win">
      <div class="vw-head">
        <div class="vw-avatar">🤖</div>
        <div>
          <div class="vw-name">VIRIATO</div>
          <div class="vw-sub">Assistente Ferroviário</div>
        </div>
        <button class="vw-close" id="vwClose" aria-label="Fechar">
          <svg width="14" height="14" fill="none" stroke="currentColor" stroke-width="2.4" viewBox="0 0 24 24"><line x1="18" y1="6" x2="6" y2="18"/><line x1="6" y1="6" x2="18" y2="18"/></svg>
        </button>
      </div>
      <div class="vw-body" id="vwBody">
        ${msgs.map(m=>`<div class="msg ${m.role==="user"?"user":"bot"}">${escapeHtml(m.content)}</div>`).join("")}
        ${S.viriatoTyping?'<div class="msg bot typing">Viriato digitando…</div>':""}
      </div>
      <div class="vw-input" style="position:relative">
        <button class="vw-plus" id="vwPlus" title="Anexar / opções" style="background:#161a22;border:1px solid var(--border);color:var(--text);width:34px;height:34px;border-radius:8px;cursor:pointer;font-size:18px;font-weight:600">+</button>
        <input id="vwInput" type="text" placeholder="Digite sua mensagem…" autocomplete="off"/>
        <button class="vw-send" id="vwSend">➤</button>
        <div id="vwPlusPop" style="display:none;position:absolute;bottom:48px;left:8px;background:#0e1117;border:1px solid var(--border);border-radius:10px;padding:6px;z-index:5;box-shadow:0 12px 30px #000a;min-width:180px">
          <button data-act="doc" class="vp-opt">📄 Documento (PDF/DOCX)</button>
          <button data-act="temp" class="vp-opt">⏱️ Documento TEMP</button>
          <button data-act="img" class="vp-opt">🖼️ Imagem</button>
          <button data-act="cam" class="vp-opt">📷 Câmera</button>
          <button data-act="clear" class="vp-opt" style="color:#ff8a8a">🗑️ Limpar conversa</button>
        </div>
      </div>
    </div>`;
  document.getElementById("vwClose").onclick=()=>{S.viriatoOpen=false;renderViriato();};
  const inp=document.getElementById("vwInput");
  const send=document.getElementById("vwSend");
  inp.focus();
  const body=document.getElementById("vwBody");
  body.scrollTop=body.scrollHeight;
  const doSend=async()=>{
    const txt=inp.value.trim();
    if(!txt||S.viriatoTyping)return;
    S.history.push({role:"user",content:txt});
    inp.value="";
    S.viriatoTyping=true;
    renderViriato();
    try{
      const token=localStorage.getItem("turmaA_authToken")||"";
      const headers={"Content-Type":"application/json"};
      if(token)headers["Authorization"]="Bearer "+token;
      const conversation_history=S.history.slice(0,-1).map(m=>({role:m.role,content:m.content}));
      const messages=conversation_history.concat([{role:"user",content:txt}]);
      const r=await fetch("/api/claude",{
        method:"POST",
        headers,
        body:JSON.stringify({
          message:txt,
          conversation_history,
          messages
        })
      });
      if(r.status===401){
        localStorage.removeItem("turmaA_authToken");
        S.history.push({role:"assistant",content:"Sessão expirada. Faça login no app para continuar nossa conversa."});
      }else{
        const d=await r.json();
        const reply=d.text||d.reply||d.error||"Sem resposta.";
        S.history.push({role:"assistant",content:reply});
        if(d.memoria_salva && d.memoria_salva.length){
          const pe=d.memoria_salva.filter(x=>x.status==="pendente").length;
          const ok=d.memoria_salva.length-pe;
          if(ok)showToast("✅ "+ok+" item(s) salvo(s) na memória");
          if(pe)showToast("⏳ "+pe+" sugestão(ões) enviada(s) para aprovação do admin");
        }
        if(d.eventos_criados && d.eventos_criados.length){
          showToast("📅 "+d.eventos_criados.length+" evento(s) adicionado(s) à agenda");
          await carregarEventosCache();
        }
      }
    }catch(e){
      S.history.push({role:"assistant",content:"Erro de conexão: "+e.message});
    }
    S.viriatoTyping=false;
    renderViriato();
  };
  send.onclick=doSend;
  inp.addEventListener("keydown",e=>{if(e.key==="Enter")doSend();});
}
function escapeHtml(s){return String(s).replace(/[&<>"']/g,c=>({"&":"&amp;","<":"&lt;",">":"&gt;","\"":"&quot;","'":"&#39;"}[c]));}

// ===== FAB do Viriato: clicavel + arrastavel =====
(function(){
  const fab=document.getElementById("viriatoBtn");
  if(!fab)return;
  // Aplica posicao salva
  function applySavedPos(){
    try{
      const raw=localStorage.getItem("turmaA_fabPos");
      if(!raw)return;
      const p=JSON.parse(raw);
      if(typeof p.left==="number"&&typeof p.top==="number"){
        const m=44;
        const maxL=window.innerWidth-fab.offsetWidth-8;
        const maxT=window.innerHeight-fab.offsetHeight-8;
        const L=Math.min(Math.max(8,p.left),maxL);
        const T=Math.min(Math.max(8,p.top),maxT);
        fab.style.left=L+"px";
        fab.style.top=T+"px";
        fab.style.right="auto";
        fab.style.bottom="auto";
        fab.style.transform="none";
      }
    }catch(e){}
  }
  applySavedPos();
  window.addEventListener("resize",applySavedPos);

  let dragging=false, moved=false, startX=0, startY=0, origL=0, origT=0;
  const TH=6; // px threshold para considerar drag

  fab.addEventListener("pointerdown",(e)=>{
    if(e.button!==undefined&&e.button!==0)return;
    dragging=true;moved=false;
    const r=fab.getBoundingClientRect();
    origL=r.left;origT=r.top;
    startX=e.clientX;startY=e.clientY;
    fab.setPointerCapture&&fab.setPointerCapture(e.pointerId);
    fab.classList.add("dragging");
  });
  fab.addEventListener("pointermove",(e)=>{
    if(!dragging)return;
    const dx=e.clientX-startX, dy=e.clientY-startY;
    if(!moved && (Math.abs(dx)>TH||Math.abs(dy)>TH))moved=true;
    if(moved){
      const w=fab.offsetWidth, h=fab.offsetHeight;
      let L=origL+dx, T=origT+dy;
      L=Math.min(Math.max(8,L),window.innerWidth-w-8);
      T=Math.min(Math.max(8,T),window.innerHeight-h-8);
      fab.style.left=L+"px";
      fab.style.top=T+"px";
      fab.style.right="auto";
      fab.style.bottom="auto";
      fab.style.transform="none";
    }
  });
  function endDrag(e){
    if(!dragging)return;
    dragging=false;
    fab.classList.remove("dragging");
    try{fab.releasePointerCapture&&fab.releasePointerCapture(e.pointerId);}catch(_){}
    if(moved){
      const r=fab.getBoundingClientRect();
      try{localStorage.setItem("turmaA_fabPos",JSON.stringify({left:r.left,top:r.top}));}catch(_){}
    }else{
      // clique real - abre Viriato em tela dedicada
      setSection("viriato");
    }
    moved=false;
  }
  fab.addEventListener("pointerup",endDrag);
  fab.addEventListener("pointercancel",endDrag);
  // bloqueia o click sintetico apos drag (alguns navegadores)
  fab.addEventListener("click",(e)=>{if(moved){e.preventDefault();e.stopPropagation();}});
})();

// =====================================================
// ===== RELIGAÇÃO: navegação, login, modal, eventos, acervo, setup, viriato +
// =====================================================

// ----- estilos de apoio (injetados) -----
(function injectCSS(){
  const css=`
    .vp-opt{display:block;width:100%;text-align:left;background:transparent;border:0;color:var(--text);padding:8px 10px;border-radius:6px;cursor:pointer;font-size:13px}
    .vp-opt:hover{background:#171b24}
    .toast{position:fixed;bottom:90px;left:50%;transform:translateX(-50%);background:#0e1117;color:var(--text);padding:10px 16px;border:1px solid var(--border);border-radius:24px;z-index:300;box-shadow:0 12px 30px #000a;font-size:13px;animation:tFade .3s ease}
    @keyframes tFade{from{opacity:0;transform:translate(-50%,8px)}to{opacity:1;transform:translate(-50%,0)}}
    .modal-fld{display:flex;flex-direction:column;gap:6px;margin-bottom:12px}
    .modal-fld label{font-size:11px;color:var(--muted);letter-spacing:.5px;text-transform:uppercase}
    .modal-fld input,.modal-fld textarea,.modal-fld select{background:#0f1117;border:1px solid var(--border);border-radius:8px;padding:10px;color:var(--text);font-size:14px;font-family:inherit}
    [data-theme="light"] .modal-fld input,[data-theme="light"] .modal-fld textarea,[data-theme="light"] .modal-fld select{background:#fff;color:var(--text)}
    .btn-primary{background:var(--neon);color:#000;border:0;border-radius:8px;padding:10px 14px;font-weight:700;cursor:pointer;font-size:13px;letter-spacing:.5px}
    .btn-secondary{background:#161a22;color:var(--text);border:1px solid var(--border);border-radius:8px;padding:10px 14px;cursor:pointer;font-size:13px}
    [data-theme="light"] .btn-secondary{background:#f1f5f9}
    .btn-danger{background:#3a1414;color:#ff8a8a;border:1px solid #5a1f1f;border-radius:8px;padding:8px 12px;cursor:pointer;font-size:12px}
    .lst-item{background:#0f1117;border:1px solid var(--border);border-radius:10px;padding:12px;margin-bottom:8px;display:flex;justify-content:space-between;gap:10px;align-items:flex-start}
    [data-theme="light"] .lst-item{background:#fff}
    .pg-head{display:flex;justify-content:space-between;align-items:center;padding:18px 24px 10px;border-bottom:1px solid var(--border)}
    .pg-tit{font-size:18px;font-weight:600;letter-spacing:.5px}
    .pg-body{padding:18px 24px;overflow:auto;height:calc(100vh - 130px)}
    .tabs-mini{display:flex;gap:6px;margin-bottom:14px}
    .tabs-mini button{background:#0f1117;border:1px solid var(--border);color:var(--muted);padding:7px 14px;border-radius:8px;cursor:pointer;font-size:12px;letter-spacing:.5px}
    .tabs-mini button.active{background:var(--neon);color:#000;border-color:var(--neon);font-weight:700}

    /* === FIX MODO CLARO: classes que ficaram com fundo escuro hardcoded === */
    [data-theme="light"] .toast{background:#ffffff;color:#0f172a;border-color:#cbd5e1;box-shadow:0 8px 24px #0f172a22}
    [data-theme="light"] .vp-opt{color:#0f172a}
    [data-theme="light"] .vp-opt:hover{background:#f1f5f9;color:#0f172a}
    [data-theme="light"] .tabs-mini button{background:#f8fafc;color:#475569;border-color:#cbd5e1}
    [data-theme="light"] .tabs-mini button.active{background:var(--neon);color:#ffffff;border-color:var(--neon)}
    [data-theme="light"] .btn-danger{background:#fee2e2;color:#991b1b;border-color:#fca5a5}
    [data-theme="light"] .btn-legend,[data-theme="light"] .theme-toggle{background:var(--card)}
    [data-theme="light"] .wk{background:#f1f5f9;border-color:#cbd5e1}
    [data-theme="light"] .wk .wn{color:#0f172a}
    /* popups e caixas internas que vivem dentro dos modais admin (Viriato) */
    /* !important pq o elemento é criado inline com background:#0e1117 hardcoded em renderViriato() */
    [data-theme="light"] #vwPlusPop{background:#ffffff !important;border-color:#cbd5e1 !important;box-shadow:0 12px 30px #0f172a22 !important}
  `;
  const s=document.createElement("style");s.textContent=css;document.head.appendChild(s);
})();

// ----- toast -----
function showToast(msg,ms=3500){
  const t=document.createElement("div");t.className="toast";t.textContent=msg;
  document.body.appendChild(t);
  setTimeout(()=>{t.style.opacity="0";t.style.transition="opacity .3s";setTimeout(()=>t.remove(),300);},ms);
}

// ----- auth helpers -----
function getToken(){return localStorage.getItem("turmaA_authToken")||"";}
function setToken(t){if(t)localStorage.setItem("turmaA_authToken",t);else localStorage.removeItem("turmaA_authToken");}
let CURRENT_USER=null;
const REACTION_EMOJIS=["👍","❤️","😂","😮","🎉","🙏","👏","🚂"];
async function apiFetch(path,opts={}){
  const headers=Object.assign({},opts.headers||{});
  const t=getToken();
  if(t)headers["Authorization"]="Bearer "+t;
  if(opts.body && !headers["Content-Type"])headers["Content-Type"]="application/json";
  const r=await fetch(path,Object.assign({},opts,{headers}));
  if(r.status===401){setToken("");CURRENT_USER=null;openLogin();throw new Error("auth");}
  if(r.status===428){
    const d=await r.json().catch(()=>({}));
    if(d.error==="legal_acceptance_required"){
      if(CURRENT_USER)CURRENT_USER.legal_acceptance_required=true;
      openLegalAcceptanceModal(d);
      throw new Error("auth");
    }
  }
  return r;
}
async function loadMe(){
  if(!getToken())return null;
  try{
    const r=await fetch("/api/auth/me",{headers:{"Authorization":"Bearer "+getToken()}});
    if(r.ok){
      const d=await r.json();
      if(d && d.authenticated===false){setToken("");CURRENT_USER=null;return null;}
      CURRENT_USER=d.user||d;
      if(CURRENT_USER&&CURRENT_USER.legal_acceptance_required)setTimeout(()=>openLegalAcceptanceModal(CURRENT_USER),80);
      return CURRENT_USER;
    }
  }catch(e){}
  setToken("");CURRENT_USER=null;return null;
}

// ----- modal genérico -----
function openModal(title,bodyHtml,onMount){
  closeModal();
  const m=document.createElement("div");
  m.id="appModal";
  m.style.cssText="position:fixed;inset:0;background:#000a;backdrop-filter:blur(4px);z-index:200;display:flex;align-items:center;justify-content:center;padding:20px";
  m.innerHTML=`<div style="background:var(--card);border:1px solid var(--border);border-radius:14px;max-width:560px;width:100%;max-height:90vh;overflow:auto;padding:22px;color:var(--text)">
    <div style="display:flex;justify-content:space-between;align-items:center;margin-bottom:14px;border-bottom:1px solid var(--border);padding-bottom:10px">
      <h3 style="margin:0;font-size:18px;letter-spacing:.5px">${escapeHtml(title)}</h3>
      <button id="mdClose" style="background:none;border:0;color:var(--muted);cursor:pointer;font-size:26px;line-height:1">×</button>
    </div>
    <div id="mdBody">${bodyHtml}</div>
  </div>`;
  document.body.appendChild(m);
  document.getElementById("mdClose").onclick=closeModal;
  m.addEventListener("click",e=>{if(e.target===m)closeModal();});
  if(onMount)onMount(document.getElementById("mdBody"));
}
function closeModal(){const m=document.getElementById("appModal");if(m)m.remove();}

// ----- LOGIN -----
function openLogin(){
  openModal("Entrar",`
    <div class="modal-fld"><label>Matrícula (6 a 10 dígitos)</label><input id="loginMat" inputmode="numeric" maxlength="10" autocomplete="username"/></div>
    <div class="modal-fld"><label>Senha (4 dígitos)</label><input id="loginSen" type="password" inputmode="numeric" maxlength="4" autocomplete="current-password"/></div>
    <button id="loginBtn" class="btn-primary" style="width:100%">ENTRAR</button>
    <div id="loginMsg" style="color:#ff6b6b;font-size:12px;text-align:center;min-height:14px;margin-top:10px"></div>
    <div style="text-align:center;margin-top:10px;font-size:11px;color:var(--muted);line-height:1.45">
      Ao entrar, você aceita os <a href="/termos-de-uso.html" style="color:var(--neon)">Termos de Uso</a>
      e a <a href="/politica-de-seguranca.html" style="color:var(--neon)">Política de Segurança</a>.
    </div>
    <div style="text-align:center;margin-top:14px;font-size:12px;color:var(--muted)">
      Não tem conta? <a href="#" id="goReg" style="color:var(--neon)">Cadastrar-se</a>
    </div>
  `,()=>{
    const go=async()=>{
      const m=document.getElementById("loginMat").value.trim();
      const s=document.getElementById("loginSen").value.trim();
      const msg=document.getElementById("loginMsg");
      msg.textContent="Entrando...";
      try{
        const r=await fetch("/api/auth/login",{method:"POST",headers:{"Content-Type":"application/json"},body:JSON.stringify({matricula:m,senha:s})});
        const d=await r.json();
        if(r.ok && d.token){
          setToken(d.token);CURRENT_USER=d.user||null;closeModal();
          render();  // re-renderiza a home no estado logado (senao o banner/eventos ficam do estado pre-login)
          if(CURRENT_USER&&CURRENT_USER.legal_acceptance_required)openLegalAcceptanceModal(CURRENT_USER);
          else showToast("✅ Bem-vindo, "+(CURRENT_USER&&CURRENT_USER.nome||"colega"));
        }
        else msg.textContent=d.error||"Falha no login";
      }catch(e){msg.textContent="Erro: "+e.message;}
    };
    document.getElementById("loginBtn").onclick=go;
    document.getElementById("loginSen").addEventListener("keydown",e=>{if(e.key==="Enter")go();});
    document.getElementById("loginMat").focus();
    document.getElementById("goReg").onclick=e=>{e.preventDefault();openRegistro();};
  });
}
function openRegistro(){
  openModal("Criar conta",`
    <div class="modal-fld"><label>Nome completo</label><input id="rgNome"/></div>
    <div class="modal-fld"><label>Matrícula (6 a 10 dígitos)</label><input id="rgMat" inputmode="numeric" maxlength="10"/></div>
    <div class="modal-fld"><label>Função</label><select id="rgFun"><option value="">— selecione —</option><option value="Função Operacional">Função Operacional</option><option value="Função Administrativa">Função Administrativa</option></select></div>
    <div class="modal-fld"><label>E-mail (opcional)</label><input id="rgEmail" type="email"/></div>
    <div class="modal-fld"><label>Senha (4 dígitos)</label><input id="rgSen" type="password" inputmode="numeric" maxlength="4"/></div>
    <label style="display:flex;gap:8px;align-items:flex-start;font-size:12px;color:var(--muted);line-height:1.45;margin:-2px 0 12px">
      <input id="rgLegal" type="checkbox" style="margin-top:3px;accent-color:var(--neon)"/>
      <span>Li e aceito os <a href="/termos-de-uso.html" style="color:var(--neon)">Termos de Uso</a> e a <a href="/politica-de-seguranca.html" style="color:var(--neon)">Política de Segurança e Privacidade</a>.</span>
    </label>
    <button id="rgBtn" class="btn-primary" style="width:100%" disabled>CADASTRAR</button>
    <div id="rgMsg" style="font-size:12px;text-align:center;min-height:14px;margin-top:10px"></div>
    <div style="text-align:center;margin-top:10px;font-size:12px;color:var(--muted)"><a href="#" id="goLog" style="color:var(--neon)">Já tenho conta</a></div>
  `,()=>{
    document.getElementById("rgBtn").onclick=async()=>{
      const msg=document.getElementById("rgMsg");
      const legal=document.getElementById("rgLegal").checked;
      if(!legal){msg.style.color="#ff8a8a";msg.textContent="Aceite os termos para continuar.";return;}
      const body={nome:document.getElementById("rgNome").value.trim(),matricula:document.getElementById("rgMat").value.trim(),funcao:document.getElementById("rgFun").value.trim(),email:document.getElementById("rgEmail").value.trim(),senha:document.getElementById("rgSen").value.trim(),aceita_termos:legal};
      msg.style.color="var(--muted)";msg.textContent="Enviando...";
      try{
        const r=await fetch("/api/auth/registrar",{method:"POST",headers:{"Content-Type":"application/json"},body:JSON.stringify(body)});
        const d=await r.json();
        if(r.ok){msg.style.color="var(--neon)";msg.textContent=d.mensagem||"Cadastro enviado. Aguarde aprovação do admin.";}
        else{msg.style.color="#ff8a8a";msg.textContent=d.error||"Falha";}
      }catch(e){msg.style.color="#ff8a8a";msg.textContent="Erro: "+e.message;}
    };
    document.getElementById("rgLegal").onchange=()=>{document.getElementById("rgBtn").disabled=!document.getElementById("rgLegal").checked;};
    document.getElementById("goLog").onclick=e=>{e.preventDefault();openLogin();};
  });
}

function openLegalAcceptanceModal(info){
  const termos=(info&&info.legal_terms_version)||"1.0";
  const politica=(info&&info.legal_policy_version)||"1.0";
  openModal("Aceite obrigatório",`
    <div style="font-size:14px;line-height:1.5;margin-bottom:14px">
      Para continuar usando o Agenda Turma A, confirme o aceite da versão atual dos documentos:
    </div>
    <div style="display:grid;gap:8px;margin-bottom:14px">
      <a class="btn-secondary" href="/termos-de-uso.html" style="text-align:center;text-decoration:none">📄 Termos de Uso v${escapeHtml(termos)}</a>
      <a class="btn-secondary" href="/politica-de-seguranca.html" style="text-align:center;text-decoration:none">🛡 Política de Segurança v${escapeHtml(politica)}</a>
    </div>
    <label style="display:flex;gap:8px;align-items:flex-start;font-size:12px;color:var(--muted);line-height:1.45;margin-bottom:12px">
      <input id="laChk" type="checkbox" style="margin-top:3px;accent-color:var(--neon)"/>
      <span>Li e aceito os Termos de Uso e a Política de Segurança e Privacidade.</span>
    </label>
    <button id="laBtn" class="btn-primary" style="width:100%" disabled>ACEITAR E CONTINUAR</button>
    <div id="laMsg" style="font-size:12px;text-align:center;min-height:14px;margin-top:10px;color:#ff8a8a"></div>
  `,()=>{
    const chk=document.getElementById("laChk");
    const btn=document.getElementById("laBtn");
    const msg=document.getElementById("laMsg");
    chk.onchange=()=>{btn.disabled=!chk.checked;};
    btn.onclick=async()=>{
      if(!chk.checked)return;
      msg.style.color="var(--muted)";msg.textContent="Registrando aceite...";
      try{
        const r=await fetch("/api/auth/legal-acceptance",{
          method:"POST",
          headers:{"Content-Type":"application/json","Authorization":"Bearer "+getToken()},
          body:JSON.stringify({accepted:true})
        });
        const d=await r.json();
        if(r.ok){
          if(CURRENT_USER)CURRENT_USER.legal_acceptance_required=false;
          closeModal();showToast("✅ Aceite registrado");render();
        }else{
          msg.style.color="#ff8a8a";msg.textContent=d.error||"Falha ao registrar aceite";
        }
      }catch(e){msg.style.color="#ff8a8a";msg.textContent="Erro: "+e.message;}
    };
  });
}

// ----- guard de autenticação para seções privadas -----
async function requireAuth(){
  if(!getToken()){openLogin();return false;}
  if(!CURRENT_USER){await loadMe();}
  if(!CURRENT_USER){openLogin();return false;}
  if(CURRENT_USER.legal_acceptance_required){openLegalAcceptanceModal(CURRENT_USER);return false;}
  return true;
}

// ===== EVENTOS =====
function renderMuralFilterBar(){
  const filterAtivo=Array.isArray(S.evFilter)&&S.evFilter.length>0;
  const chipsHtml=Object.entries(EVENTO_TIPOS).map(([key,t])=>{
    const ativo=S.evFilter&&S.evFilter.includes(key);
    const desligado=filterAtivo&&!ativo;
    const cls=`cal-legend-item legend-btn-mural${ativo?" active":""}${desligado?" off":""}`;
    return `<button type="button" class="${cls}" data-tipo="${key}" aria-pressed="${ativo?"true":"false"}" title="${ativo?'Remover filtro: ':'Filtrar por: '}${escapeHtml(t.label)}"><span class="cl-dot" style="background:${t.cor}"></span><span class="cl-emo">${t.emoji}</span><span class="cl-lbl">${escapeHtml(t.label)}</span></button>`;
  }).join("");
  const filterCount=filterAtivo?S.evFilter.length:0;
  const hint=filterAtivo
    ?`<span class="cal-legend-hint">Mostrando ${filterCount} de ${Object.keys(EVENTO_TIPOS).length} tipos</span>`
    :`<span class="cal-legend-hint">Toque em um tipo para filtrar</span>`;
  const clearBtn=filterAtivo?`<button type="button" class="cal-legend-clear" id="muralLegendClear" title="Mostrar todos os tipos">Limpar filtro</button>`:"";
  return `<div class="cal-legend" style="margin-top:0;padding-top:0;border-top:none;padding:10px 14px 0">
    <div class="cal-legend-head">
      <div class="cal-legend-tit">Filtrar por tipo</div>
      ${hint}
      ${clearBtn}
    </div>
    <div class="cal-legend-items">${chipsHtml}</div>
  </div>`;
}
function bindMuralFilterChips(c){
  document.querySelectorAll(".legend-btn-mural[data-tipo]").forEach(b=>{
    b.addEventListener("click",(e)=>{
      e.preventDefault();
      const t=b.dataset.tipo;
      if(!EVENTO_TIPOS[t])return;
      toggleEvFilter(t);
      renderEventos(c);
    });
  });
  const cl=document.getElementById("muralLegendClear");
  if(cl)cl.onclick=(e)=>{e.preventDefault();clearEvFilter();renderEventos(c);};
}
// ===== MODULO DSS (Dialogo de Seguranca) =====
let DSS_STATE={escala:[],historico:[]};
let DSS_LOOKUP=null; // empregado resolvido no form de escalar
let DSS_CONTAINER=null; // container da secao DSS (pra voltar do editor)
const DSS_STATUS={pendente:["Pendente","dss-s-pend"],card_pronto:["Card pronto","dss-s-ready"],revisado:["Revisado","dss-s-rev"]};
function dssIsSup(){return !!(CURRENT_USER&&(CURRENT_USER.role==="admin"||CURRENT_USER.role==="aprovador"));}
function dssIsAdmin(){return !!(CURRENT_USER&&CURRENT_USER.role==="admin");}
function dssIsMine(e){return !!(CURRENT_USER&&e&&String(CURRENT_USER.matricula)===String(e.matricula));}
function dssFmt(d){if(!d)return"—";const p=String(d).split("-");return p.length===3?`${p[2]}/${p[1]}`:d;}
function dssDia(d){return d?parseInt(String(d).split("-")[2],10):"";}
function dssMes3(d){return d?MESES3[parseInt(String(d).split("-")[1],10)-1]:"";}
function dssDaysTo(d){const t=new Date();t.setHours(0,0,0,0);return Math.round((new Date(d+"T00:00")-t)/864e5);}
function dssWhen(d){const n=dssDaysTo(d);return n<0?"já passou":n===0?"hoje":n===1?"amanhã":"em "+n+" dias";}
function dssIni(n){return (n||"?").split(" ").slice(0,2).map(w=>w[0]||"").join("").toUpperCase();}

async function renderDSS(c){
  document.getElementById("rightPanel").style.display="none";
  DSS_CONTAINER=c;
  const sup=dssIsSup(), adm=dssIsAdmin();
  c.innerHTML=`
  <div class="dss-wrap">
    <div class="dss-hero">
      <div class="dss-hero-ic"><svg width="26" height="26" fill="none" stroke="currentColor" stroke-width="1.9" viewBox="0 0 24 24"><path d="M12 22s8-4 8-10V5l-8-3-8 3v7c0 6 8 10 8 10z"/><path d="M9 12l2 2 4-4"/></svg></div>
      <div><div class="dss-hero-tit">Programa Mensal de DSS</div>
      <div class="dss-hero-sub">Escala de apresentação da turma</div></div>
    </div>

    <div class="dss-shead">
      <h3>Próximos apresentadores</h3>
      ${adm?`<button class="dss-btn dss-btn-primary dss-sm" id="dssEscalarBtn"><svg width="15" height="15" fill="none" stroke="currentColor" stroke-width="2.2" viewBox="0 0 24 24"><path d="M12 5v14M5 12h14"/></svg> Escalar apresentador</button>`:""}
    </div>
    ${adm?`<div class="dss-escala" id="dssEscalaForm">
      <div class="dss-eg">
        <div class="dss-field dss-search"><label>Buscar empregado *</label>
          <input id="dssEQ" autocomplete="off" placeholder="Nome ou matrícula"/>
          <div class="dss-results" id="dssEResults"></div>
          <div class="dss-selected" id="dssESelected"></div>
        </div>
        <div class="dss-field"><label>Data *</label><input id="dssEData" type="date"/></div>
        <div class="dss-field"><label>Tema</label><input id="dssETema" placeholder="Ex.: Trabalho em altura"/></div>
        <button class="dss-btn dss-btn-primary" id="dssESave">Confirmar escala</button>
      </div>
      <div class="dss-hint">Só administradores escalam. Busque por nome ou matrícula e selecione o empregado.</div>
    </div>`:""}
    <div class="dss-next" id="dssNext"></div>

    <div class="dss-shead"><h3>Na agenda da turma</h3><span class="dss-count">lançado quando a DSS é verificada</span></div>
    <div class="dss-agbox" id="dssAgenda"></div>

    <div class="dss-shead"><h3>Programa do mês</h3><span class="dss-count" id="dssProgCount"></span></div>
    <div class="dss-list" id="dssProg"></div>

    <div class="dss-shead"><h3>Histórico de DSS realizadas</h3><span class="dss-count" id="dssHistCount"></span></div>
    <div class="dss-list" id="dssHist"></div>
  </div>`;

  if(adm){
    const form=document.getElementById("dssEscalaForm");
    document.getElementById("dssEscalarBtn").onclick=()=>form.classList.toggle("open");
    document.getElementById("dssEQ").addEventListener("input",dssDebouncedSearch);
    document.getElementById("dssESave").onclick=dssEscalar;
  }
  await dssLoad();
}

let _dssSrchTimer=null;
function dssDebouncedSearch(){
  clearTimeout(_dssSrchTimer);
  const q=document.getElementById("dssEQ").value.trim();
  const box=document.getElementById("dssEResults");
  if(q.length<2){box.innerHTML="";box.classList.remove("open");return;}
  _dssSrchTimer=setTimeout(async()=>{
    try{
      const r=await apiFetch("/api/dss/buscar?q="+encodeURIComponent(q));
      const d=await r.json();const res=d.results||[];
      if(!res.length){box.innerHTML='<div class="dss-res-empty">Nenhum empregado encontrado</div>';box.classList.add("open");return;}
      box.innerHTML=res.map(u=>`<div class="dss-res" data-mat="${escapeHtml(u.matricula)}" data-nome="${escapeHtml(u.nome)}" data-func="${escapeHtml(u.funcao)}"><div class="dss-res-nm">${escapeHtml(u.nome||"(sem nome)")}</div><div class="dss-res-mt">Matr. ${escapeHtml(u.matricula)} · ${escapeHtml(u.funcao||"")}</div></div>`).join("");
      box.classList.add("open");
      box.querySelectorAll(".dss-res").forEach(el=>el.onclick=()=>{
        DSS_LOOKUP={matricula:el.dataset.mat,nome:el.dataset.nome,funcao:el.dataset.func};
        document.getElementById("dssESelected").innerHTML="✓ <b>"+escapeHtml(el.dataset.nome)+"</b> · Matr. "+escapeHtml(el.dataset.mat);
        document.getElementById("dssEQ").value=el.dataset.nome;
        box.innerHTML="";box.classList.remove("open");
      });
    }catch(e){box.innerHTML="";box.classList.remove("open");}
  },280);
}

async function dssEscalar(){
  const data=document.getElementById("dssEData").value;
  const tema=document.getElementById("dssETema").value.trim();
  if(!DSS_LOOKUP||!DSS_LOOKUP.matricula){showToast("Busque e selecione um empregado");return;}
  if(!data){showToast("Informe a data da apresentação");return;}
  try{
    const r=await apiFetch("/api/dss/escala",{method:"POST",body:JSON.stringify({matricula:DSS_LOOKUP.matricula,data_prevista:data,tema:tema})});
    const d=await r.json();
    if(r.ok&&d.ok){
      ["dssEQ","dssEData","dssETema"].forEach(id=>{const el=document.getElementById(id);if(el)el.value="";});
      const sel=document.getElementById("dssESelected");if(sel)sel.innerHTML="";
      DSS_LOOKUP=null;
      document.getElementById("dssEscalaForm").classList.remove("open");
      showToast("Apresentador escalado ✓");await dssLoad();
    }else{showToast(d.mensagem||"Não foi possível escalar");}
  }catch(e){if(e.message!=="auth")showToast("Erro ao escalar");}
}

async function dssLoad(){
  try{const r=await apiFetch("/api/dss");const d=await r.json();DSS_STATE={escala:d.escala||[],historico:d.historico||[]};}
  catch(e){DSS_STATE={escala:[],historico:[]};}
  dssRenderMural();
  try{await carregarEventosCache();}catch(e){}
  dssRenderAgenda();
}

function dssRenderMural(){
  const sup=dssIsSup(), adm=dssIsAdmin();
  const esc=[...DSS_STATE.escala].sort((a,b)=>(a.data_prevista||"").localeCompare(b.data_prevista||""));
  const next=esc.filter(e=>dssDaysTo(e.data_prevista)>=0).slice(0,4);
  const nextEl=document.getElementById("dssNext");
  if(nextEl)nextEl.innerHTML=next.length?next.map((e,i)=>{
    const st=DSS_STATUS[e.status]||DSS_STATUS.pendente;
    return `<div class="dss-pcard ${i===0?"first":""}">
      <span class="dss-when">${dssWhen(e.data_prevista)}</span>
      <span class="dss-plabel">${i===0?"PRÓXIMO":(i+1)+"º DA ESCALA"}</span>
      <div class="dss-person"><div class="dss-av">${dssIni(e.nome)}</div><div><div class="dss-nm">${escapeHtml(e.nome||"")}</div><div class="dss-mt">Matr. ${escapeHtml(e.matricula||"")}</div></div></div>
      <div class="dss-ptheme">Tema: <b>${escapeHtml(e.tema||"a definir")}</b> · ${dssFmt(e.data_prevista)}</div>
      <div><span class="dss-status ${st[1]}">${st[0]}</span></div>
      <div class="dss-acts">${(dssIsMine(e)||adm)?`<button class="dss-btn dss-btn-primary dss-sm" onclick="dssOpenCard('${e.id}')">${e.status==="pendente"?"Montar card":"Ver card"}</button>`:""}${sup?`<button class="dss-btn dss-btn-ghost dss-sm" onclick="dssConfirmar('${e.id}')">✓ Realizada</button>`:""}${adm?`<button class="dss-btn dss-btn-ghost dss-sm" onclick="dssRemover('${e.id}')">Remover</button>`:""}</div>
    </div>`;}).join(""):`<div class="dss-pcard"><span class="dss-plabel">Ninguém escalado ainda</span></div>`;

  const prog=document.getElementById("dssProg");
  if(prog)prog.innerHTML=esc.length?esc.map(e=>{
    const st=DSS_STATUS[e.status]||DSS_STATUS.pendente;
    return `<div class="dss-row">
      <div class="dss-date"><div class="d">${dssDia(e.data_prevista)}</div><div class="m">${dssMes3(e.data_prevista)}</div></div>
      <div class="dss-who">${escapeHtml(e.nome||"")}<small>Matr. ${escapeHtml(e.matricula||"")}</small></div>
      <div class="dss-th">${escapeHtml(e.tema||"tema a definir")}</div>
      <div style="display:flex;align-items:center;gap:8px;justify-content:flex-end"><span class="dss-status ${st[1]}">${st[0]}</span>${(dssIsMine(e)||adm)?`<button class="dss-btn dss-btn-ghost dss-sm" onclick="dssOpenCard('${e.id}')">Card</button>`:""}</div>
    </div>`;}).join(""):`<div class="dss-row" style="color:var(--muted)">Nenhuma apresentação programada.</div>`;
  const pc=document.getElementById("dssProgCount");if(pc)pc.textContent=esc.length+" programadas";

  const hist=[...DSS_STATE.historico].sort((a,b)=>(b.data_real||"").localeCompare(a.data_real||""));
  const histEl=document.getElementById("dssHist");
  if(histEl)histEl.innerHTML=hist.length?hist.map(x=>{
    const atraso=x.data_prevista&&x.data_prevista!==x.data_real?` <span style="color:var(--orange,#f5a623);font-size:11px">(prev. ${dssFmt(x.data_prevista)} · atrasou)</span>`:"";
    return `<div class="dss-row">
      <div class="dss-date"><div class="d">${dssDia(x.data_real)}</div><div class="m">${dssMes3(x.data_real)}</div></div>
      <div class="dss-who">${escapeHtml(x.nome||"")}<small>Matr. ${escapeHtml(x.matricula||"")}</small></div>
      <div class="dss-th">${escapeHtml(x.tema||"")}${atraso}</div>
      <div><span class="dss-status dss-s-done">Apresentado</span></div>
    </div>`;}).join(""):`<div class="dss-row" style="color:var(--muted)">Nenhuma DSS realizada ainda.</div>`;
  const hc=document.getElementById("dssHistCount");if(hc)hc.textContent=hist.length+" realizadas";
}

function dssRenderAgenda(){
  const el=document.getElementById("dssAgenda");if(!el)return;
  const evs=(EVENTOS_CACHE||[]).filter(e=>e.tipo==="dss").sort((a,b)=>(b.data||"").localeCompare(a.data||"")).slice(0,6);
  el.innerHTML=evs.length?evs.map(e=>`<div class="dss-agrow"><span class="dss-agdot"></span><span class="dss-agdate">${dssFmt(e.data)}</span><span class="dss-agtit">${escapeHtml(e.titulo||"")}</span><span class="dss-agtag">DSS</span></div>`).join(""):`<div class="dss-agrow" style="color:var(--muted)">Nenhum lançamento ainda.</div>`;
}

window.dssConfirmar=async function(id){
  if(!confirm("Confirmar que a DSS foi apresentada?\nMarca como verificada (data de hoje) e lança na agenda da turma."))return;
  try{
    const r=await apiFetch("/api/dss/"+id+"/confirmar",{method:"POST"});
    const d=await r.json();
    if(r.ok&&d.ok){showToast("✓ Verificado · lançado na agenda");await dssLoad();}
    else showToast(d.mensagem||"Não foi possível confirmar");
  }catch(e){if(e.message!=="auth")showToast("Erro ao confirmar");}
};
window.dssRemover=async function(id){
  if(!confirm("Remover este apresentador da escala?"))return;
  try{
    const r=await apiFetch("/api/dss/escala/"+id,{method:"DELETE"});
    if(r.ok){showToast("Removido da escala");await dssLoad();}
    else showToast("Não foi possível remover");
  }catch(e){if(e.message!=="auth")showToast("Erro ao remover");}
};

/* ===== Card de exportação (WhatsApp) — autoria manual da pessoa escalada ===== */
let DSS_EDIT=null;        // entry sendo editada (referencia em DSS_STATE.escala)
let dssImgURL=null;       // dataURL/endpoint da imagem (preview + canvas)
let dssImgFit="contain";  // contain | cover
let dssRatio="wide";      // wide (16:9) | story (9:16)
const DSS_CHECK='<svg width="13" height="13" fill="none" stroke="currentColor" stroke-width="2.6" viewBox="0 0 24 24"><path d="M20 6L9 17l-5-5"/></svg>';

window.dssOpenCard=function(id){
  const e=(DSS_STATE.escala||[]).find(x=>x.id===id);
  if(!e){showToast("Apresentação não encontrada");return;}
  DSS_EDIT=e;
  dssImgFit="contain"; dssRatio="wide";
  dssImgURL=e.card_img_key?("/api/dss/"+e.id+"/imagem?t="+encodeURIComponent(getToken())+"&_="+Date.now()):null;
  dssRenderEditor();
};

// lê o card direto dos campos (fonte da verdade do preview/export)
function dssCurrentCard(){
  const g=id=>(document.getElementById(id)?.value||"");
  return {
    titulo:g("dcT").trim()||((DSS_EDIT&&DSS_EDIT.tema)||""),
    bullets:g("dcB").split("\n").map(s=>s.trim()).filter(Boolean),
    fala:g("dcF").trim(),
    pergunta:g("dcQ").trim(),
  };
}

function dssRenderEditor(){
  const e=DSS_EDIT, c=DSS_CONTAINER; if(!e||!c)return;
  const card=(e.card&&typeof e.card==="object")?e.card:{};
  c.innerHTML=`
  <button class="dss-back" id="dssBack"><svg width="16" height="16" fill="none" stroke="currentColor" stroke-width="2" viewBox="0 0 24 24"><path d="M19 12H5M12 19l-7-7 7-7"/></svg> Voltar ao mural</button>
  <div class="dss-shead"><h3>Card de DSS pro grupo</h3><span class="dss-count">${escapeHtml(e.nome||"")} · ${dssFmt(e.data_prevista)}</span></div>
  <div class="dss-gen">
    <div class="dss-panel">
      <div class="dss-gfield"><label>Título <span class="req">*</span></label><input id="dcT" maxlength="80" placeholder="Ex.: Uso correto de EPI"/></div>
      <div class="dss-gfield"><label>Pontos-chave (um por linha)</label><textarea id="dcB" maxlength="800" placeholder="Inspecione o EPI antes do turno&#10;Descarte itens danificados&#10;Comunique qualquer condição insegura"></textarea></div>
      <div class="dss-gfield"><label>Fala do apresentador</label><textarea id="dcF" maxlength="400" placeholder="Frase de abertura que você fala pra equipe"></textarea></div>
      <div class="dss-gfield"><label>Pergunta de engajamento</label><input id="dcQ" maxlength="200" placeholder="Ex.: E você, está usando o EPI certo?"/></div>
      <div class="dss-gfield"><label>Imagem (opcional)</label>
        <label class="dss-drop" for="dcImg"><input id="dcImg" type="file" accept="image/jpeg,image/png,image/webp" hidden/><span id="dcImgTxt">📷 Toque para adicionar uma foto</span></label>
        <div class="dss-chips" style="margin-top:9px" id="dcFit"><button type="button" class="dss-chip" aria-pressed="true" data-fit="contain">Foto inteira (sem cortar)</button><button type="button" class="dss-chip" aria-pressed="false" data-fit="cover">Preencher (corta)</button></div>
        <div id="dcImgActions" style="margin-top:8px"></div></div>
      <div class="dss-gfield"><label>Apresentação · PowerPoint ou PDF (opcional)</label>
        <label class="dss-drop" for="dcPpt"><input id="dcPpt" type="file" accept=".ppt,.pptx,.pdf,application/vnd.ms-powerpoint,application/vnd.openxmlformats-officedocument.presentationml.presentation,application/pdf" hidden/><span id="dcPptTxt">📊 Subir .pptx, .ppt ou .pdf</span></label>
        <div class="dss-hint">É o material que você espelha na tela. PPT/PPTX vira PDF automaticamente (até 20 MB).</div>
        <div id="dcPptActions" style="margin-top:8px"></div></div>
      <div class="dss-gactions"><button class="dss-btn dss-btn-primary" id="dcSave">Salvar card</button></div>
      <div class="dss-note"><svg width="15" height="15" fill="none" stroke="currentColor" stroke-width="2" viewBox="0 0 24 24" style="flex:0 0 auto;margin-top:1px"><circle cx="12" cy="12" r="10"/><path d="M12 16v-4M12 8h.01"/></svg><span>Você escreve a sua DSS e sobe a sua apresentação. O card vira um PNG pronto pra mandar no grupo do WhatsApp.</span></div>
    </div>
    <div>
      <div class="dss-prevhead"><h4>Card de exportação</h4>
        <div class="dss-ratio" id="dcRatio"><button type="button" class="dss-chip" aria-pressed="true" data-r="wide">16:9</button><button type="button" class="dss-chip" aria-pressed="false" data-r="story">9:16 WhatsApp</button></div></div>
      <article class="dss-slide" id="dcSlide">
        <div class="dss-stop"><span class="dss-badge">DSS</span><span class="dss-kicker">Diálogo de Segurança</span><span class="dss-vale">VALE</span></div>
        <div class="dss-sbody">
          <div class="dss-smain"><h1 class="dss-stitle" id="dcsTitle"></h1><ul class="dss-bullets" id="dcsBullets"></ul></div>
          <div class="dss-saside">
            <div class="dss-simg" id="dcsImg"><div class="imghint"><svg width="28" height="28" fill="none" stroke="currentColor" stroke-width="1.6" viewBox="0 0 24 24"><rect x="3" y="3" width="18" height="18" rx="2"/><circle cx="8.5" cy="8.5" r="1.5"/><path d="M21 15l-5-5L5 21"/></svg>fundo padrão</div></div>
            <div class="dss-speaker"><div class="lbl"><svg width="12" height="12" fill="none" stroke="currentColor" stroke-width="2.2" viewBox="0 0 24 24"><path d="M3 11l18-5v12L3 14v-3z"/></svg>Fala do apresentador</div><p id="dcsSpeaker"></p></div>
          </div>
        </div>
        <div class="dss-sfoot">
          <span class="fitem"><svg width="12" height="12" fill="none" stroke="currentColor" stroke-width="2" viewBox="0 0 24 24"><rect x="3" y="4" width="18" height="18" rx="2"/><path d="M16 2v4M8 2v4M3 10h18"/></svg><b id="dcsDate"></b></span>
          <span class="fitem"><svg width="12" height="12" fill="none" stroke="currentColor" stroke-width="2" viewBox="0 0 24 24"><circle cx="12" cy="8" r="4"/><path d="M4 21a8 8 0 0 1 16 0"/></svg><b id="dcsResp"></b></span>
          <span class="dss-qmark"><svg width="12" height="12" fill="none" stroke="currentColor" stroke-width="2.4" viewBox="0 0 24 24"><path d="M9.1 9a3 3 0 0 1 5.8 1c0 2-3 3-3 3M12 17h.01"/></svg><span id="dcsQ"></span></span>
        </div>
      </article>
      <div class="dss-gactions">
        <button class="dss-btn dss-btn-primary" id="dcPng"><svg width="17" height="17" fill="none" stroke="currentColor" stroke-width="2" viewBox="0 0 24 24"><path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4M7 10l5 5 5-5M12 15V3"/></svg> Baixar PNG</button>
        <button class="dss-btn dss-btn-ghost" id="dcShare"><svg width="17" height="17" fill="none" stroke="currentColor" stroke-width="2" viewBox="0 0 24 24"><path d="M4 12v8a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2v-8M16 6l-4-4-4 4M12 2v13"/></svg> Compartilhar</button>
      </div>
    </div>
  </div>`;

  // prefill a partir do card salvo (ou tema da escala)
  document.getElementById("dcT").value=card.titulo||e.tema||"";
  document.getElementById("dcB").value=(card.bullets||[]).join("\n");
  document.getElementById("dcF").value=card.fala||"";
  document.getElementById("dcQ").value=card.pergunta||"";

  document.getElementById("dssBack").onclick=()=>renderDSS(c);
  ["dcT","dcB","dcF","dcQ"].forEach(id=>document.getElementById(id).addEventListener("input",dssPreview));
  document.getElementById("dcFit").addEventListener("click",ev=>{const b=ev.target.closest(".dss-chip");if(!b)return;[...ev.currentTarget.children].forEach(x=>x.setAttribute("aria-pressed",x===b));dssImgFit=b.dataset.fit;dssPreview();});
  document.getElementById("dcRatio").addEventListener("click",ev=>{const b=ev.target.closest(".dss-chip");if(!b)return;[...ev.currentTarget.children].forEach(x=>x.setAttribute("aria-pressed",x===b));dssRatio=b.dataset.r;document.getElementById("dcSlide").classList.toggle("story",dssRatio==="story");});
  document.getElementById("dcImg").addEventListener("change",dssImgPick);
  document.getElementById("dcPpt").addEventListener("change",dssPptPick);
  document.getElementById("dcSave").onclick=dssSalvarCard;
  document.getElementById("dcPng").onclick=()=>dssExport(false);
  document.getElementById("dcShare").onclick=()=>dssExport(true);
  dssRenderImgActions();
  dssRenderPptActions();
  dssPreview();
}

function dssRenderImgActions(){
  const box=document.getElementById("dcImgActions");if(!box)return;
  const txt=document.getElementById("dcImgTxt");
  if(dssImgURL){
    if(txt)txt.textContent="✓ Imagem adicionada";
    box.innerHTML=`<button class="dss-btn dss-btn-ghost dss-sm" id="dcImgDel">Remover imagem</button>`;
    document.getElementById("dcImgDel").onclick=dssImgRemove;
  }else{box.innerHTML="";if(txt)txt.textContent="📷 Toque para adicionar uma foto";}
}

function dssPreview(){
  const card=dssCurrentCard();
  document.getElementById("dcsTitle").textContent=card.titulo||"Título da DSS";
  const bl=document.getElementById("dcsBullets");
  bl.innerHTML=(card.bullets.length?card.bullets:["Adicione os pontos-chave (um por linha)"]).map(b=>`<li>${DSS_CHECK}<span>${escapeHtml(b)}</span></li>`).join("");
  document.getElementById("dcsSpeaker").textContent=card.fala||"Sua fala de abertura aparece aqui.";
  document.getElementById("dcsQ").textContent=card.pergunta||"Pergunta de engajamento";
  document.getElementById("dcsResp").textContent=(DSS_EDIT&&DSS_EDIT.nome)||"—";
  const dd=DSS_EDIT&&DSS_EDIT.data_prevista?new Date(DSS_EDIT.data_prevista+"T00:00"):new Date();
  document.getElementById("dcsDate").textContent=dd.toLocaleDateString("pt-BR",{day:"2-digit",month:"2-digit",year:"numeric"});
  const img=document.getElementById("dcsImg");
  if(dssImgURL){img.style.backgroundImage=`url("${dssImgURL}")`;img.classList.toggle("contain",dssImgFit==="contain");img.innerHTML="";}
  else{img.style.backgroundImage="";img.classList.remove("contain");img.innerHTML=`<div class="imghint"><svg width="28" height="28" fill="none" stroke="currentColor" stroke-width="1.6" viewBox="0 0 24 24"><rect x="3" y="3" width="18" height="18" rx="2"/><circle cx="8.5" cy="8.5" r="1.5"/><path d="M21 15l-5-5L5 21"/></svg>fundo padrão</div>`;}
}

async function dssSalvarCard(){
  const card=dssCurrentCard();
  if(!card.titulo){showToast("Dê um título pro card");return;}
  try{
    const r=await apiFetch("/api/dss/"+DSS_EDIT.id+"/card",{method:"POST",body:JSON.stringify({card})});
    const d=await r.json();
    if(r.ok&&d.ok&&d.card){DSS_EDIT.card=d.card;DSS_EDIT.status="card_pronto";showToast("Card salvo ✓");}
    else showToast(d.mensagem||"Não foi possível salvar");
  }catch(e){if(e.message!=="auth")showToast("Erro ao salvar");}
}

async function dssImgPick(ev){
  const f=ev.target.files&&ev.target.files[0];if(!f)return;
  if(!/^image\/(jpeg|png|webp)$/.test(f.type)){showToast("Use JPG, PNG ou WebP");return;}
  if(f.size>5*1024*1024){showToast("Imagem maior que 5 MB");return;}
  let dataURL;
  try{dataURL=await dssReadAsDataURL(f);}catch(e){showToast("Não consegui ler a imagem");return;}
  dssImgURL=dataURL;dssRenderImgActions();dssPreview();
  const b64=(dataURL.split(",")[1])||"";
  try{
    const r=await apiFetch("/api/dss/"+DSS_EDIT.id+"/imagem",{method:"POST",body:JSON.stringify({b64,mimetype:f.type})});
    const d=await r.json();
    if(r.ok&&d.ok){DSS_EDIT.card_img_key="set";showToast("Imagem enviada ✓");}
    else showToast(d.mensagem||"Falha ao enviar a imagem");
  }catch(e){if(e.message!=="auth")showToast("Erro ao enviar imagem");}
}

async function dssImgRemove(){
  dssImgURL=null;dssRenderImgActions();dssPreview();
  const inp=document.getElementById("dcImg");if(inp)inp.value="";
  try{await apiFetch("/api/dss/"+DSS_EDIT.id+"/imagem",{method:"DELETE"});DSS_EDIT.card_img_key=null;}catch(e){}
}

function dssReadAsDataURL(file){return new Promise((res,rej)=>{const fr=new FileReader();fr.onload=()=>res(fr.result);fr.onerror=rej;fr.readAsDataURL(file);});}

/* ---- apresentacao: upload (PPT/PDF), conversao no servidor, visualizador ---- */
async function dssPptPick(ev){
  const f=ev.target.files&&ev.target.files[0];if(!f)return;
  const ext=(f.name.split(".").pop()||"").toLowerCase();
  if(!["ppt","pptx","pdf"].includes(ext)){showToast("Use .pptx, .ppt ou .pdf");return;}
  if(f.size>20*1024*1024){showToast("Arquivo maior que 20 MB");return;}
  const txt=document.getElementById("dcPptTxt");
  if(txt)txt.textContent="⏳ Enviando"+(ext==="pdf"?"":" e convertendo")+"… "+f.name;
  let dataURL;try{dataURL=await dssReadAsDataURL(f);}catch(e){showToast("Não consegui ler o arquivo");dssRenderPptActions();return;}
  const b64=(dataURL.split(",")[1])||"";
  try{
    const r=await apiFetch("/api/dss/"+DSS_EDIT.id+"/apresentacao",{method:"POST",body:JSON.stringify({b64,nome:f.name,mimetype:f.type})});
    const d=await r.json();
    if(r.ok&&d.ok){
      DSS_EDIT.ppt_nome=d.nome;DSS_EDIT.ppt_key="set";
      DSS_EDIT.ppt_pdf_key=d.tem_pdf?"set":null;DSS_EDIT.ppt_pendente=!!d.pendente;
      showToast(d.pendente?"Enviado. Conversão pendente (falta o LibreOffice no servidor).":"Apresentação pronta ✓");
    }else{showToast(d.mensagem||"Falha ao enviar a apresentação");}
  }catch(e){if(e.message!=="auth")showToast("Erro ao enviar a apresentação");}
  finally{dssRenderPptActions();}
}

function dssRenderPptActions(){
  const box=document.getElementById("dcPptActions");if(!box)return;
  const txt=document.getElementById("dcPptTxt");const e=DSS_EDIT||{};
  if(e.ppt_pdf_key){
    if(txt)txt.textContent="✓ "+(e.ppt_nome||"apresentação");
    box.innerHTML=`<button class="dss-btn dss-btn-primary dss-sm" id="dcPptOpen">▶ Abrir apresentação</button> <button class="dss-btn dss-btn-ghost dss-sm" id="dcPptDel">Remover</button>`;
    document.getElementById("dcPptOpen").onclick=dssOpenDeck;
    document.getElementById("dcPptDel").onclick=dssPptRemove;
  }else if(e.ppt_pendente){
    if(txt)txt.textContent="⚠ "+(e.ppt_nome||"arquivo")+" — conversão pendente";
    box.innerHTML=`<div class="dss-hint" style="color:var(--orange);margin:0 0 6px">PPT enviado, mas falta o LibreOffice no servidor pra converter em PDF.</div><a class="dss-btn dss-btn-ghost dss-sm" href="/api/dss/${e.id}/apresentacao/original?t=${encodeURIComponent(getToken())}&_=${Date.now()}">Baixar original</a> <button class="dss-btn dss-btn-ghost dss-sm" id="dcPptDel">Remover</button>`;
    document.getElementById("dcPptDel").onclick=dssPptRemove;
  }else{box.innerHTML="";if(txt)txt.textContent="📊 Subir .pptx, .ppt ou .pdf";}
}

async function dssPptRemove(){
  if(!confirm("Remover a apresentação?"))return;
  try{await apiFetch("/api/dss/"+DSS_EDIT.id+"/apresentacao",{method:"DELETE"});}catch(e){}
  DSS_EDIT.ppt_pdf_key=null;DSS_EDIT.ppt_key=null;DSS_EDIT.ppt_pendente=false;DSS_EDIT.ppt_nome=null;
  const inp=document.getElementById("dcPpt");if(inp)inp.value="";
  dssRenderPptActions();
}

function dssOpenDeck(){
  const e=DSS_EDIT;if(!e||!e.ppt_pdf_key)return;
  // cache-buster (&_=) garante que, apos trocar o arquivo, o iframe nao sirva o PDF antigo
  const url="/api/dss/"+e.id+"/apresentacao.pdf?t="+encodeURIComponent(getToken())+"&_="+Date.now();
  let deck=document.getElementById("dssDeck");
  if(!deck){deck=document.createElement("div");deck.id="dssDeck";deck.className="dss-deck";document.body.appendChild(deck);}
  deck.innerHTML=`<div class="dss-deck-bar"><button class="dss-btn dss-btn-primary dss-deck-back" id="dssDeckClose"><svg width="18" height="18" fill="none" stroke="currentColor" stroke-width="2.2" viewBox="0 0 24 24"><path d="M19 12H5M12 19l-7-7 7-7"/></svg> Voltar</button><span class="dss-deck-tit">${escapeHtml(e.ppt_nome||"Apresentação")}</span><a class="dss-iconbtn" href="${url}" target="_blank" rel="noopener" title="Abrir em nova aba"><svg width="17" height="17" fill="none" stroke="currentColor" stroke-width="2" viewBox="0 0 24 24"><path d="M18 13v6a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2V8a2 2 0 0 1 2-2h6M15 3h6v6M10 14L21 3"/></svg></a></div><iframe class="dss-deck-frame" src="${url}" title="Apresentação"></iframe>`;
  deck.style.display="flex";document.body.classList.add("dss-noscroll");
  document.getElementById("dssDeckClose").onclick=dssCloseDeck;
  document.removeEventListener("keydown",dssDeckKey);
  document.addEventListener("keydown",dssDeckKey);
}
function dssDeckKey(ev){if(ev.key==="Escape")dssCloseDeck();}
function dssCloseDeck(){
  const deck=document.getElementById("dssDeck");if(deck){deck.style.display="none";deck.innerHTML="";}
  document.body.classList.remove("dss-noscroll");
  document.removeEventListener("keydown",dssDeckKey);
}

/* ---- export PNG (canvas nativo, sem libs; imagem same-origin nao tainta) ---- */
function dssLoadImage(src){return new Promise(res=>{const im=new Image();im.onload=()=>res(im);im.onerror=()=>res(null);im.src=src;});}
function dssRoundRect(ctx,x,y,w,h,r){ctx.beginPath();ctx.moveTo(x+r,y);ctx.arcTo(x+w,y,x+w,y+h,r);ctx.arcTo(x+w,y+h,x,y+h,r);ctx.arcTo(x,y+h,x,y,r);ctx.arcTo(x,y,x+w,y,r);ctx.closePath();}
function dssWrap(ctx,text,maxW){const words=(text||"").split(/\s+/);const lines=[];let line="";for(const w of words){const t=line?line+" "+w:w;if(ctx.measureText(t).width>maxW&&line){lines.push(line);line=w;}else line=t;}if(line)lines.push(line);return lines;}
function dssDrawImageBox(ctx,im,x,y,w,h,fit){ctx.save();dssRoundRect(ctx,x,y,w,h,0);ctx.clip();ctx.fillStyle="#0b1119";ctx.fillRect(x,y,w,h);if(im){const ir=im.width/im.height,br=w/h;let dw,dh,dx,dy;if((fit==="contain")?(ir>br):(ir<br)){dw=w;dh=w/ir;}else{dh=h;dw=h*ir;}dx=x+(w-dw)/2;dy=y+(h-dh)/2;ctx.drawImage(im,dx,dy,dw,dh);}ctx.restore();}

async function dssBuildCanvas(){
  const card=dssCurrentCard();
  const story=dssRatio==="story";
  const W=story?1080:1280, H=story?1920:720;
  const cv=document.createElement("canvas");cv.width=W;cv.height=H;
  const ctx=cv.getContext("2d");
  // fundo
  ctx.fillStyle="#0f1720";ctx.fillRect(0,0,W,H);
  const pad=story?64:56;
  // topo
  const topH=story?96:86;
  const g=ctx.createLinearGradient(0,0,W,0);g.addColorStop(0,"#0e2a1c");g.addColorStop(1,"#0f1720");
  ctx.fillStyle=g;ctx.fillRect(0,0,W,topH);
  ctx.fillStyle="#00e676";ctx.fillRect(0,topH-5,W,5);
  ctx.fillStyle="#00e676";dssRoundRect(ctx,pad,topH/2-19,86,38,7);ctx.fill();
  ctx.fillStyle="#04130a";ctx.font="800 22px Lexend, sans-serif";ctx.textBaseline="middle";ctx.fillText("DSS",pad+20,topH/2+1);
  ctx.fillStyle="#9fb0a6";ctx.font="700 19px 'Source Sans 3',sans-serif";ctx.fillText("DIÁLOGO DE SEGURANÇA",pad+104,topH/2+1);
  ctx.fillStyle="#ffd24a";ctx.font="800 26px Lexend, sans-serif";ctx.textAlign="right";ctx.fillText("VALE",W-pad,topH/2+1);ctx.textAlign="left";
  // layout corpo
  const im=dssImgURL?await dssLoadImage(dssImgURL):null;
  const footH=story?150:104;
  const bodyY=topH+(story?36:34), bodyB=H-footH;
  let textX=pad, textW=W-pad*2, imgY, imgH;
  if(story){imgH=im||dssImgURL?640:0;if(imgH){dssDrawImageBox(ctx,im,0,bodyY,W,imgH,dssImgFit);}}
  else{const colW=Math.round(W*0.40);dssDrawImageBox(ctx,im,W-colW,topH+5,colW,bodyB-(topH+5),dssImgFit);textW=W-colW-pad*2-24;}
  let y=story?(bodyY+(imgH?imgH+48:8)):bodyY+8;
  // titulo
  ctx.fillStyle="#fff";ctx.textBaseline="top";
  const tSize=story?58:42;ctx.font=`800 ${tSize}px Lexend, sans-serif`;
  dssWrap(ctx,card.titulo||(DSS_EDIT&&DSS_EDIT.tema)||"Diálogo de Segurança",textW).slice(0,3).forEach(ln=>{ctx.fillText(ln,textX,y);y+=tSize*1.12;});
  y+=story?22:16;
  // bullets
  const bSize=story?30:21;ctx.font=`400 ${bSize}px 'Source Sans 3',sans-serif`;
  (card.bullets||[]).slice(0,4).forEach(b=>{
    ctx.fillStyle="#00e676";ctx.font=`700 ${bSize}px 'Source Sans 3',sans-serif`;ctx.fillText("✓",textX,y);
    ctx.fillStyle="#dfe7ee";ctx.font=`400 ${bSize}px 'Source Sans 3',sans-serif`;
    const lines=dssWrap(ctx,b,textW-38);lines.forEach((ln,i)=>{ctx.fillText(ln,textX+34,y+i*bSize*1.32);});
    y+=Math.max(1,lines.length)*bSize*1.32+(story?18:13);
  });
  // fala (caixa) — encaixa acima do rodape
  if(card.fala){
    const fSize=story?26:19;ctx.font=`italic 400 ${fSize}px 'Source Sans 3',sans-serif`;
    const flines=dssWrap(ctx,'"'+card.fala+'"',textW-36).slice(0,4);
    const boxH=flines.length*fSize*1.34+44;const boxY=Math.min(y+10,bodyB-boxH-8);
    ctx.fillStyle="#0b1119";dssRoundRect(ctx,textX,boxY,textW,boxH,12);ctx.fill();
    ctx.strokeStyle="#1c2733";ctx.lineWidth=1;dssRoundRect(ctx,textX,boxY,textW,boxH,12);ctx.stroke();
    ctx.fillStyle="#f5a623";ctx.font=`800 ${story?15:13}px 'Source Sans 3',sans-serif`;ctx.fillText("FALA DO APRESENTADOR",textX+18,boxY+14);
    ctx.fillStyle="#c8d2dc";ctx.font=`italic 400 ${fSize}px 'Source Sans 3',sans-serif`;
    flines.forEach((ln,i)=>ctx.fillText(ln,textX+18,boxY+38+i*fSize*1.34));
  }
  // rodape
  ctx.fillStyle="#0a0f15";ctx.fillRect(0,H-footH,W,footH);
  ctx.fillStyle="#1c2733";ctx.fillRect(0,H-footH,W,1);
  const fy=H-footH/2;ctx.textBaseline="middle";
  const dd=DSS_EDIT&&DSS_EDIT.data_prevista?new Date(DSS_EDIT.data_prevista+"T00:00"):new Date();
  const dstr=dd.toLocaleDateString("pt-BR",{day:"2-digit",month:"2-digit",year:"numeric"});
  ctx.fillStyle="#dfe7ee";ctx.font="600 22px 'Source Sans 3',sans-serif";
  ctx.fillText(dstr+"   ·   "+((DSS_EDIT&&DSS_EDIT.nome)||""),pad,fy);
  if(card.pergunta){
    ctx.font="700 21px 'Source Sans 3',sans-serif";
    const q=card.pergunta;const qw=Math.min(ctx.measureText(q).width+44,W*0.5);
    ctx.fillStyle="#f5a62322";dssRoundRect(ctx,W-pad-qw,fy-26,qw,52,26);ctx.fill();
    ctx.strokeStyle="#f5a623";ctx.lineWidth=1.5;dssRoundRect(ctx,W-pad-qw,fy-26,qw,52,26);ctx.stroke();
    ctx.fillStyle="#f5a623";ctx.textAlign="center";
    const qline=dssWrap(ctx,q,qw-30)[0]||q;ctx.fillText(qline,W-pad-qw/2,fy);ctx.textAlign="left";
  }
  return cv;
}

async function dssExport(share){
  if(!dssCurrentCard().titulo){showToast("Dê um título pro card primeiro");return;}
  let cv;try{cv=await dssBuildCanvas();}catch(e){showToast("Erro ao montar o PNG");return;}
  const fname="DSS_"+((DSS_EDIT&&DSS_EDIT.nome)||"card").replace(/[^a-zA-Z0-9]+/g,"_").slice(0,30)+".png";
  cv.toBlob(async blob=>{
    if(!blob){showToast("Erro ao gerar o PNG");return;}
    if(share&&navigator.share&&navigator.canShare){
      const file=new File([blob],fname,{type:"image/png"});
      if(navigator.canShare({files:[file]})){
        try{await navigator.share({files:[file],title:"Card de DSS"});return;}catch(e){if(e&&e.name==="AbortError")return;}
      }
    }
    const url=URL.createObjectURL(blob);const a=document.createElement("a");a.href=url;a.download=fname;document.body.appendChild(a);a.click();a.remove();
    setTimeout(()=>URL.revokeObjectURL(url),4000);
    showToast(share?"Compartilhamento indisponível — baixei o PNG":"PNG baixado ✓");
  },"image/png");
}

async function renderEventos(c){
  c.innerHTML=`<div class="pg-head"><div class="pg-tit">📋 MURAL DA TURMA</div><button id="evNew" class="btn-primary">+ NOVO POST</button></div>${renderMuralFilterBar()}<div class="pg-body" id="evBody"><div style="color:var(--muted)">Carregando...</div></div>`;
  document.getElementById("evNew").onclick=()=>openEventoForm();
  bindMuralFilterChips(c);
  if(!await requireAuth()){document.getElementById("evBody").innerHTML='<div style="color:var(--muted);padding:20px;text-align:center">Faça login para ver os eventos.</div>';return;}
  try{
    const r=await apiFetch("/api/mem/eventos");
    const d=await r.json();
    const evsAll=(d.eventos||[]).slice().sort((a,b)=>(Number(b.id)||0)-(Number(a.id)||0));
    const evs=evsAll.filter(passaFiltroEv);
    const body=document.getElementById("evBody");
    if(!evsAll.length){body.innerHTML='<div style="color:var(--muted);padding:20px;text-align:center">Nenhum evento ainda. Clique em + NOVO POST.</div>';return;}
    if(!evs.length){
      const filterAtivo=Array.isArray(S.evFilter)&&S.evFilter.length>0;
      body.innerHTML=`<div style="color:var(--muted);padding:20px;text-align:center">${filterAtivo?"Nenhum post com este filtro.<br/><span style=\"font-size:12px\">Ajuste os tipos acima ou limpe o filtro.</span>":"Nenhum evento ainda."}</div>`;
      return;
    }
    const meuMat=CURRENT_USER&&CURRENT_USER.matricula;
    body.innerHTML=evs.map(e=>{
      const ti=evTipoInfo(e.tipo);
      const reac=e.reacoes||{};
      const barra=REACTION_EMOJIS.map(emo=>{
        const lst=reac[emo]||[];
        const mine=meuMat&&lst.includes(meuMat);
        const cnt=lst.length;
        return `<button class="rx-btn ${mine?"on":""}" data-eid="${e.id}" data-emo="${emo}" title="${cnt?cnt+(cnt===1?" reação":" reações"):"Reagir"}">
          <span class="rx-emo">${emo}</span>${cnt?`<span class="rx-cnt">${cnt}</span>`:""}
        </button>`;
      }).join("");
      return `<div class="lst-item" style="flex-direction:column;align-items:stretch;gap:10px;border-left:3px solid ${ti.cor}">
        <div style="display:flex;justify-content:space-between;gap:10px;align-items:flex-start">
          <div style="flex:1;min-width:0">
            <div style="display:flex;align-items:center;flex-wrap:wrap;gap:6px;margin-bottom:4px"><span class="cal-legend-item" style="font-size:11px;padding:2px 8px"><span class="cl-dot" style="background:${ti.cor}"></span><span class="cl-emo">${ti.emoji}</span><span class="cl-lbl">${escapeHtml(ti.label)}</span></span></div>
            <div style="font-weight:600;font-size:14px">${escapeHtml(e.titulo||"")}</div>
            <div style="color:var(--muted);font-size:12px;margin-top:4px">📅 ${escapeHtml(e.data||"")} ${e.hora?"· ⏰ "+escapeHtml(e.hora):""}</div>
            ${e.descricao?`<div style="margin-top:6px;color:var(--text);font-size:13px;line-height:1.5">${escapeHtml(e.descricao)}</div>`:""}
            <div style="color:var(--muted);font-size:11px;margin-top:6px">por ${escapeHtml(e.autor||"—")}</div>
          </div>
          <button class="btn-danger" data-id="${e.id}">Excluir</button>
        </div>
        <div class="rx-bar">${barra}</div>
      </div>`;
    }).join("");
    body.querySelectorAll("button.btn-danger").forEach(b=>{
      b.onclick=async()=>{
        if(!confirm("Excluir este evento?"))return;
        const novos=evsAll.filter(x=>x.id!=b.dataset.id);
        await apiFetch("/api/mem/eventos",{method:"POST",body:JSON.stringify({eventos:novos})});
        renderEventos(c);
      };
    });
    body.querySelectorAll("button.rx-btn").forEach(b=>{
      b.onclick=async()=>{
        const eid=b.dataset.eid, emo=b.dataset.emo;
        try{
          const r=await apiFetch("/api/eventos/"+encodeURIComponent(eid)+"/reacao",{method:"POST",body:JSON.stringify({emoji:emo})});
          if(r.ok){
            const ev=evs.find(x=>String(x.id)===String(eid));
            if(ev){const d=await r.json();ev.reacoes=d.reacoes||{};renderEventos(c);}
          }
        }catch(err){}
      };
    });
  }catch(e){if(e.message!=="auth")document.getElementById("evBody").innerHTML='<div style="color:#ff8a8a">Erro: '+escapeHtml(e.message)+'</div>';}
}

// ===== EVENTOS PESSOAIS (privados, só do usuário) =====
async function renderPessoais(c){
  c.innerHTML=`<div class="pg-head"><div class="pg-tit">🔒 MEUS EVENTOS</div><button id="pessNew" class="btn-primary">+ NOVO</button></div>
    <div style="font-size:12px;color:var(--text-mute);padding:0 14px 10px">Eventos privados — só você vê. Não vai pro mural nem notifica a turma.</div>
    <div class="pg-body" id="pessBody"><div style="color:var(--muted)">Carregando...</div></div>`;
  document.getElementById("pessNew").onclick=()=>openEventoForm(null,{pessoal:true});
  if(!await requireAuth()){document.getElementById("pessBody").innerHTML='<div style="color:var(--muted);padding:20px;text-align:center">Faça login pra ver seus eventos.</div>';return;}
  try{
    const r=await apiFetch("/api/eventos-pessoais");
    const d=await r.json();
    const evs=(d.eventos||[]).slice().sort((a,b)=>(a.data||"").localeCompare(b.data||""));
    const body=document.getElementById("pessBody");
    if(!evs.length){body.innerHTML='<div style="color:var(--muted);padding:20px;text-align:center">Nenhum evento pessoal ainda.<br/>Toque em <b>+ NOVO</b> pra adicionar.</div>';return;}
    body.innerHTML=evs.map(e=>{
      const ti=evTipoInfo(e.tipo);
      return `<div class="lst-item" style="flex-direction:column;align-items:stretch;gap:6px;border-left:3px solid ${ti.cor}">
        <div style="display:flex;justify-content:space-between;gap:10px;align-items:flex-start">
          <div style="flex:1;min-width:0">
            <div style="font-weight:600;font-size:14px"><span style="color:${ti.cor}">${ti.emoji} ${escapeHtml(ti.label)}</span> · ${escapeHtml(e.titulo||"")}</div>
            <div style="color:var(--muted);font-size:12px;margin-top:4px">📅 ${escapeHtml(e.data||"")}${e.hora?" · ⏰ "+escapeHtml(e.hora):""}</div>
            ${e.descricao?`<div style="margin-top:6px;color:var(--text);font-size:13px;line-height:1.5">${escapeHtml(e.descricao)}</div>`:""}
          </div>
          <button class="btn-danger" data-id="${e.id}">Excluir</button>
        </div>
      </div>`;
    }).join("");
    body.querySelectorAll("button.btn-danger").forEach(b=>{
      b.onclick=async()=>{
        if(!confirm("Excluir este evento pessoal?"))return;
        const novos=evs.filter(x=>String(x.id)!==String(b.dataset.id));
        await apiFetch("/api/eventos-pessoais",{method:"POST",body:JSON.stringify({eventos:novos})});
        await carregarEventosCache();renderPessoais(c);
      };
    });
  }catch(e){if(e.message!=="auth")document.getElementById("pessBody").innerHTML='<div style="color:#ff8a8a">Erro: '+escapeHtml(e.message)+'</div>';}
}

// ===== DIARIO DE BORDO (privado, com câmera/galeria/arquivo) =====
async function _compressImage(file, maxDim=1280, quality=0.7){
  return new Promise((resolve,reject)=>{
    const img=new Image();
    img.onload=()=>{
      let w=img.width, h=img.height;
      if(w>maxDim || h>maxDim){
        if(w>h){h=Math.round(h*maxDim/w);w=maxDim;}
        else{w=Math.round(w*maxDim/h);h=maxDim;}
      }
      const cv=document.createElement("canvas");
      cv.width=w;cv.height=h;
      cv.getContext("2d").drawImage(img,0,0,w,h);
      cv.toBlob(blob=>{
        if(!blob){reject(new Error("Falha ao comprimir"));return;}
        const r=new FileReader();
        r.onload=()=>resolve({b64:r.result.split(",")[1],mimetype:"image/jpeg",size:blob.size});
        r.readAsDataURL(blob);
      },"image/jpeg",quality);
    };
    img.onerror=()=>reject(new Error("Imagem inválida"));
    img.src=URL.createObjectURL(file);
  });
}
async function _fileToB64(file){
  return new Promise((res,rej)=>{const r=new FileReader();r.onload=()=>res({b64:r.result.split(",")[1],mimetype:file.type||"application/octet-stream",size:file.size});r.onerror=rej;r.readAsDataURL(file);});
}
function _formatBytes(n){if(n<1024)return n+" B";if(n<1024*1024)return (n/1024).toFixed(0)+" KB";return (n/1024/1024).toFixed(1)+" MB";}
function _isImage(mt){return (mt||"").startsWith("image/");}
function _brDate(s){if(!s)return"";const [a,m,d]=s.split("-");return `${d}/${m}/${a}`;}

async function renderDiario(c){
  c.innerHTML=`<div class="pg-head"><div class="pg-tit">📓 DIÁRIO DE BORDO</div><button id="diNew" class="btn-primary">+ NOVA ENTRADA</button></div>
    <div style="font-size:12px;color:var(--text-mute);padding:0 14px 10px">Anote o que rolou no seu dia de manobra. Anexe fotos, prints, arquivos. <b>Tudo privado</b> — só você vê.</div>
    <div class="pg-body" id="diBody"><div style="color:var(--muted)">Carregando...</div></div>`;
  document.getElementById("diNew").onclick=()=>openDiarioForm();
  if(!await requireAuth()){document.getElementById("diBody").innerHTML='<div style="color:var(--muted);padding:20px;text-align:center">Faça login pra ver seu diário.</div>';return;}
  try{
    const r=await apiFetch("/api/diario");
    const d=await r.json();
    const ents=(d.entradas||[]).slice().sort((a,b)=>(b.data||"").localeCompare(a.data||"")||(Number(b.id)||0)-(Number(a.id)||0));
    const body=document.getElementById("diBody");
    if(!ents.length){body.innerHTML='<div style="color:var(--muted);padding:20px;text-align:center">Nenhuma entrada ainda.<br/>Toque em <b>+ NOVA ENTRADA</b> pra começar.</div>';return;}
    const _tok=getToken();
    body.innerHTML=ents.map(e=>{
      const anx=(e.anexos||[]);
      const thumbs=anx.map((a,i)=>{
        const url=a.key?`/api/diario/anexo?key=${encodeURIComponent(a.key)}&t=${encodeURIComponent(_tok)}`:(a.b64?`data:${a.mimetype};base64,${a.b64}`:"");
        if(_isImage(a.mimetype)){
          return `<img class="di-thumb" data-eid="${e.id}" data-idx="${i}" src="${url}" style="width:80px;height:80px;object-fit:cover;border-radius:8px;cursor:pointer;border:1px solid var(--border)" loading="lazy"/>`;
        }
        return `<a href="${url}" download="${escapeHtml(a.nome||"arquivo")}" style="display:flex;flex-direction:column;align-items:center;justify-content:center;width:80px;height:80px;background:var(--card);border:1px solid var(--border);border-radius:8px;text-decoration:none;color:var(--text);font-size:10px;padding:6px;text-align:center;gap:4px"><div style="font-size:24px">📄</div><div style="overflow:hidden;text-overflow:ellipsis;white-space:nowrap;width:100%">${escapeHtml((a.nome||"arquivo").slice(0,18))}</div></a>`;
      }).join("");
      return `<div class="lst-item" style="flex-direction:column;align-items:stretch;gap:8px">
        <div style="display:flex;justify-content:space-between;gap:10px;align-items:flex-start">
          <div style="flex:1;min-width:0">
            <div style="font-weight:600;font-size:14px;color:var(--neon)">📓 ${escapeHtml(_brDate(e.data))}</div>
            ${e.texto?`<div style="margin-top:6px;color:var(--text);font-size:13px;line-height:1.5;white-space:pre-wrap">${escapeHtml(e.texto)}</div>`:""}
          </div>
          <button class="btn-danger" data-id="${e.id}">Excluir</button>
        </div>
        ${thumbs?`<div style="display:flex;gap:6px;flex-wrap:wrap;margin-top:4px">${thumbs}</div>`:""}
      </div>`;
    }).join("");
    body.querySelectorAll("button.btn-danger").forEach(b=>{
      b.onclick=async()=>{
        if(!confirm("Excluir esta entrada do diário?"))return;
        const novos=ents.filter(x=>String(x.id)!==String(b.dataset.id));
        await apiFetch("/api/diario",{method:"POST",body:JSON.stringify({entradas:novos})});
        renderDiario(c);
      };
    });
    body.querySelectorAll(".di-thumb").forEach(im=>{
      im.onclick=()=>{
        const ent=ents.find(x=>String(x.id)===String(im.dataset.eid));
        if(!ent)return;
        const a=ent.anexos[im.dataset.idx];
        if(!a)return;
        const ov=document.createElement("div");
        ov.style.cssText="position:fixed;inset:0;background:rgba(0,0,0,.92);z-index:9999;display:flex;align-items:center;justify-content:center;padding:20px;cursor:zoom-out";
        ov.innerHTML=`<img src="data:${a.mimetype};base64,${a.b64}" style="max-width:100%;max-height:100%;object-fit:contain"/>`;
        ov.onclick=()=>document.body.removeChild(ov);
        document.body.appendChild(ov);
      };
    });
  }catch(e){if(e.message!=="auth")document.getElementById("diBody").innerHTML='<div style="color:#ff8a8a">Erro: '+escapeHtml(e.message)+'</div>';}
}

function openDiarioForm(dataPre){
  let pendentes=[]; // {nome, mimetype, b64, size}
  openModal("Nova Entrada do Diário 📓",`
    <div style="font-size:12px;color:var(--neon);margin-bottom:10px;padding:8px 10px;background:rgba(0,230,118,.10);border-radius:8px">🔒 Privado — só você vê esta entrada.</div>
    <div class="modal-fld"><label>Data</label><input id="diData" type="date" value="${dataPre||new Date().toISOString().slice(0,10)}"/></div>
    <div class="modal-fld"><label>O que aconteceu?</label><textarea id="diTxt" rows="5" placeholder="Ex.: Manobra do trem 1234, problema na chave 7..."></textarea></div>
    <div style="margin-bottom:10px">
      <div style="font-size:12px;color:var(--text-mute);margin-bottom:6px">Anexos (fotos, prints, PDFs)</div>
      <div style="display:grid;grid-template-columns:1fr 1fr 1fr;gap:6px">
        <button type="button" id="diCam" class="btn-secondary" style="font-size:12px;padding:10px 4px">📷 Câmera</button>
        <button type="button" id="diImg" class="btn-secondary" style="font-size:12px;padding:10px 4px">🖼️ Galeria</button>
        <button type="button" id="diArq" class="btn-secondary" style="font-size:12px;padding:10px 4px">📎 Arquivo</button>
      </div>
      <input type="file" id="diInpCam" accept="image/*" capture="environment" style="display:none"/>
      <input type="file" id="diInpImg" accept="image/*" multiple style="display:none"/>
      <input type="file" id="diInpArq" accept=".pdf,.txt,.doc,.docx" multiple style="display:none"/>
      <div id="diPrev" style="display:flex;gap:6px;flex-wrap:wrap;margin-top:10px"></div>
    </div>
    <div style="display:flex;gap:10px;justify-content:flex-end">
      <button class="btn-secondary" onclick="closeModal()">Cancelar</button>
      <button id="diSave" class="btn-primary">SALVAR</button>
    </div>
  `,()=>{
    const prev=document.getElementById("diPrev");
    function redrawPrev(){
      if(!pendentes.length){prev.innerHTML="";return;}
      prev.innerHTML=pendentes.map((a,i)=>{
        const thumb=_isImage(a.mimetype)
          ?`<img src="data:${a.mimetype};base64,${a.b64}" style="width:64px;height:64px;object-fit:cover;border-radius:6px"/>`
          :`<div style="width:64px;height:64px;display:flex;align-items:center;justify-content:center;background:var(--card);border:1px solid var(--border);border-radius:6px;font-size:24px">📄</div>`;
        return `<div style="position:relative">${thumb}
          <button data-i="${i}" class="rmAnx" style="position:absolute;top:-6px;right:-6px;width:22px;height:22px;border-radius:50%;background:#ff5555;color:#fff;border:none;cursor:pointer;font-size:14px;line-height:1">×</button>
          <div style="font-size:9px;color:var(--muted);text-align:center;margin-top:2px">${_formatBytes(a.size)}</div>
        </div>`;
      }).join("");
      prev.querySelectorAll(".rmAnx").forEach(b=>b.onclick=()=>{pendentes.splice(Number(b.dataset.i),1);redrawPrev();});
    }
    async function adicionar(file, comprimir){
      try{
        const a = comprimir && _isImage(file.type)
          ? await _compressImage(file)
          : await _fileToB64(file);
        a.nome = file.name || (comprimir?"foto.jpg":"arquivo");
        if(a.size > 8*1024*1024){showToast("❌ Arquivo grande demais ("+_formatBytes(a.size)+", máx 8 MB)");return;}
        pendentes.push(a);
        redrawPrev();
      }catch(e){showToast("❌ Falha ao processar: "+e.message);}
    }
    const inpCam=document.getElementById("diInpCam");
    const inpImg=document.getElementById("diInpImg");
    const inpArq=document.getElementById("diInpArq");
    document.getElementById("diCam").onclick=()=>inpCam.click();
    document.getElementById("diImg").onclick=()=>inpImg.click();
    document.getElementById("diArq").onclick=()=>inpArq.click();
    inpCam.onchange=async()=>{for(const f of inpCam.files)await adicionar(f,true);inpCam.value="";};
    inpImg.onchange=async()=>{for(const f of inpImg.files)await adicionar(f,true);inpImg.value="";};
    inpArq.onchange=async()=>{for(const f of inpArq.files)await adicionar(f,false);inpArq.value="";};
    document.getElementById("diSave").onclick=async()=>{
      const data=document.getElementById("diData").value;
      const texto=document.getElementById("diTxt").value.trim();
      if(!data){showToast("Data é obrigatória");return;}
      if(!texto && !pendentes.length){showToast("Escreva algo ou anexe um arquivo");return;}
      const novaEntrada={id:Date.now(),data,texto,anexos:pendentes};
      const r=await apiFetch("/api/diario");
      const d=await r.json();
      const novos=(d.entradas||[]).concat([novaEntrada]);
      const r2=await apiFetch("/api/diario",{method:"POST",body:JSON.stringify({entradas:novos})});
      if(r2.ok){closeModal();showToast("📓 Entrada salva");if(S.section==="diario")renderDiario(document.getElementById("content"));}
      else{const dd=await r2.json().catch(()=>({}));showToast("❌ "+(dd.error||"Falha ao salvar"));}
    };
  });
}

// ===== CHAT =====
let CHAT_CONV=null, CHAT_POLL=null, CHAT_LAST_TS=0;
function _stopChatPoll(){if(CHAT_POLL){clearInterval(CHAT_POLL);CHAT_POLL=null;}}
function avatarFor(nome){return (nome||"?").trim().split(/\s+/).slice(0,2).map(s=>s[0]||"").join("").toUpperCase()||"?";}
function _relTime(ts){const s=Math.max(0,Math.floor(Date.now()/1000-ts));if(s<60)return"agora";if(s<3600)return"há "+Math.floor(s/60)+"min";if(s<86400)return"há "+Math.floor(s/3600)+"h";return"há "+Math.floor(s/86400)+"d";}
async function renderChat(c){
  c.innerHTML=`<div id="chatRoot" class="chat-wrap"><div style="padding:30px;color:var(--muted)">Carregando...</div></div>`;
  if(!await requireAuth()){document.getElementById("chatRoot").innerHTML='<div style="padding:30px;color:var(--muted);text-align:center;width:100%">Faça login para usar o chat.</div>';return;}
  await drawChatList();
}
async function drawChatList(){
  const root=document.getElementById("chatRoot");if(!root)return;
  let convs=[],usuarios=[];
  try{const r=await apiFetch("/api/chat/conversas");convs=(await r.json()).conversas||[];}catch(e){if(e.message==="auth")return;}
  try{const r=await apiFetch("/api/chat/usuarios");usuarios=(await r.json()).usuarios||[];}catch(e){}
  const totUnread=convs.reduce((s,c)=>s+(c.nao_lidas||0),0);
  updateChatBadge(totUnread);
  // mapeia matricula -> conversa 1a1 existente
  const conv1a1ByMat={};
  convs.forEach(c=>{
    if(c.tipo!=="grupo" && (c.participantes||[]).length===2){
      const outra=(c.participantes||[]).find(m=>m!==CURRENT_USER.matricula);
      if(outra)conv1a1ByMat[outra]=c;
    }
  });
  root.innerHTML=`
    <div class="chat-list">
      <div class="chat-list-head"><span>Conversas</span><button id="newConv" class="btn-primary" style="padding:4px 10px;font-size:11px">+ Grupo</button></div>
      <div id="convList">${convs.length?convs.map(c=>{
        const lst=c.ultima?(c.ultima.texto||(c.ultima.anexo?"📎 anexo":"")).slice(0,40):"Nova conversa";
        const tag=c.tipo==="grupo"?"👥 ":"";
        return `<div class="chat-conv ${CHAT_CONV&&CHAT_CONV.id===c.id?"active":""}" data-id="${c.id}">
          <div class="av">${escapeHtml(avatarFor(c.nome))}</div>
          <div class="meta"><div class="nm">${tag}${escapeHtml(c.nome)}</div><div class="lst">${escapeHtml(lst)}</div></div>
          ${c.nao_lidas?`<div class="nlb">${c.nao_lidas}</div>`:""}
        </div>`;
      }).join(""):'<div style="padding:14px;color:var(--muted);font-size:12px;text-align:center">Nenhuma conversa ainda.<br/>Toque num colega abaixo pra começar.</div>'}</div>
      <div class="chat-list-head" style="margin-top:8px;border-top:1px solid var(--border);padding-top:12px"><span>Colegas da Turma</span></div>
      <div id="colegasList">${usuarios.length?usuarios.map(u=>{
        const conv=conv1a1ByMat[u.matricula];
        const unread=conv?conv.nao_lidas||0:0;
        const status=u.online?'<span class="presence on" title="online"></span>':'<span class="presence off" title="offline"></span>';
        const sub=u.online?"online agora":(u.last_seen?"visto "+_relTime(u.last_seen):"offline");
        return `<div class="chat-conv" data-mat="${escapeHtml(u.matricula)}" title="Conversar com ${escapeHtml(u.nome)}">
          <div class="av" style="position:relative">${escapeHtml(avatarFor(u.nome))}${status}</div>
          <div class="meta"><div class="nm">${escapeHtml(u.nome)}</div><div class="lst">${conv?"💬 ":""}${sub}</div></div>
          ${unread?`<div class="nlb">${unread}</div>`:""}
        </div>`;
      }).join(""):'<div style="padding:14px;color:var(--muted);font-size:12px;text-align:center">Nenhum colega aprovado ainda.</div>'}</div>
    </div>
    <div class="chat-pane" id="chatPane">
      ${CHAT_CONV?"":'<div class="chat-empty">Toque numa conversa ou num colega à esquerda.</div>'}
    </div>`;
  document.getElementById("newConv").onclick=openNovaConversa;
  document.querySelectorAll(".chat-conv[data-id]").forEach(el=>{el.onclick=()=>{const c=convs.find(x=>x.id===el.dataset.id);if(c)abrirConversa(c);};});
  document.querySelectorAll(".chat-conv[data-mat]").forEach(el=>{
    el.onclick=async()=>{
      const mat=el.dataset.mat;
      const existing=conv1a1ByMat[mat];
      if(existing){abrirConversa(existing);return;}
      const u=usuarios.find(x=>x.matricula===mat);if(!u)return;
      try{
        const r=await apiFetch("/api/chat/conversa",{method:"POST",body:JSON.stringify({participantes:[mat],nome:""})});
        const d=await r.json();
        if(r.ok){await drawChatList();abrirConversa({id:d.id,tipo:"1a1",nome:u.nome,participantes:[mat,CURRENT_USER.matricula]});}
      }catch(e){}
    };
  });
  if(CHAT_CONV){const cur=convs.find(x=>x.id===CHAT_CONV.id);if(cur){CHAT_CONV=cur;await abrirConversa(cur,true);}}
}
function _isMobileChat(){return window.matchMedia("(max-width:720px)").matches;}
function _showChatPane(){const list=document.querySelector(".chat-list"),pane=document.getElementById("chatPane");if(!list||!pane)return;if(_isMobileChat()){list.classList.add("hide-mobile");pane.classList.remove("hide-mobile");}else{list.classList.remove("hide-mobile");pane.classList.remove("hide-mobile");}}
function _showChatList(){const list=document.querySelector(".chat-list"),pane=document.getElementById("chatPane");if(!list||!pane)return;if(_isMobileChat()){list.classList.remove("hide-mobile");pane.classList.add("hide-mobile");}else{list.classList.remove("hide-mobile");pane.classList.remove("hide-mobile");}}
async function abrirConversa(c,jaListou){
  CHAT_CONV=c;CHAT_LAST_TS=0;
  if(!jaListou){document.querySelectorAll(".chat-conv").forEach(el=>el.classList.toggle("active",el.dataset.id===c.id));}
  const pane=document.getElementById("chatPane");
  _showChatPane();
  const sub=c.tipo==="grupo"?(c.participantes||[]).length+" participantes":"Conversa privada";
  pane.innerHTML=`
    <div class="chat-head">
      <button class="btn-secondary" id="convBack" style="padding:4px 10px;font-size:14px;margin-right:8px">←</button>
      <div style="flex:1;min-width:0"><div class="nm">${c.tipo==="grupo"?"👥 ":""}${escapeHtml(c.nome)}</div><div class="sub">${escapeHtml(sub)}</div></div>
      <button class="btn-secondary" id="convExit" style="padding:4px 10px;font-size:11px">Sair</button>
    </div>
    <div class="chat-msgs" id="chatMsgs"><div style="color:var(--muted);text-align:center;padding:20px">Carregando...</div></div>
    <div class="chat-input">
      <button id="chatAttach" class="btn-secondary" title="Anexar" style="padding:8px 10px">📎</button>
      <textarea id="chatTxt" placeholder="Mensagem..." rows="1"></textarea>
      <button id="chatSend" class="btn-primary" style="padding:8px 14px">Enviar</button>
      <input type="file" id="chatFile" accept="image/*,.pdf,.docx,.txt" style="display:none"/>
    </div>`;
  document.getElementById("convBack").onclick=()=>{CHAT_CONV=null;_stopChatPoll();_showChatList();const p=document.getElementById("chatPane");if(p)p.innerHTML='<div class="chat-empty">Toque numa conversa ou num colega à esquerda.</div>';};
  document.getElementById("convExit").onclick=async()=>{
    if(!confirm(c.tipo==="grupo"?"Sair deste grupo?":"Apagar esta conversa?"))return;
    await apiFetch("/api/chat/conversa/"+c.id,{method:"DELETE"});CHAT_CONV=null;_stopChatPoll();_showChatList();await drawChatList();
  };
  document.getElementById("chatAttach").onclick=()=>document.getElementById("chatFile").click();
  document.getElementById("chatFile").onchange=enviarComAnexo;
  document.getElementById("chatSend").onclick=enviarMsg;
  document.getElementById("chatTxt").onkeydown=(e)=>{if(e.key==="Enter"&&!e.shiftKey){e.preventDefault();enviarMsg();}};
  await carregarMsgs(true);
  _stopChatPoll();
  CHAT_POLL=setInterval(()=>{if(S.section==="chat"&&CHAT_CONV)carregarMsgs(false);else _stopChatPoll();},4000);
}
const CHAT_ANEXO_CACHE={};
async function _loadAnexoBlob(cid,mid){
  const k=cid+"/"+mid;
  if(CHAT_ANEXO_CACHE[k])return CHAT_ANEXO_CACHE[k];
  try{
    const r=await apiFetch("/api/chat/conversa/"+cid+"/anexo/"+mid);
    if(!r.ok)return null;
    const blob=await r.blob();
    const url=URL.createObjectURL(blob);
    CHAT_ANEXO_CACHE[k]=url;return url;
  }catch(e){return null;}
}
async function _hydrateAnexos(cid,box){
  box.querySelectorAll("[data-anx-mid]").forEach(async el=>{
    const mid=el.dataset.anxMid;const url=await _loadAnexoBlob(cid,mid);if(!url)return;
    if(el.tagName==="IMG"){el.src=url;}
    else{const a=el.querySelector("a");if(a){a.href=url;a.removeAttribute("data-pending");}}
  });
}
async function carregarMsgs(scroll,force){
  if(!CHAT_CONV)return;
  try{
    const r=await apiFetch("/api/chat/conversa/"+CHAT_CONV.id+"/mensagens");
    const msgs=(await r.json()).mensagens||[];
    const top=msgs[msgs.length-1];
    const newTs=top?top.ts:0;
    if(newTs===CHAT_LAST_TS && !scroll && !force)return;
    CHAT_LAST_TS=newTs;
    const box=document.getElementById("chatMsgs");if(!box)return;
    const me=CURRENT_USER&&CURRENT_USER.matricula;
    box.innerHTML=msgs.length?msgs.map(m=>{
      const mine=m.autor_mat===me;
      const dt=new Date((m.ts||0)*1000);
      const hh=dt.toLocaleTimeString("pt-BR",{hour:"2-digit",minute:"2-digit"});
      const dd=dt.toLocaleDateString("pt-BR",{day:"2-digit",month:"2-digit"});
      let anexoHtml="";
      if(m.anexo&&m.anexo.tem){
        const isImg=(m.anexo.mimetype||"").startsWith("image/");
        anexoHtml=isImg
          ? `<img class="anximg" data-anx-mid="${m.id}" alt="${escapeHtml(m.anexo.nome)}"/>`
          : `<div class="anx" data-anx-mid="${m.id}">📎 <a href="#" data-pending="1" download="${escapeHtml(m.anexo.nome)}" target="_blank">${escapeHtml(m.anexo.nome)}</a></div>`;
      }
      return `<div class="chat-msg ${mine?"mine":""}">
        ${!mine&&CHAT_CONV.tipo==="grupo"?`<div class="au">${escapeHtml(m.autor_nome||"")}</div>`:""}
        ${m.texto?`<div class="tx">${escapeHtml(m.texto)}</div>`:""}
        ${anexoHtml}
        <div class="ts"><span>${dd} ${hh}</span><span class="star ${m.importante?"on":""}" data-mid="${m.id}" title="${m.importante?"Importante (mantém)":"Marcar como importante"}">★</span></div>
      </div>`;
    }).join(""):'<div style="color:var(--muted);text-align:center;padding:20px">Sem mensagens. Diga oi 👋</div>';
    box.querySelectorAll(".star").forEach(s=>{s.onclick=async()=>{await apiFetch("/api/chat/mensagem/"+CHAT_CONV.id+"/"+s.dataset.mid+"/importante",{method:"POST"});carregarMsgs(true,true);};});
    _hydrateAnexos(CHAT_CONV.id,box);
    if(scroll)box.scrollTop=box.scrollHeight;
    await apiFetch("/api/chat/conversa/"+CHAT_CONV.id+"/lida",{method:"POST"}).catch(()=>{});
    refreshChatBadge();
  }catch(e){if(e.message==="auth")_stopChatPoll();}
}
async function enviarMsg(){
  const ta=document.getElementById("chatTxt");if(!ta)return;
  const t=ta.value.trim();if(!t)return;
  ta.value="";
  await apiFetch("/api/chat/conversa/"+CHAT_CONV.id+"/mensagem",{method:"POST",body:JSON.stringify({texto:t})});
  await carregarMsgs(true);await drawChatList();
}
async function enviarComAnexo(){
  const fi=document.getElementById("chatFile");const f=fi.files&&fi.files[0];if(!f)return;
  if(f.size>50*1024*1024){showToast("Anexo > 50MB");fi.value="";return;}
  const ta=document.getElementById("chatTxt");const t=ta?ta.value.trim():"";
  showToast("Enviando "+f.name+"...");
  const b64=await new Promise(res=>{const r=new FileReader();r.onload=()=>res(r.result.split(",")[1]);r.readAsDataURL(f);});
  const r=await apiFetch("/api/chat/conversa/"+CHAT_CONV.id+"/mensagem",{method:"POST",body:JSON.stringify({texto:t,anexo:{nome:f.name,mimetype:f.type,data:b64}})});
  if(r.ok){if(ta)ta.value="";fi.value="";await carregarMsgs(true);await drawChatList();}
  else{const d=await r.json();showToast("❌ "+(d.error||"Falha"));}
}
async function openNovaConversa(){
  let usuarios=[];
  try{const r=await apiFetch("/api/chat/usuarios");usuarios=(await r.json()).usuarios||[];}catch(e){return;}
  if(!usuarios.length){openModal("Nova conversa","<div style='color:var(--muted);text-align:center;padding:20px'>Nenhum outro usuário aprovado ainda.</div>",()=>{});return;}
  openModal("Nova conversa",`
    <div class="modal-fld"><label>Nome do grupo (opcional — deixe vazio para conversa 1 a 1)</label><input id="ncNome" placeholder="Ex: Resgate Linha 6"/></div>
    <div class="modal-fld"><label>Selecione os colegas:</label>
      <div id="ncList" style="max-height:240px;overflow:auto;border:1px solid var(--border-soft);border-radius:8px;padding:6px">
        ${usuarios.map(u=>`<label style="display:flex;align-items:center;gap:8px;padding:6px 8px;cursor:pointer;border-radius:6px"><input type="checkbox" value="${escapeHtml(u.matricula)}"/> <span>${escapeHtml(u.nome)} <span style="color:var(--muted);font-size:11px">(${escapeHtml(u.matricula)})</span></span></label>`).join("")}
      </div>
    </div>
    <div style="display:flex;gap:10px;justify-content:flex-end">
      <button class="btn-secondary" onclick="closeModal()">Cancelar</button>
      <button id="ncSave" class="btn-primary">Iniciar</button>
    </div>
  `,()=>{
    document.getElementById("ncSave").onclick=async()=>{
      const sel=Array.from(document.querySelectorAll("#ncList input:checked")).map(i=>i.value);
      const nome=document.getElementById("ncNome").value.trim();
      if(!sel.length){showToast("Selecione pelo menos um colega");return;}
      const r=await apiFetch("/api/chat/conversa",{method:"POST",body:JSON.stringify({participantes:sel,nome})});
      const d=await r.json();
      if(r.ok){closeModal();await drawChatList();const conv={id:d.id,tipo:sel.length>=2?"grupo":"1a1",nome:nome||usuarios.find(u=>u.matricula===sel[0]).nome,participantes:sel.concat([CURRENT_USER.matricula])};abrirConversa(conv);}
      else{showToast("❌ "+(d.error||"Falha"));}
    };
  });
}
function updateChatBadge(n){const b=document.getElementById("chatBadge");if(!b)return;if(n>0){b.textContent=n>9?"9+":n;b.style.display="";}else{b.style.display="none";}}
async function refreshChatBadge(){
  if(!CURRENT_USER)return;
  try{const r=await apiFetch("/api/chat/conversas");const d=await r.json();const tot=(d.conversas||[]).reduce((s,c)=>s+(c.nao_lidas||0),0);updateChatBadge(tot);}catch(e){}
}
setInterval(()=>{if(CURRENT_USER&&S.section!=="chat")refreshChatBadge();},15000);

async function openDia(k){
  if(!await requireAuth())return;
  const [a,m,d]=k.split("-");
  const dt=new Date(+a,+m-1,+d);
  const dataBr=`${d}/${m}/${a}`;
  const dow=["Domingo","Segunda","Terça","Quarta","Quinta","Sexta","Sábado"][dt.getDay()];
  const fol=isFolga(dt);
  const ferNome=FER[k]||"";
  const ferBlock=ferNome?`<div style="margin-bottom:10px;padding:10px 14px;background:rgba(124,58,237,.14);border:1px solid #7c3aed55;border-radius:10px;font-size:13px;color:var(--purple);font-weight:600">🎉 Feriado: ${ferNome}</div>`:"";
  const filterAtivoDia=Array.isArray(S.evFilter)&&S.evFilter.length>0;
  const filterChips=filterAtivoDia
    ? S.evFilter.map(t=>{const ti=evTipoInfo(t);return `<span style="display:inline-flex;align-items:center;gap:4px;background:var(--card-2);border:1px solid var(--border-soft);border-radius:999px;padding:2px 8px;font-size:11px;color:var(--text-dim)"><span style="width:8px;height:8px;border-radius:50%;background:${ti.cor}"></span><span>${ti.emoji}</span><span>${escapeHtml(ti.label)}</span></span>`}).join("")
    : "";
  const filterBanner=filterAtivoDia
    ? `<div id="diaFilterBanner" style="margin-bottom:10px;padding:8px 12px;background:rgba(0,230,118,.08);border:1px solid #3be79955;border-radius:8px;font-size:12px;color:var(--text-dim);display:flex;align-items:center;gap:8px;flex-wrap:wrap"><span style="font-weight:600;color:var(--neon)">🔎 Filtro ativo:</span>${filterChips}<button type="button" id="diaClearFilter" style="margin-left:auto;background:transparent;border:1px solid var(--border-soft);color:var(--text-dim);padding:3px 10px;border-radius:999px;font-size:11px;cursor:pointer">Limpar</button></div>`
    : "";
  openModal(`${dow}, ${dataBr}`,`
    ${ferBlock}
    <div style="margin-bottom:12px;padding:8px 12px;background:${fol?"rgba(59,231,153,.1)":"rgba(255,138,76,.1)"};border-radius:8px;font-size:12px;color:${fol?"var(--neon)":"var(--orange)"}">${fol?"🟢 Folga":"🟠 Trabalho"}</div>
    ${filterBanner}
    <div id="diaList" style="margin-bottom:14px;max-height:240px;overflow:auto"><div style="color:var(--muted);font-size:13px">Carregando...</div></div>
    <div style="display:grid;grid-template-columns:1fr 1fr;gap:8px">
      <button id="diaEv" class="btn-primary" style="font-size:12px;padding:10px 6px">📢 Mural</button>
      <button id="diaPess" class="btn-secondary" style="font-size:12px;padding:10px 6px">🔒 Meus Eventos</button>
      <button id="diaDiario" class="btn-secondary" style="font-size:12px;padding:10px 6px">📓 Diário</button>
      <button id="diaNota" class="btn-secondary" style="font-size:12px;padding:10px 6px">📝 Nota</button>
    </div>
  `,async()=>{
    async function refresh(){
      const list=document.getElementById("diaList");
      try{
        const [rEv,rPess,rMem,rDi]=await Promise.all([apiFetch("/api/mem/eventos"),apiFetch("/api/eventos-pessoais"),apiFetch("/api/memoria"),apiFetch("/api/diario")]);
        const dEv=await rEv.json();const dPess=await rPess.json();const dMem=await rMem.json();const dDi=await rDi.json();
        const evs=(dEv.eventos||[]).filter(e=>e.data===k).filter(passaFiltroEv);
        const evsPess=(dPess.eventos||[]).filter(e=>e.data===k).filter(passaFiltroEv);
        const notas=(dMem.pessoal||[]).filter(p=>(p.texto||"").startsWith(`[DIA ${k}]`));
        const diarios=(dDi.entradas||[]).filter(d=>d.data===k);
        const renderEv=(e,pess)=>{
          const ti=evTipoInfo(e.tipo);
          const chip=`<span class="cal-legend-item" style="font-size:11px;padding:2px 8px"><span class="cl-dot" style="background:${ti.cor}"></span><span class="cl-emo">${ti.emoji}</span><span class="cl-lbl">${escapeHtml(ti.label)}</span></span>`;
          const tag=pess?'<span style="color:var(--neon);font-size:10px;background:rgba(0,230,118,.15);padding:2px 8px;border-radius:999px">🔒 PRIVADO</span>':'';
          return `<div class="lst-item" style="padding:8px 10px;margin-bottom:6px;border-left:3px solid ${ti.cor}">
            <div style="flex:1;min-width:0">
              <div style="display:flex;align-items:center;flex-wrap:wrap;gap:6px;margin-bottom:5px">${chip}${tag}</div>
              <div style="font-weight:600;font-size:13px;color:var(--text)">${escapeHtml(e.titulo||"")}</div>
              ${e.hora?`<div style="color:var(--muted);font-size:11px;margin-top:2px">⏰ ${escapeHtml(e.hora)}</div>`:""}
              ${e.descricao?`<div style="font-size:12px;color:var(--text);margin-top:3px">${escapeHtml(e.descricao)}</div>`:""}
              <button data-eid="${e.id}" data-pess="${pess?1:0}" class="ev-del" style="margin-top:6px;background:transparent;border:1px solid #ff6b6b55;color:#ff8a8a;padding:3px 8px;border-radius:6px;font-size:11px;cursor:pointer">🗑️ Excluir</button>
            </div>
          </div>`;
        };
        let html="";
        if(evs.length){html+=`<div style="font-size:11px;color:var(--text-mute);letter-spacing:1px;margin-bottom:6px">📋 MURAL DA TURMA</div>`;
          html+=evs.map(e=>renderEv(e,false)).join("");
        }
        if(evsPess.length){html+=`<div style="font-size:11px;color:var(--neon);letter-spacing:1px;margin:10px 0 6px">🔒 MEUS EVENTOS</div>`;
          html+=evsPess.map(e=>renderEv(e,true)).join("");
        }
        if(notas.length){html+=`<div style="font-size:11px;color:var(--text-mute);letter-spacing:1px;margin:10px 0 6px">NOTAS</div>`;
          html+=notas.map(n=>`<div class="lst-item" style="padding:8px 10px;margin-bottom:6px;border-left:3px solid #94a3b8">
            <div style="flex:1;min-width:0">
              <div style="font-size:12px;color:var(--text)">${escapeHtml((n.texto||"").replace(`[DIA ${k}] `,""))}</div>
              <button data-nid="${n.id}" class="nota-del" style="margin-top:6px;background:transparent;border:1px solid #ff6b6b55;color:#ff8a8a;padding:3px 8px;border-radius:6px;font-size:11px;cursor:pointer">🗑️ Excluir nota</button>
            </div>
          </div>`).join("");
        }
        if(diarios.length){html+=`<div style="font-size:11px;color:var(--neon);letter-spacing:1px;margin:10px 0 6px">📓 DIÁRIO DE BORDO</div>`;
          html+=diarios.map(di=>{
            const anx=(di.anexos||[]).length;
            const anxBadge=anx?`<span style="font-size:10px;color:var(--muted);margin-left:6px">📎 ${anx}</span>`:"";
            const txt=(di.texto||"").trim();
            const full=escapeHtml(txt||"(sem texto)");
            const needTrunc=txt.length>140;
            const preview=needTrunc?escapeHtml(txt.slice(0,140))+"…":full;
            return `<div class="lst-item" style="padding:8px 10px;margin-bottom:6px;border-left:3px solid var(--neon)">
              <div style="flex:1;min-width:0">
                <div class="di-txt" style="font-size:12px;color:var(--text);white-space:pre-wrap" data-full="${full.replace(/"/g,'&quot;')}" data-short="${preview.replace(/"/g,'&quot;')}" data-exp="0">${preview}</div>
                ${needTrunc?`<button class="di-expand" style="background:none;border:none;color:var(--neon);font-size:11px;cursor:pointer;padding:4px 0;margin-top:2px">ver mais ▼</button>`:""}`+anxBadge+`</div>
                <button data-did="${di.id}" class="di-del" style="margin-top:6px;background:transparent;border:1px solid #ff6b6b55;color:#ff8a8a;padding:3px 8px;border-radius:6px;font-size:11px;cursor:pointer">🗑️ Excluir entrada</button>
              </div>
            </div>`;
          }).join("");
        }
        list.innerHTML=html||`<div style="color:var(--muted);font-size:13px;text-align:center;padding:14px">Nada agendado neste dia.</div>`;
        list.querySelectorAll(".ev-del").forEach(b=>{
          b.onclick=async()=>{
            if(!confirm("Excluir este evento?"))return;
            const ep=b.dataset.pess==="1"?"/api/eventos-pessoais":"/api/mem/eventos";
            const r2=await apiFetch(ep);const d2=await r2.json();
            const novos=(d2.eventos||[]).filter(e=>String(e.id)!==String(b.dataset.eid));
            await apiFetch(ep,{method:"POST",body:JSON.stringify({eventos:novos})});
            await carregarEventosCache();showToast("Excluído");refresh();render();
          };
        });
        list.querySelectorAll(".nota-del").forEach(b=>{
          b.onclick=async()=>{
            if(!confirm("Excluir esta nota?"))return;
            const r=await apiFetch("/api/memoria/pessoal/"+encodeURIComponent(b.dataset.nid),{method:"DELETE"});
            if(r.ok){showToast("Nota excluída");refresh();}
            else showToast("❌ Falha ao excluir");
          };
        });
        list.querySelectorAll(".di-expand").forEach(b=>{
          b.onclick=()=>{
            const div=b.previousElementSibling;
            if(!div)return;
            const exp=div.dataset.exp==="1";
            div.innerHTML=exp?div.dataset.short:div.dataset.full;
            div.dataset.exp=exp?"0":"1";
            b.textContent=exp?"ver mais ▼":"ver menos ▲";
          };
        });
        list.querySelectorAll(".di-del").forEach(b=>{
          b.onclick=async()=>{
            if(!confirm("Excluir esta entrada do diário?"))return;
            const r=await apiFetch("/api/diario");const d=await r.json();
            const novos=(d.entradas||[]).filter(x=>String(x.id)!==String(b.dataset.did));
            const r2=await apiFetch("/api/diario",{method:"POST",body:JSON.stringify({entradas:novos})});
            if(r2.ok){showToast("Entrada excluída");refresh();}
            else showToast("❌ Falha ao excluir");
          };
        });
      }catch(e){if(e.message!=="auth")list.innerHTML='<div style="color:#ff8a8a">Erro ao carregar.</div>';}
    }
    refresh();
    document.getElementById("diaEv").onclick=()=>{closeModal();openEventoForm(k);};
    document.getElementById("diaPess").onclick=()=>{closeModal();openEventoForm(k,{pessoal:true});};
    document.getElementById("diaDiario").onclick=()=>{closeModal();openDiarioForm(k);};
    document.getElementById("diaNota").onclick=()=>{
      const t=prompt(`Nota para ${dataBr}:`);
      if(!t||!t.trim())return;
      apiFetch("/api/memoria/pessoal",{method:"POST",body:JSON.stringify({texto:`[DIA ${k}] ${t.trim()}`})}).then(()=>{showToast("✅ Nota salva");refresh();});
    };
    const cf=document.getElementById("diaClearFilter");
    if(cf)cf.onclick=()=>{
      clearEvFilter();
      const banner=document.getElementById("diaFilterBanner");
      if(banner)banner.remove();
      refresh();
      render();
    };
  });
}
function openEventoForm(dataPre,opts){
  opts=opts||{};
  const pessoal=!!opts.pessoal;
  const endpoint=pessoal?"/api/eventos-pessoais":"/api/mem/eventos";
  const titulo=pessoal?"Novo Evento Pessoal 🔒":"Novo Post no Mural";
  const aviso=pessoal
    ?'<div style="font-size:12px;color:var(--neon);margin-bottom:10px;padding:8px 10px;background:rgba(0,230,118,.10);border-radius:8px">🔒 Este evento é privado. Só você vai ver.</div>'
    :'<div style="font-size:12px;color:#fbbf24;margin-bottom:10px;padding:8px 10px;background:rgba(251,191,36,.10);border-radius:8px">📢 Este post vai pro mural e a turma toda recebe notificação.</div>';
  const tiposOpts=Object.entries(EVENTO_TIPOS).map(([k,v])=>`<option value="${k}">${v.emoji} ${v.label}</option>`).join("");
  openModal(titulo,`
    ${aviso}
    <div class="modal-fld"><label>Tipo</label>
      <select id="eTipo" style="width:100%;padding:10px;background:var(--card);color:var(--text);border:1px solid var(--border);border-radius:8px;font-size:14px">${tiposOpts}</select>
    </div>
    <div class="modal-fld"><label>Título</label><input id="eTit" placeholder="Ex.: Consulta cardiologista"/></div>
    <div style="display:grid;grid-template-columns:1fr 1fr;gap:10px">
      <div class="modal-fld"><label>Data</label><input id="eData" type="date" value="${dataPre||new Date().toISOString().slice(0,10)}"/></div>
      <div class="modal-fld"><label>Hora (opcional)</label><input id="eHora" type="time"/></div>
    </div>
    <div class="modal-fld"><label>Descrição</label><textarea id="eDesc" rows="4"></textarea></div>
    <div id="eDicaRec" style="display:none;font-size:12px;color:var(--text-mute);margin-bottom:10px;padding:8px 10px;background:rgba(236,72,153,.12);border-radius:8px">🔁 Aniversários repetem automaticamente todo ano.</div>
    <div style="display:flex;gap:10px;justify-content:flex-end">
      <button class="btn-secondary" onclick="closeModal()">Cancelar</button>
      <button id="eSave" class="btn-primary">SALVAR</button>
    </div>
  `,()=>{
    const sel=document.getElementById("eTipo");
    const dica=document.getElementById("eDicaRec");
    sel.onchange=()=>{dica.style.display=sel.value==="aniversario"?"block":"none";};
    document.getElementById("eSave").onclick=async()=>{
      const ev={id:Date.now(),tipo:sel.value,titulo:document.getElementById("eTit").value.trim(),data:document.getElementById("eData").value,hora:document.getElementById("eHora").value,descricao:document.getElementById("eDesc").value.trim(),autor:CURRENT_USER&&CURRENT_USER.nome||""};
      if(!ev.titulo||!ev.data){showToast("Título e data são obrigatórios");return;}
      const r=await apiFetch(endpoint);
      const d=await r.json();
      const novos=(d.eventos||[]).concat([ev]);
      await apiFetch(endpoint,{method:"POST",body:JSON.stringify({eventos:novos})});
      closeModal();showToast(pessoal?"🔒 Evento pessoal criado":"✅ Post enviado ao mural");await carregarEventosCache();render();
      const efetivo=tipoEfetivoEv(ev.tipo);
      if(Array.isArray(S.evFilter)&&S.evFilter.length&&!S.evFilter.includes(efetivo)){
        promptAjustarFiltroEv(efetivo);
      }
    };
  });
}
function promptAjustarFiltroEv(tipo){
  const info=evTipoInfo(tipo);
  const ativos=(S.evFilter||[]).map(t=>{const i=evTipoInfo(t);return `${i.emoji} ${i.label}`;}).join(", ");
  openModal("Filtro está escondendo o novo evento",`
    <div style="font-size:14px;line-height:1.5;margin-bottom:14px">
      Seu evento <b>${info.emoji} ${escapeHtml(info.label)}</b> foi salvo, mas o filtro do calendário está mostrando só: <b>${escapeHtml(ativos)}</b>.
      <br><br>Por isso ele não vai aparecer no calendário enquanto o filtro estiver assim. O que você quer fazer?
    </div>
    <div style="display:flex;flex-direction:column;gap:8px">
      <button id="fAdd" class="btn-primary">➕ Incluir ${escapeHtml(info.emoji+" "+info.label)} no filtro</button>
      <button id="fClr" class="btn-secondary">🧹 Limpar filtro (mostrar todos os tipos)</button>
      <button id="fKeep" class="btn-secondary">Manter filtro como está</button>
    </div>
  `,()=>{
    document.getElementById("fAdd").onclick=()=>{toggleEvFilter(tipo);closeModal();render();};
    document.getElementById("fClr").onclick=()=>{clearEvFilter();closeModal();render();};
    document.getElementById("fKeep").onclick=()=>{closeModal();};
  });
}

// ===== ACERVO (PDFs + Fatos + Memórias) =====
let ACERVO_TAB="pdfs";
async function renderAcervo(c){
  c.innerHTML=`<div class="pg-head"><div class="pg-tit">📚 ACERVO</div></div><div class="pg-body" id="acBody"></div>`;
  if(!await requireAuth()){document.getElementById("acBody").innerHTML='<div style="color:var(--muted);padding:20px;text-align:center">Faça login para ver o acervo.</div>';return;}
  const body=document.getElementById("acBody");
  const _isAdm=CURRENT_USER&&(CURRENT_USER.role==="admin"||CURRENT_USER.role==="aprovador");
  if(!_isAdm&&ACERVO_TAB==="fatos")ACERVO_TAB="pdfs";
  body.innerHTML=`<div class="tabs-mini">
    <button data-t="pdfs" class="${ACERVO_TAB==="pdfs"?"active":""}">📄 PDFs (${"…"})</button>
    ${_isAdm?`<button data-t="fatos" class="${ACERVO_TAB==="fatos"?"active":""}">🧠 Fatos da turma</button>`:""}
    <button data-t="minhas" class="${ACERVO_TAB==="minhas"?"active":""}">🔒 Minhas memórias</button>
  </div><div id="acPanel">Carregando...</div>`;
  body.querySelectorAll(".tabs-mini button").forEach(b=>b.onclick=()=>{ACERVO_TAB=b.dataset.t;renderAcervo(c);});
  if(ACERVO_TAB==="pdfs")await renderAcervoPdfs(document.getElementById("acPanel"));
  else if(ACERVO_TAB==="fatos")await renderAcervoFatos(document.getElementById("acPanel"));
  else await renderAcervoMinhas(document.getElementById("acPanel"));
}
async function renderAcervoPdfs(el){
  el.innerHTML="Carregando...";
  const r=await apiFetch("/api/biblioteca");const d=await r.json();
  el.innerHTML=`<div style="display:flex;justify-content:space-between;align-items:center;margin-bottom:12px">
    <div style="color:var(--muted);font-size:13px">${d.total} documento(s) na biblioteca</div>
    <button id="upPdf" class="btn-primary">+ ENVIAR PDF</button>
  </div><div id="docs"></div>`;
  document.getElementById("upPdf").onclick=()=>uploadDoc(false);
  const docs=document.getElementById("docs");
  if(!d.documentos.length){docs.innerHTML='<div style="color:var(--muted);padding:20px;text-align:center">Nenhum PDF enviado ainda.</div>';return;}
  const isAdmin=CURRENT_USER&&CURRENT_USER.role==="admin";
  docs.innerHTML=d.documentos.map(doc=>`<div class="lst-item">
    <div style="flex:1;min-width:0">
      <div style="font-weight:600;font-size:13px">${escapeHtml(doc.nome)}</div>
      <div style="color:var(--muted);font-size:11px;margin-top:4px">[${escapeHtml(doc.categoria||"")}] · ${doc.paginas_chunks} trechos · ${escapeHtml(doc.data_envio||"")}</div>
      ${doc.resumo?`<div style="font-size:12px;margin-top:6px;color:var(--text);opacity:.85">${escapeHtml(doc.resumo)}</div>`:""}
    </div>
    ${isAdmin?`<button class="btn-danger" data-id="${escapeHtml(doc.id)}">Excluir</button>`:""}
  </div>`).join("");
  if(isAdmin)docs.querySelectorAll("button.btn-danger").forEach(b=>{
    b.onclick=async()=>{if(!confirm("Excluir este documento? Os trechos não estarão mais disponíveis para o Viriato."))return;const r=await apiFetch("/api/biblioteca/"+encodeURIComponent(b.dataset.id),{method:"DELETE"});if(r.ok){showToast("Documento excluído");renderAcervoPdfs(el);}else{const d=await r.json().catch(()=>({}));showToast("❌ "+(d.error||"Sem permissão"));}};
  });
}
function uploadDoc(isTemp){
  const inp=document.createElement("input");inp.type="file";inp.accept=".pdf,.docx,.txt";
  inp.onchange=async()=>{
    const f=inp.files&&inp.files[0];if(!f)return;
    if(f.size>50*1024*1024){showToast("Arquivo > 50MB");return;}
    showToast("Enviando "+f.name+"...");
    const b64=await new Promise((res,rej)=>{const r=new FileReader();r.onload=()=>res(r.result.split(",")[1]);r.onerror=rej;r.readAsDataURL(f);});
    try{
      const r=await apiFetch("/api/biblioteca/upload",{method:"POST",body:JSON.stringify({nome:f.name,data:b64,mimetype:f.type,temp:isTemp})});
      const d=await r.json();
      if(r.ok){showToast("✅ "+f.name+" ("+d.chunks+" trechos)");if(S.section==="acervo")render();}
      else showToast("❌ "+(d.error||"falhou"));
    }catch(e){if(e.message!=="auth")showToast("Erro: "+e.message);}
  };
  inp.click();
}
async function renderAcervoFatos(el){
  el.innerHTML="Carregando...";
  const r=await apiFetch("/api/memoria");const d=await r.json();
  const fatos=(d.fatos||[]).slice().reverse();
  el.innerHTML=`<div style="display:flex;justify-content:space-between;align-items:center;margin-bottom:12px">
    <div style="color:var(--muted);font-size:13px">${fatos.length} fato(s) compartilhado(s) com a turma</div>
    <button id="addF" class="btn-primary">+ NOVO FATO</button>
  </div><div id="fl"></div>`;
  document.getElementById("addF").onclick=()=>{
    openModal("Novo fato da turma",`
      <div class="modal-fld"><label>Texto do fato (será visível ao Viriato e à turma)</label><textarea id="fxT" rows="5" placeholder="Ex: Linha L006 tem capacidade ~117 vagões GDT"></textarea></div>
      <div style="display:flex;gap:10px;justify-content:flex-end"><button class="btn-secondary" onclick="closeModal()">Cancelar</button><button id="fxS" class="btn-primary">SALVAR</button></div>
    `,()=>{
      document.getElementById("fxS").onclick=async()=>{
        const txt=document.getElementById("fxT").value.trim();if(!txt){showToast("Texto vazio");return;}
        await apiFetch("/api/memoria/fato",{method:"POST",body:JSON.stringify({texto:txt})});
        closeModal();showToast("✅ Fato salvo");renderAcervoFatos(el);
      };
    });
  };
  const fl=document.getElementById("fl");
  if(!fatos.length){fl.innerHTML='<div style="color:var(--muted);padding:20px;text-align:center">Nenhum fato salvo ainda.</div>';return;}
  fl.innerHTML=fatos.map(f=>`<div class="lst-item">
    <div style="flex:1;min-width:0">
      <div style="font-size:13px;line-height:1.5">${escapeHtml(f.texto||"")}</div>
      <div style="color:var(--muted);font-size:11px;margin-top:6px">por ${escapeHtml(f.autor||"—")} · ${escapeHtml(f.data||"")}</div>
    </div>
    <button class="btn-danger" data-id="${f.id}">Excluir</button>
  </div>`).join("");
  fl.querySelectorAll("button.btn-danger").forEach(b=>{
    b.onclick=async()=>{
      if(!confirm("Excluir este fato?"))return;
      const r=await apiFetch("/api/memoria/fato/"+b.dataset.id,{method:"DELETE"});
      if(r.ok){showToast("Excluído");renderAcervoFatos(el);}
      else{const d=await r.json();showToast("❌ "+(d.error||"falhou"));}
    };
  });
}
async function renderAcervoMinhas(el){
  el.innerHTML="Carregando...";
  const r=await apiFetch("/api/memoria");const d=await r.json();
  const mem=(d.pessoal||[]).slice().reverse();
  el.innerHTML=`<div style="display:flex;justify-content:space-between;align-items:center;margin-bottom:12px">
    <div style="color:var(--muted);font-size:13px">${mem.length} memória(s) pessoal(is) — só você vê</div>
    <button id="addM" class="btn-primary">+ NOVA MEMÓRIA</button>
  </div><div id="ml"></div>`;
  document.getElementById("addM").onclick=()=>{
    openModal("Nova memória pessoal",`
      <div class="modal-fld"><label>Texto (visível só pra você e o Viriato)</label><textarea id="mxT" rows="5"></textarea></div>
      <div style="display:flex;gap:10px;justify-content:flex-end"><button class="btn-secondary" onclick="closeModal()">Cancelar</button><button id="mxS" class="btn-primary">SALVAR</button></div>
    `,()=>{
      document.getElementById("mxS").onclick=async()=>{
        const txt=document.getElementById("mxT").value.trim();if(!txt){showToast("Texto vazio");return;}
        await apiFetch("/api/memoria/pessoal",{method:"POST",body:JSON.stringify({texto:txt})});
        closeModal();showToast("✅ Memória salva");renderAcervoMinhas(el);
      };
    });
  };
  const ml=document.getElementById("ml");
  if(!mem.length){ml.innerHTML='<div style="color:var(--muted);padding:20px;text-align:center">Nada salvo. Você também pode pedir ao Viriato "anota isso".</div>';return;}
  ml.innerHTML=mem.map(m=>`<div class="lst-item">
    <div style="flex:1;min-width:0">
      <div style="font-size:13px;line-height:1.5">${escapeHtml(m.texto||"")}</div>
      <div style="color:var(--muted);font-size:11px;margin-top:6px">${escapeHtml(m.data||"")}</div>
    </div>
    <button class="btn-danger" data-id="${m.id}">Excluir</button>
  </div>`).join("");
  ml.querySelectorAll("button.btn-danger").forEach(b=>{
    b.onclick=async()=>{
      if(!confirm("Excluir?"))return;
      await apiFetch("/api/memoria/pessoal/"+b.dataset.id,{method:"DELETE"});showToast("Excluído");renderAcervoMinhas(el);
    };
  });
}

// ===== SETUP MODAL =====
async function openSetup(){
  if(!await requireAuth())return;
  const u=CURRENT_USER||{};
  const isAdm=u.role==="admin"||u.role==="aprovador";
  openModal("Configurações",`
    <div style="margin-bottom:14px;padding:10px;background:var(--card-2);border:1px solid var(--border);border-radius:10px">
      <div style="font-size:13px;font-weight:600">${escapeHtml(u.nome||"")}</div>
      <div style="font-size:12px;color:var(--muted)">Matrícula ${escapeHtml(u.matricula||"")} · ${escapeHtml(u.role||"membro")}</div>
    </div>
    <div style="display:grid;gap:8px">
      <button class="btn-secondary" id="stTema">🌓 Alternar tema (claro/escuro)</button>
      <button class="btn-secondary" id="stSenha">🔑 Trocar senha</button>
      <button class="btn-secondary" id="stFun">👤 Trocar função</button>
      <a class="btn-secondary" href="/termos-de-uso.html" style="text-align:center;text-decoration:none">📄 Termos de Uso</a>
      <a class="btn-secondary" href="/politica-de-seguranca.html" style="text-align:center;text-decoration:none">🛡 Segurança e Privacidade</a>
      ${isAdm?'<button class="btn-secondary" id="stAdm">👑 Painel admin</button>':""}
      <button class="btn-danger" id="stSair" style="margin-top:6px">🚪 Sair</button>
    </div>
  `,()=>{
    document.getElementById("stTema").onclick=()=>{const cur=document.documentElement.getAttribute("data-theme")||"dark";applyTheme(cur==="dark"?"light":"dark");};
    document.getElementById("stSenha").onclick=()=>openTrocarSenha();
    document.getElementById("stFun").onclick=()=>openTrocarFuncao();
    if(isAdm)document.getElementById("stAdm").onclick=()=>openAdmin();
    document.getElementById("stSair").onclick=async()=>{
      try{await apiFetch("/api/auth/logout",{method:"POST"});}catch(e){}
      setToken("");CURRENT_USER=null;closeModal();showToast("Sessão encerrada");
    };
  });
}
function openTrocarSenha(){
  openModal("Trocar senha",`
    <div class="modal-fld"><label>Senha atual</label><input id="psA" type="password" maxlength="4" inputmode="numeric"/></div>
    <div class="modal-fld"><label>Senha nova (4 dígitos)</label><input id="psN" type="password" maxlength="4" inputmode="numeric"/></div>
    <button id="psB" class="btn-primary" style="width:100%">SALVAR</button>
    <div id="psM" style="font-size:12px;text-align:center;margin-top:10px;min-height:14px"></div>
  `,()=>{
    document.getElementById("psB").onclick=async()=>{
      const r=await apiFetch("/api/auth/trocar-senha",{method:"POST",body:JSON.stringify({atual:document.getElementById("psA").value,nova:document.getElementById("psN").value})});
      const d=await r.json();const m=document.getElementById("psM");
      if(r.ok){m.style.color="var(--neon)";m.textContent="✅ Senha alterada";setTimeout(closeModal,1200);}
      else{m.style.color="#ff8a8a";m.textContent=d.error||"Falha";}
    };
  });
}
function openTrocarFuncao(){
  openModal("Trocar função",`
    <div class="modal-fld"><label>Função atual: ${escapeHtml((CURRENT_USER&&CURRENT_USER.funcao)||"—")}</label><select id="fnN"><option value="">— selecione —</option><option value="Função Operacional">Função Operacional</option><option value="Função Administrativa">Função Administrativa</option></select></div>
    <button id="fnB" class="btn-primary" style="width:100%">SALVAR</button>
    <div id="fnM" style="font-size:12px;text-align:center;margin-top:10px;min-height:14px"></div>
  `,()=>{
    document.getElementById("fnB").onclick=async()=>{
      const r=await apiFetch("/api/auth/funcao",{method:"POST",body:JSON.stringify({funcao:document.getElementById("fnN").value.trim()})});
      const d=await r.json();const m=document.getElementById("fnM");
      if(r.ok){m.style.color="var(--neon)";m.textContent="✅ Atualizado";await loadMe();setTimeout(closeModal,1000);}
      else{m.style.color="#ff8a8a";m.textContent=d.error||"Falha";}
    };
  });
}
async function openAdmin(){
  openModal("Painel administrativo",`
    <div class="tabs-mini" id="adTabs" style="flex-wrap:wrap">
      <button data-t="pend" class="active">⏳ Cadastros</button>
      <button data-t="mem">🧠 Memorizações</button>
      <button data-t="usu">👥 Usuários</button>
      <button data-t="reg">🧪 Regras técnicas</button>
      <button data-t="ant">🚫 Anti-padrões</button>
      <button data-t="log">📋 Log Viriato</button>
      <button data-t="drive">🔄 Sync Drive</button>
    </div>
    <div id="adPanel">Carregando...</div>
  `,async(body)=>{
    let tab="pend";
    const load=async()=>{
      const p=document.getElementById("adPanel");p.innerHTML="Carregando...";
      if(tab==="pend"){
        const r=await apiFetch("/api/admin/pendentes");const d=await r.json();
        const list=d.pendentes||d||[];
        if(!list.length){p.innerHTML='<div style="color:var(--muted);padding:14px;text-align:center">Nenhum cadastro pendente</div>';return;}
        p.innerHTML=list.map(u=>`<div class="lst-item"><div style="flex:1"><div style="font-weight:600">${escapeHtml(u.nome||"")}</div><div style="font-size:12px;color:var(--muted)">Mat ${escapeHtml(u.matricula||"")} · ${escapeHtml(u.funcao||"—")}</div></div><div style="display:flex;gap:6px"><button class="btn-primary" data-act="ap" data-m="${escapeHtml(u.matricula)}" style="padding:6px 10px">Aprovar</button><button class="btn-danger" data-act="ng" data-m="${escapeHtml(u.matricula)}">Negar</button></div></div>`).join("");
        p.querySelectorAll("button[data-act]").forEach(b=>{
          b.onclick=async()=>{
            const ep=b.dataset.act==="ap"?"aprovar":"negar";
            const r=await apiFetch("/api/admin/"+ep+"/"+encodeURIComponent(b.dataset.m),{method:"POST"});
            if(r.ok){showToast(b.dataset.act==="ap"?"✅ Aprovado":"Negado");load();}
          };
        });
      }else if(tab==="mem"){
        const r=await apiFetch("/api/admin/memoria/pendentes");const d=await r.json();
        const list=d.pendentes||[];
        if(!list.length){p.innerHTML='<div style="color:var(--muted);padding:14px;text-align:center">Nenhuma memorização pendente</div>';return;}
        p.innerHTML='<div style="font-size:11px;color:var(--muted);margin-bottom:8px;padding:0 4px">Sugestões enviadas pelo Viriato a partir das conversas dos colegas. Aprove para gravar no MemPalace.</div>'+list.map(m=>{
          const isPess=m.tipo==='pessoal';
          const cor=isPess?'#7c3aed':'#0ea5e9';
          const tag=isPess?'PESSOAL':'FATO DA TURMA';
          return `<div class="lst-item" style="flex-direction:column;align-items:stretch;gap:8px">
            <div style="display:flex;align-items:center;gap:8px;flex-wrap:wrap">
              <span style="background:${cor};color:#fff;padding:2px 8px;border-radius:6px;font-size:10px;font-weight:700">${tag}</span>
              <span style="font-size:11px;color:var(--muted)">${escapeHtml(m.autor||"")} · Mat ${escapeHtml(m.matricula||"")} · ${escapeHtml(m.data||"")}</span>
            </div>
            <div style="font-size:13px;line-height:1.4">${escapeHtml(m.texto||"")}</div>
            <div style="display:flex;gap:6px;justify-content:flex-end">
              <button class="btn-primary" data-act="ap" data-i="${m.id}" style="padding:6px 12px">✅ Aprovar</button>
              <button class="btn-danger" data-act="ng" data-i="${m.id}" style="padding:6px 12px">✖ Negar</button>
            </div>
          </div>`;
        }).join("");
        p.querySelectorAll("button[data-act]").forEach(b=>{
          b.onclick=async()=>{
            const ep=b.dataset.act==="ap"?"aprovar":"negar";
            const r=await apiFetch("/api/admin/memoria/pendentes/"+b.dataset.i+"/"+ep,{method:"POST"});
            if(r.ok){showToast(b.dataset.act==="ap"?"✅ Memorizado":"Sugestão descartada");load();}
            else{const d=await r.json().catch(()=>({}));showToast("❌ "+(d.error||d.erro||"falhou"));}
          };
        });
      }else if(tab==="usu"){
        const r=await apiFetch("/api/admin/usuarios");const d=await r.json();
        const list=d.usuarios||d||[];
        const myLvl=(CURRENT_USER&&CURRENT_USER.admin_level)||0;
        const myMat=CURRENT_USER&&CURRENT_USER.matricula;
        const canManage=(u)=>{ if(u.owner)return myLvl>=3; if((u.admin_level||0)>=1)return myLvl>=2; return myLvl>=1; };
        const B=(act,m,txt,extra,cls)=>'<button class="'+(cls||'btn-secondary')+'" data-act="'+act+'" data-m="'+escapeHtml(m)+'"'+(extra||'')+' style="padding:4px 8px;font-size:11px">'+txt+'</button>';
        p.innerHTML=list.map(u=>{
          const lvl=u.admin_level||0;
          const cargo=u.owner?'<span style="color:var(--neon);font-weight:700">desenvolvedor 🛠️</span>':(lvl>=1?('admin <b>N'+lvl+'</b>'):escapeHtml(u.role||"membro"));
          const badge=u.status==="negado"?' · <span style="color:#ff6b6b;font-weight:700">BANIDO</span>':u.status==="pendente"?' · <span style="color:var(--orange,#f5a623)">pendente</span>':'';
          const isSelf=u.matricula===myMat;
          let acts='';
          if(u.status==="negado"){
            if(canManage(u))acts+=B('ap',u.matricula,'♻ Reativar');
          }else if(!u.owner){
            if(lvl===0){
              if(myLvl>=2)acts+=B('pr',u.matricula,'↑ Admin N1',' data-nivel="1"')+B('pr',u.matricula,'↑ Admin N2',' data-nivel="2"');
            }else if(myLvl>=2){
              acts+=B('pr',u.matricula,lvl===2?'↓ p/ N1':'↑ p/ N2',' data-nivel="'+(lvl===2?'1':'2')+'"');
              acts+=B('dp',u.matricula,'✕ Tirar admin');
            }
          }
          if(canManage(u)||isSelf)acts+=B('rs',u.matricula,'🔑 Resetar');
          if(!u.owner&&!isSelf&&u.status!=="negado"&&canManage(u))acts+=B('bn',u.matricula,'🚫 Banir',null,'btn-danger');
          return '<div class="lst-item"><div style="flex:1"><div style="font-weight:600">'+escapeHtml(u.nome||"")+'</div><div style="font-size:12px;color:var(--muted)">Mat '+escapeHtml(u.matricula||"")+' · '+cargo+badge+'</div></div><div style="display:flex;gap:4px;flex-wrap:wrap">'+acts+'</div></div>';
        }).join("");
        p.querySelectorAll("button[data-act]").forEach(b=>{
          b.onclick=async()=>{
            const ep={pr:"promover",dp:"despromover",rs:"reset-senha",bn:"banir",ap:"aprovar"}[b.dataset.act];
            if(b.dataset.act==="bn"&&!confirm("Banir este usuário? O acesso é revogado na hora (sessões derrubadas). Dá pra reativar depois."))return;
            const opts={method:"POST"};
            if(b.dataset.act==="pr")opts.body=JSON.stringify({nivel:b.dataset.nivel||"1"});
            const r=await apiFetch("/api/admin/"+ep+"/"+encodeURIComponent(b.dataset.m),opts);
            const d=await r.json();
            if(r.ok)showToast(d.mensagem||"✅ Feito");
            else showToast("❌ "+(d.error||"falhou"));
            load();
          };
        });
      }else if(tab==="reg"){
        const r=await apiFetch("/api/regras_tecnicas");const d=await r.json();
        const regras=d.regras||[];
        const form=`<div style="background:var(--card-2);border:1px solid var(--border);border-radius:10px;padding:10px;margin-bottom:10px">
          <div style="font-size:12px;font-weight:600;margin-bottom:8px;color:var(--neon)">+ Nova regra técnica</div>
          <div class="modal-fld" style="margin-bottom:6px"><input id="rgC" placeholder="Conceito (ex: Pressão de alívio L201)" maxlength="120"/></div>
          <div class="modal-fld" style="margin-bottom:6px"><textarea id="rgR" placeholder="Regra de ouro (operacional, completa)" maxlength="600" rows="3" style="width:100%;background:var(--bg);border:1px solid var(--border);border-radius:8px;padding:8px;color:var(--text);font-family:inherit;font-size:13px"></textarea></div>
          <div class="modal-fld" style="margin-bottom:6px"><input id="rgB" placeholder="Condição de borda (opcional)" maxlength="400"/></div>
          <div style="display:flex;gap:6px;margin-bottom:6px">
            <input id="rgP" placeholder="Peso 0.0–1.0" value="0.9" style="flex:1;background:var(--bg);border:1px solid var(--border);border-radius:8px;padding:8px;color:var(--text)"/>
            <input id="rgF" placeholder="Fonte (doc/pessoa)" maxlength="120" style="flex:2;background:var(--bg);border:1px solid var(--border);border-radius:8px;padding:8px;color:var(--text)"/>
          </div>
          <button id="rgB1" class="btn-primary" style="width:100%;padding:8px">Gravar regra</button>
        </div>`;
        const lista=regras.length?regras.map(r=>`<div class="lst-item" style="flex-direction:column;align-items:stretch;gap:6px">
          <div style="display:flex;align-items:center;gap:8px;flex-wrap:wrap">
            <span style="background:#14b8a6;color:#fff;padding:2px 8px;border-radius:6px;font-size:10px;font-weight:700">REGRA</span>
            <span style="font-weight:600;font-size:13px;flex:1">${escapeHtml(r.conceito||"")}</span>
            <span style="font-size:10px;color:var(--muted)">peso ${r.peso_de_confianca||1}</span>
            <button class="btn-danger" data-id="${r.id}" data-act="del" style="padding:4px 10px;font-size:11px">🗑</button>
          </div>
          <div style="font-size:13px;line-height:1.4">${escapeHtml(r.regra_de_ouro||"")}</div>
          ${r.condicao_de_borda?`<div style="font-size:11px;color:var(--muted)"><b>Borda:</b> ${escapeHtml(r.condicao_de_borda)}</div>`:""}
          <div style="font-size:10px;color:var(--muted)">Fonte: ${escapeHtml(r.fonte||"?")} · ${escapeHtml(r.data||"")}</div>
        </div>`).join(""):'<div style="color:var(--muted);padding:14px;text-align:center;font-size:12px">Nenhuma regra cadastrada ainda</div>';
        p.innerHTML=form+lista;
        document.getElementById("rgB1").onclick=async()=>{
          const body={
            conceito:document.getElementById("rgC").value.trim(),
            regra_de_ouro:document.getElementById("rgR").value.trim(),
            condicao_de_borda:document.getElementById("rgB").value.trim(),
            peso_de_confianca:parseFloat(document.getElementById("rgP").value)||0.9,
            fonte:document.getElementById("rgF").value.trim()
          };
          const r=await apiFetch("/api/regras_tecnicas",{method:"POST",body:JSON.stringify(body)});
          const d=await r.json();
          if(r.ok){showToast("✅ Regra gravada");load();}else{showToast("❌ "+(d.error||"falha"));}
        };
        p.querySelectorAll("button[data-act='del']").forEach(b=>{
          b.onclick=async()=>{
            if(!confirm("Apagar esta regra?"))return;
            const r=await apiFetch("/api/regras_tecnicas/"+b.dataset.id,{method:"DELETE"});
            if(r.ok){showToast("Apagada");load();}
          };
        });
      }else if(tab==="ant"){
        const r=await apiFetch("/api/antipadroes");const d=await r.json();
        const lst=d.antipadroes||[];
        const form=`<div style="background:var(--card-2);border:1px solid var(--border);border-radius:10px;padding:10px;margin-bottom:10px">
          <div style="font-size:12px;font-weight:600;margin-bottom:8px;color:#ff8a8a">+ Novo anti-padrão (erro a NUNCA repetir)</div>
          <div class="modal-fld" style="margin-bottom:6px"><textarea id="apE" placeholder="Erro que o Viriato cometeu" maxlength="400" rows="2" style="width:100%;background:var(--bg);border:1px solid var(--border);border-radius:8px;padding:8px;color:var(--text);font-family:inherit;font-size:13px"></textarea></div>
          <div class="modal-fld" style="margin-bottom:6px"><textarea id="apC" placeholder="Correção (o que ele deveria ter dito)" maxlength="400" rows="2" style="width:100%;background:var(--bg);border:1px solid var(--border);border-radius:8px;padding:8px;color:var(--text);font-family:inherit;font-size:13px"></textarea></div>
          <button id="apB1" class="btn-primary" style="width:100%;padding:8px">Gravar anti-padrão</button>
        </div>`;
        const lista=lst.length?lst.map(a=>`<div class="lst-item" style="flex-direction:column;align-items:stretch;gap:6px">
          <div style="display:flex;align-items:center;gap:8px;flex-wrap:wrap">
            <span style="background:#dc2626;color:#fff;padding:2px 8px;border-radius:6px;font-size:10px;font-weight:700">EVITAR</span>
            <span style="font-size:11px;color:var(--muted);flex:1">${escapeHtml(a.autor||"")} · ${escapeHtml(a.data||"")}</span>
            <button class="btn-danger" data-id="${a.id}" data-act="del" style="padding:4px 10px;font-size:11px">🗑</button>
          </div>
          <div style="font-size:13px;line-height:1.4"><b style="color:#ff8a8a">Erro:</b> ${escapeHtml(a.erro_a_evitar||"")}</div>
          <div style="font-size:13px;line-height:1.4"><b style="color:var(--neon)">Correção:</b> ${escapeHtml(a.correcao||"")}</div>
        </div>`).join(""):'<div style="color:var(--muted);padding:14px;text-align:center;font-size:12px">Nenhum anti-padrão cadastrado</div>';
        p.innerHTML=form+lista;
        document.getElementById("apB1").onclick=async()=>{
          const body={erro_a_evitar:document.getElementById("apE").value.trim(),correcao:document.getElementById("apC").value.trim()};
          const r=await apiFetch("/api/antipadroes",{method:"POST",body:JSON.stringify(body)});
          const d=await r.json();
          if(r.ok){showToast("✅ Anti-padrão gravado");load();}else{showToast("❌ "+(d.error||"falha"));}
        };
        p.querySelectorAll("button[data-act='del']").forEach(b=>{
          b.onclick=async()=>{
            if(!confirm("Apagar este anti-padrão?"))return;
            const r=await apiFetch("/api/antipadroes/"+b.dataset.id,{method:"DELETE"});
            if(r.ok){showToast("Apagado");load();}
          };
        });
      }else if(tab==="log"){
        const r=await apiFetch("/api/admin/log_decisoes");const d=await r.json();
        const lst=d.entradas||[];
        if(!lst.length){p.innerHTML='<div style="color:var(--muted);padding:14px;text-align:center;font-size:12px">Sem decisões deliberativas registradas</div>';return;}
        p.innerHTML='<div style="font-size:11px;color:var(--muted);margin-bottom:8px;padding:0 4px">Cada vez que o Viriato entra em modo deliberativo (pergunta crítica), uma entrada é gravada aqui.</div>'+lst.map(e=>{
          const cor=e.modo==="deliberativo"?"#14b8a6":"#f59e0b";
          const tag=e.modo==="deliberativo"?"AUDITADO":"SEM REGRA";
          return `<div class="lst-item" style="flex-direction:column;align-items:stretch;gap:6px">
            <div style="display:flex;align-items:center;gap:8px;flex-wrap:wrap">
              <span style="background:${cor};color:#fff;padding:2px 8px;border-radius:6px;font-size:10px;font-weight:700">${tag}</span>
              <span style="font-size:11px;color:var(--muted)">${escapeHtml(e.autor||e.matricula||"")} · ${escapeHtml(e.data||"")}</span>
            </div>
            <div style="font-size:13px;line-height:1.4">${escapeHtml(e.pergunta||"")}</div>
            ${(e.regras_usadas||[]).length?`<div style="font-size:11px;color:var(--muted)"><b>Regras consultadas:</b> ${e.regras_usadas.map(r=>escapeHtml(r.conceito||"?")).join(" · ")}</div>`:'<div style="font-size:11px;color:#f59e0b">⚠ Pergunta crítica sem regra técnica cadastrada</div>'}
          </div>`;
        }).join("");
      }else if(tab==="drive"){
        p.innerHTML=`<div style="text-align:center;padding:20px">
          <div style="font-size:13px;color:var(--muted);margin-bottom:16px">Sincroniza PDFs da pasta Google Drive (Viriato-Acervo) com a biblioteca do Viriato.</div>
          <button id="btnDriveSync" class="btn-primary" style="padding:10px 24px;font-size:14px">🔄 Sincronizar Drive</button>
          <div id="driveSyncStatus" style="margin-top:12px;font-size:12px;color:var(--muted)"></div>
        </div>`;
        document.getElementById("btnDriveSync").onclick=async()=>{
          const btn=document.getElementById("btnDriveSync");
          const st=document.getElementById("driveSyncStatus");
          btn.disabled=true;btn.textContent="⏳ Sincronizando...";
          st.textContent="Pode levar alguns minutos. Não feche esta tela.";
          try{
            const r=await apiFetch("/api/admin/drive-sync",{method:"POST"});
            const d=await r.json();
            if(d.ok){
              st.innerHTML='<span style="color:var(--neon)">✅ Sync iniciado em background.</span><br>Acompanhe o status abaixo.';
              const poll=setInterval(async()=>{
                const sr=await apiFetch("/api/admin/drive-sync/status");
                const sd=await sr.json();
                if(!sd.running){clearInterval(poll);btn.disabled=false;btn.textContent="🔄 Sincronizar Drive";st.innerHTML='<span style="color:var(--neon)">✅ Sync concluído!</span>';}
              },5000);
            }else{st.innerHTML='<span style="color:#ef4444">❌ '+(d.error||d.erro||"Erro")+'</span>';btn.disabled=false;btn.textContent="🔄 Sincronizar Drive";}
          }catch(e){st.innerHTML='<span style="color:#ef4444">❌ Falha: '+e.message+'</span>';btn.disabled=false;btn.textContent="🔄 Sincronizar Drive";}
        };
      }
    };
    body.querySelectorAll("#adTabs button").forEach(b=>{
      b.onclick=()=>{tab=b.dataset.t;body.querySelectorAll("#adTabs button").forEach(x=>x.classList.toggle("active",x===b));load();};
    });
    load();
  });
}

// ===== SIDEBAR ROUTER =====
function setSection(sec){
  S.section=sec;
  document.querySelectorAll(".mp-item[data-sec]").forEach(b=>b.classList.toggle("active",b.dataset.sec===sec));
  ["sec-calendario","sec-eventos","sec-dss","sec-pessoais","sec-diario","sec-chat","sec-acervo","sec-viriato","sec-setup"].forEach(c=>document.body.classList.remove(c));
  document.body.classList.add("sec-"+sec);
  render();
}
S.section=S.section||"calendario";
["sec-calendario","sec-eventos","sec-dss","sec-pessoais","sec-diario","sec-chat","sec-acervo","sec-viriato","sec-setup"].forEach(c=>document.body.classList.remove(c));
document.body.classList.add("sec-"+S.section);
// Menu ⋮ wiring
(function(){
  const fab=document.getElementById("menuFab");
  const pop=document.getElementById("menuPop");
  const bd=document.getElementById("menuBackdrop");
  const closeMenu=()=>{pop.classList.remove("open");bd.classList.remove("open");fab.classList.remove("active");};
  const openMenu=()=>{pop.classList.add("open");bd.classList.add("open");fab.classList.add("active");};
  fab.addEventListener("click",(e)=>{e.stopPropagation();pop.classList.contains("open")?closeMenu():openMenu();});
  bd.addEventListener("click",closeMenu);
  document.addEventListener("keydown",(e)=>{if(e.key==="Escape")closeMenu();});
  document.querySelectorAll(".menu-pop .mp-item[data-sec]").forEach(b=>{
    b.addEventListener("click",async()=>{
      const sec=b.dataset.sec;
      closeMenu();
      if(sec==="setup"){await openSetup();return;}
      if(sec!=="calendario"){if(!await requireAuth())return;}
      setSection(sec);
    });
  });
  document.querySelectorAll(".menu-pop a.mp-item").forEach(a=>{
    a.addEventListener("click",closeMenu);
  });
})();

// ===== VIRIATO + popover (anexa após cada renderViriato) =====
const _origRenderViriato=renderViriato;
window.renderViriato=function(){
  _origRenderViriato();
  if(window._viriatoPlusOutside){document.removeEventListener("click",window._viriatoPlusOutside,true);window._viriatoPlusOutside=null;}
  if(!S.viriatoOpen)return;
  const plus=document.getElementById("vwPlus");
  const pop=document.getElementById("vwPlusPop");
  if(!plus||!pop)return;
  plus.onclick=(e)=>{e.stopPropagation();pop.style.display=pop.style.display==="block"?"none":"block";};
  window._viriatoPlusOutside=(e)=>{if(pop && pop.style.display==="block" && !pop.contains(e.target) && e.target!==plus)pop.style.display="none";};
  document.addEventListener("click",window._viriatoPlusOutside,true);
  pop.querySelectorAll("button").forEach(b=>{
    b.onclick=async()=>{
      pop.style.display="none";
      const act=b.dataset.act;
      if(act==="doc")uploadDoc(false);
      else if(act==="temp")uploadDoc(true);
      else if(act==="img"||act==="cam"){
        const inp=document.createElement("input");inp.type="file";inp.accept="image/*";if(act==="cam")inp.capture="environment";
        inp.onchange=async()=>{const f=inp.files&&inp.files[0];if(!f)return;
          if(f.size>50*1024*1024){showToast("Imagem > 50MB");return;}
          showToast("Enviando imagem...");
          const b64=await new Promise((res,rej)=>{const r=new FileReader();r.onload=()=>res(r.result.split(",")[1]);r.onerror=rej;r.readAsDataURL(f);});
          try{
            const r=await apiFetch("/api/biblioteca/upload",{method:"POST",body:JSON.stringify({nome:f.name||"camera.jpg",data:b64,mimetype:f.type||"image/jpeg",temp:true})});
            const d=await r.json();
            if(r.ok)showToast("✅ Imagem enviada ("+d.chunks+" trechos)");
            else showToast("❌ "+(d.error||"falhou"));
          }catch(e){if(e.message!=="auth")showToast("Erro: "+e.message);}
        };
        inp.click();
      }else if(act==="clear"){
        if(confirm("Limpar conversa atual?")){S.history=[];renderViriato();}
      }
    };
  });
};

// ===== WEB PUSH (notificacoes do celular + buzina) =====
let SW_REG=null;
let PUSH_VAPID=null;
function urlBase64ToUint8Array(b64){
  const pad="=".repeat((4-b64.length%4)%4);
  const base=(b64+pad).replace(/-/g,"+").replace(/_/g,"/");
  const raw=atob(base);
  const arr=new Uint8Array(raw.length);
  for(let i=0;i<raw.length;i++)arr[i]=raw.charCodeAt(i);
  return arr;
}
async function registerSW(){
  if(!("serviceWorker" in navigator))return null;
  try{
    SW_REG=await navigator.serviceWorker.register("/sw.js",{scope:"/"});
    return SW_REG;
  }catch(e){console.warn("SW register falhou:",e);return null;}
}
async function getVapidKey(){
  if(PUSH_VAPID)return PUSH_VAPID;
  try{
    const r=await fetch("/api/push/vapid-public-key");
    const d=await r.json();
    if(d.enabled && d.publicKey){PUSH_VAPID=d.publicKey;return PUSH_VAPID;}
  }catch(_){}
  return null;
}
async function pushIsSubscribed(){
  if(!SW_REG)return false;
  try{const s=await SW_REG.pushManager.getSubscription();return !!s;}catch(_){return false;}
}
async function enablePushNotifications(){
  if(!("serviceWorker" in navigator) || !("PushManager" in window) || !("Notification" in window)){
    showToast("❌ Seu navegador nao suporta notificacoes push");return false;
  }
  if(!CURRENT_USER){showToast("Faca login primeiro");return false;}
  if(!SW_REG){await registerSW();}
  if(!SW_REG){showToast("❌ Service Worker nao registrado");return false;}
  const key=await getVapidKey();
  if(!key){showToast("❌ Servidor sem chave VAPID");return false;}
  let perm=Notification.permission;
  if(perm==="default"){perm=await Notification.requestPermission();}
  if(perm!=="granted"){showToast("❌ Permissao negada nas configuracoes do navegador");return false;}
  try{
    let sub=await SW_REG.pushManager.getSubscription();
    if(!sub){
      sub=await SW_REG.pushManager.subscribe({userVisibleOnly:true,applicationServerKey:urlBase64ToUint8Array(key)});
    }
    const r=await apiFetch("/api/push/subscribe",{method:"POST",body:JSON.stringify({subscription:sub.toJSON()})});
    if(r.ok){
      showToast("✅ Notificacoes ativadas! Tocando buzina de teste...");
      tocarBuzina();
      // dispara push de teste do servidor
      setTimeout(()=>{apiFetch("/api/push/test",{method:"POST",body:"{}"});},1200);
      atualizarBotaoNotif();
      return true;
    }
    showToast("❌ Falha ao registrar no servidor");return false;
  }catch(e){console.warn(e);showToast("❌ Erro: "+e.message);return false;}
}
async function disablePushNotifications(){
  if(!SW_REG)return;
  try{
    const sub=await SW_REG.pushManager.getSubscription();
    if(sub){
      await apiFetch("/api/push/unsubscribe",{method:"POST",body:JSON.stringify({endpoint:sub.endpoint})});
      await sub.unsubscribe();
    }
    showToast("Notificacoes desativadas");atualizarBotaoNotif();
  }catch(e){showToast("Erro: "+e.message);}
}
async function atualizarBotaoNotif(){
  const lbl=document.getElementById("mpNotifLbl");
  if(!lbl)return;
  if(!("Notification" in window)){lbl.textContent="🔕 Sem suporte";return;}
  const subed=await pushIsSubscribed();
  if(Notification.permission==="granted" && subed){lbl.textContent="🔔 Notificacoes ativas — desativar";}
  else if(Notification.permission==="denied"){lbl.textContent="🔕 Bloqueadas (libere no navegador)";}
  else{lbl.textContent="🔔 Ativar notificacoes";}
}

// audio buzina (cache)
let _BUZINA=null;
function tocarBuzina(){
  try{
    if(!_BUZINA){_BUZINA=new Audio("/buzina_trem.mp3");_BUZINA.volume=0.85;}
    _BUZINA.currentTime=0;
    const p=_BUZINA.play();
    if(p&&p.catch)p.catch(()=>{/* navegador pode bloquear sem gesto */});
  }catch(_){}
}

// receber mensagens do service worker (push em foreground / clique em notificacao)
if("serviceWorker" in navigator){
  navigator.serviceWorker.addEventListener("message",(ev)=>{
    const m=ev.data||{};
    if(m.type==="push"){
      tocarBuzina();
      const p=m.payload||{};
      if(p.title||p.body){showToast((p.title||"")+(p.body?" — "+p.body:""));}
      // recarrega caches relevantes
      if(p.kind==="mural"){carregarEventosCache().then(()=>{if(S.section==="eventos"||S.section==="calendario")render();});}
    } else if(m.type==="notification_click"){
      tocarBuzina();
      if(m.url && m.url.includes("chat")){S.section="chat";saveLS();render();}
      else if(m.url && m.url.includes("eventos")){S.section="eventos";saveLS();render();}
    }
  });
}

// ===== Leitor de Manual (PDF in-app com botao Sair) =====
function abrirManualPDF(){
  let v=document.getElementById("manualViewer");
  if(v){v.remove();}
  v=document.createElement("div");
  v.id="manualViewer";
  v.style.cssText="position:fixed;inset:0;z-index:9999;background:var(--bg);display:flex;flex-direction:column";
  v.innerHTML=`
    <div style="display:flex;align-items:center;gap:12px;padding:12px 16px;background:var(--card);border-bottom:1px solid var(--border);box-shadow:0 4px 12px #0008">
      <button id="mvSair" style="background:var(--neon);color:#000;border:0;border-radius:8px;padding:10px 16px;font-weight:700;font-size:14px;cursor:pointer;display:flex;align-items:center;gap:6px">
        <span style="font-size:18px">←</span> Sair do manual
      </button>
      <div style="flex:1;color:var(--text);font-weight:600;font-size:14px;text-align:center">📖 Manual do App</div>
      <a href="/manual_agenda_turma_a.pdf" download style="background:var(--card-2);color:var(--text);border:1px solid var(--border);border-radius:8px;padding:10px 14px;font-size:13px;text-decoration:none">⬇️ Baixar</a>
    </div>
    <iframe src="/manual_agenda_turma_a.pdf" style="flex:1;width:100%;border:0;background:#fff" title="Manual"></iframe>`;
  document.body.appendChild(v);
  const sair=()=>{const x=document.getElementById("manualViewer");if(x)x.remove();document.removeEventListener("keydown",onEsc);};
  const onEsc=(e)=>{if(e.key==="Escape")sair();};
  document.getElementById("mvSair").onclick=sair;
  document.addEventListener("keydown",onEsc);
}

// ===== Boot =====
loadMe().then(async()=>{
  // loadMe resolve assincrono e seta CURRENT_USER; o render() de baixo roda antes
  // disso (com user ainda null). Re-renderiza agora que o usuario eh conhecido,
  // senao a home (banner DSS, eventos) fica presa no estado pre-login ate navegar.
  if(CURRENT_USER)render();
  await registerSW();
  atualizarBotaoNotif();
  // hook do botao do menu
  const btn=document.getElementById("mpNotif");
  if(btn){
    btn.onclick=async(e)=>{
      e.preventDefault();
      const subed=await pushIsSubscribed();
      if(subed && Notification.permission==="granted"){await disablePushNotifications();}
      else{await enablePushNotifications();}
    };
  }
  const bman=document.getElementById("mpManual");
  if(bman){bman.onclick=(e)=>{e.preventDefault();abrirManualPDF();};}
});

render();
