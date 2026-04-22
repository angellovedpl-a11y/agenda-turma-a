import { useState } from "react";
import { Send, Paperclip, Pin, Image as ImageIcon, Camera, ChevronRight } from "lucide-react";

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

export function SwipeBar() {
  const [expanded, setExpanded] = useState(false);
  const [tempMode, setTempMode] = useState(false);
  const [text, setText] = useState("");

  const ico = (Icon: any, key: string, onClick: () => void, active = false) => (
    <button key={key} onClick={onClick}
      style={{ width: 36, height: 36, borderRadius: 10, background: active ? "#f59e0b22" : C.card2, border: `1px solid ${active ? "#f59e0b66" : C.border}`, color: active ? C.amber : C.text3, display: "flex", alignItems: "center", justifyContent: "center", cursor: "pointer", flexShrink: 0 }}>
      <Icon size={16} />
    </button>
  );

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

      <div style={{ padding: "10px 12px", borderTop: `1px solid ${C.border}`, background: C.card }}>
        <div style={{ display: "flex", alignItems: "center", gap: 8 }}>
          {expanded ? (
            <div style={{ display: "flex", gap: 6, alignItems: "center", animation: "slideIn 0.18s ease-out" }}>
              {ico(Paperclip, "doc", () => console.log("doc"))}
              {ico(Pin, "temp", () => setTempMode(v => !v), tempMode)}
              {ico(ImageIcon, "img", () => console.log("img"))}
              {ico(Camera, "cam", () => console.log("cam"))}
              <button onClick={() => setExpanded(false)}
                style={{ width: 36, height: 36, borderRadius: 10, background: "transparent", border: "none", color: C.muted, display: "flex", alignItems: "center", justifyContent: "center", cursor: "pointer", flexShrink: 0 }}>
                <ChevronRight size={18} style={{ transform: "rotate(180deg)" }} />
              </button>
            </div>
          ) : (
            <button onClick={() => setExpanded(true)}
              style={{ display: "flex", alignItems: "center", gap: 6, padding: "0 12px", height: 36, borderRadius: 18, background: C.card2, border: `1px solid ${C.border}`, color: C.text3, fontSize: 12, cursor: "pointer", flexShrink: 0, fontWeight: 600 }}
              title="Anexar">
              <Paperclip size={14} />
              <span>Anexar</span>
              {tempMode && <Pin size={11} style={{ color: C.amber }} />}
            </button>
          )}

          {!expanded && (
            <input
              value={text}
              onChange={e => setText(e.target.value)}
              placeholder="Pergunte"
              style={{ flex: 1, height: 34, padding: "0 12px", background: C.card2, border: `1px solid ${C.border}`, borderRadius: 10, color: C.text, fontSize: 13.5, outline: "none", minWidth: 0 }}
            />
          )}

          {!expanded && (
            <button style={{ width: 36, height: 34, borderRadius: 10, background: C.green, border: "none", color: "#000", fontWeight: 700, display: "flex", alignItems: "center", justifyContent: "center", cursor: "pointer", flexShrink: 0 }}>
              <Send size={15} />
            </button>
          )}
        </div>

        {tempMode && (
          <div style={{ marginTop: 6, fontSize: 10.5, color: C.amber, display: "flex", alignItems: "center", gap: 4 }}>
            <Pin size={10} /> Próximo anexo → pasta TEMP
          </div>
        )}
      </div>

      <style>{`@keyframes slideIn { from { opacity: 0; transform: translateX(-8px); } to { opacity: 1; transform: translateX(0); } }`}</style>
    </div>
  );
}
