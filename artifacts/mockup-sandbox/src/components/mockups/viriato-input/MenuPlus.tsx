import { useState, useRef, useEffect } from "react";
import { Plus, Send, Paperclip, Pin, Image as ImageIcon, Camera, X } from "lucide-react";

const C = {
  bg: "#07090f",
  card: "#0f1628",
  card2: "#0c1020",
  text: "#e8edf5",
  text3: "#b8c4d8",
  muted: "#4a6080",
  border: "#1e2d44",
  green: "#4ade80",
  blue: "#0ea5e9",
  amber: "#f59e0b",
};

function ChatPreview() {
  return (
    <div style={{ flex: 1, overflowY: "auto", padding: "12px 14px", display: "flex", flexDirection: "column", gap: 10 }}>
      <div style={{ alignSelf: "flex-start", maxWidth: "82%", background: C.card2, border: `1px solid ${C.border}`, color: C.text3, padding: "8px 11px", borderRadius: 12, fontSize: 13, lineHeight: 1.5 }}>
        Bom dia, Angelo! Hoje você está de <b style={{ color: C.green }}>folga</b>. Próximo serviço: 24/04 (sex). 🚂
      </div>
      <div style={{ alignSelf: "flex-end", maxWidth: "82%", background: "#0ea5e922", border: `1px solid #0ea5e966`, color: C.text, padding: "8px 11px", borderRadius: 12, fontSize: 13 }}>
        Tem o layout do pátio TFPM aí?
      </div>
      <div style={{ alignSelf: "flex-start", maxWidth: "82%", background: C.card2, border: `1px solid ${C.border}`, color: C.text3, padding: "8px 11px", borderRadius: 12, fontSize: 13, lineHeight: 1.5 }}>
        Tenho sim — <b>Layout dos Pátios TFPM.pdf</b> está na biblioteca. Quer que eu te resuma?
      </div>
    </div>
  );
}

export function MenuPlus() {
  const [open, setOpen] = useState(false);
  const [tempMode, setTempMode] = useState(false);
  const [text, setText] = useState("");
  const ref = useRef<HTMLDivElement>(null);

  useEffect(() => {
    const onDoc = (e: MouseEvent) => {
      if (ref.current && !ref.current.contains(e.target as Node)) setOpen(false);
    };
    document.addEventListener("mousedown", onDoc);
    return () => document.removeEventListener("mousedown", onDoc);
  }, []);

  const action = (label: string) => {
    setOpen(false);
    console.log("action:", label);
  };

  const items = [
    { icon: Paperclip, label: "Documento", color: C.text3, onClick: () => action("doc") },
    { icon: Pin, label: tempMode ? "TEMP ligado" : "Marcar TEMP", color: tempMode ? C.amber : C.text3, onClick: () => { setTempMode(v => !v); setOpen(false); } },
    { icon: ImageIcon, label: "Imagem", color: C.text3, onClick: () => action("img") },
    { icon: Camera, label: "Câmera", color: C.text3, onClick: () => action("cam") },
  ];

  return (
    <div style={{ height: "100vh", background: C.bg, color: C.text, display: "flex", flexDirection: "column", fontFamily: "system-ui, -apple-system, sans-serif" }}>
      <div style={{ display: "flex", alignItems: "center", gap: 8, padding: "10px 12px", borderBottom: `1px solid ${C.border}`, background: "#0d1120" }}>
        <div style={{ width: 30, height: 30, borderRadius: 8, background: "#1e293b", border: `1.5px solid ${C.green}`, display: "flex", alignItems: "center", justifyContent: "center", fontSize: 16 }}>🤖</div>
        <div style={{ flex: 1 }}>
          <div style={{ fontSize: 14, fontWeight: 700, color: C.green }}>Viriato</div>
          <div style={{ fontSize: 10, color: C.green, background: "#4ade8018", border: "1px solid #4ade8033", padding: "1px 7px", borderRadius: 7, display: "inline-block" }}>Claude Haiku</div>
        </div>
      </div>

      <ChatPreview />

      {tempMode && (
        <div style={{ padding: "6px 12px", background: "#f59e0b14", borderTop: `1px solid #f59e0b33`, fontSize: 11, color: C.amber, display: "flex", alignItems: "center", gap: 6 }}>
          <Pin size={12} /> Próximo anexo vai para a pasta TEMP
        </div>
      )}

      <div ref={ref} style={{ position: "relative", padding: "10px 12px", borderTop: `1px solid ${C.border}`, background: C.card }}>
        {open && (
          <div style={{ position: "absolute", bottom: "calc(100% + 6px)", left: 12, background: C.card2, border: `1px solid ${C.border}`, borderRadius: 12, padding: 6, minWidth: 190, boxShadow: "0 8px 24px rgba(0,0,0,0.5)", zIndex: 10 }}>
            {items.map((it, i) => {
              const Ico = it.icon;
              return (
                <button key={i} onClick={it.onClick} style={{ display: "flex", alignItems: "center", gap: 10, width: "100%", padding: "9px 10px", background: "transparent", border: "none", color: it.color, fontSize: 13, cursor: "pointer", borderRadius: 8, textAlign: "left" }}
                  onMouseEnter={e => (e.currentTarget.style.background = "#1e2d4455")}
                  onMouseLeave={e => (e.currentTarget.style.background = "transparent")}
                >
                  <Ico size={16} /> {it.label}
                </button>
              );
            })}
          </div>
        )}

        <div style={{ display: "flex", alignItems: "center", gap: 8 }}>
          <button onClick={() => setOpen(v => !v)}
            style={{ width: 36, height: 36, borderRadius: 10, background: open ? C.green : C.card2, border: `1px solid ${open ? C.green : C.border}`, color: open ? "#000" : C.text3, display: "flex", alignItems: "center", justifyContent: "center", cursor: "pointer", flexShrink: 0, transition: "transform 0.15s", transform: open ? "rotate(45deg)" : "none" }}
            title="Anexar / Ações">
            <Plus size={20} strokeWidth={2.5} />
          </button>

          <input
            value={text}
            onChange={e => setText(e.target.value)}
            placeholder="Pergunte"
            style={{ flex: 1, height: 36, padding: "0 12px", background: C.card2, border: `1px solid ${C.border}`, borderRadius: 10, color: C.text, fontSize: 13.5, outline: "none" }}
          />

          <button style={{ width: 36, height: 36, borderRadius: 10, background: C.green, border: "none", color: "#000", fontWeight: 700, display: "flex", alignItems: "center", justifyContent: "center", cursor: "pointer", flexShrink: 0 }}>
            <Send size={16} />
          </button>
        </div>
      </div>
    </div>
  );
}
