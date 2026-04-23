import { useState } from "react";
import { Send, Paperclip, Pin, Image as ImageIcon, Camera, MoreHorizontal, X } from "lucide-react";

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

export function BottomSheet() {
  const [sheetOpen, setSheetOpen] = useState(false);
  const [tempMode, setTempMode] = useState(false);
  const [text, setText] = useState("");

  const tile = (Icon: any, label: string, sub: string, onClick: () => void, accent = C.green, active = false) => (
    <button onClick={onClick}
      style={{ display: "flex", flexDirection: "column", alignItems: "flex-start", gap: 6, padding: "12px 12px", background: active ? `${accent}22` : C.card2, border: `1px solid ${active ? `${accent}66` : C.border}`, borderRadius: 12, cursor: "pointer", color: C.text, textAlign: "left" }}>
      <div style={{ width: 32, height: 32, borderRadius: 9, background: `${accent}22`, color: accent, display: "flex", alignItems: "center", justifyContent: "center" }}>
        <Icon size={17} />
      </div>
      <div style={{ fontSize: 13, fontWeight: 600 }}>{label}</div>
      <div style={{ fontSize: 10.5, color: C.muted, lineHeight: 1.3 }}>{sub}</div>
    </button>
  );

  return (
    <div style={{ height: "100vh", background: C.bg, color: C.text, display: "flex", flexDirection: "column", fontFamily: "system-ui, -apple-system, sans-serif", position: "relative", overflow: "hidden" }}>
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
          <Pin size={12} /> TEMP ligado — próximo anexo vai para a pasta TEMP
        </div>
      )}

      <div style={{ padding: "10px 12px", borderTop: `1px solid ${C.border}`, background: C.card }}>
        <div style={{ display: "flex", alignItems: "center", gap: 8 }}>
          <button onClick={() => setSheetOpen(true)}
            style={{ width: 44, height: 44, minHeight: 44, minWidth: 44, borderRadius: 10, background: C.card2, border: `1px solid ${C.border}`, color: C.text3, display: "flex", alignItems: "center", justifyContent: "center", cursor: "pointer", flexShrink: 0, position: "relative" }}
            title="Mais ações">
            <MoreHorizontal size={18} />
            {tempMode && (
              <div style={{ position: "absolute", top: -3, right: -3, width: 12, height: 12, borderRadius: 6, background: C.amber, border: `2px solid ${C.card}` }} />
            )}
          </button>

          <input
            value={text}
            onChange={e => setText(e.target.value)}
            placeholder="Pergunte"
            style={{ flex: 1, height: 44, minHeight: 44, padding: "0 12px", background: C.card2, border: `1px solid ${C.border}`, borderRadius: 10, color: C.text, fontSize: 13.5, outline: "none" }}
          />

          <button style={{ width: 44, height: 44, minHeight: 44, minWidth: 44, borderRadius: 10, background: C.green, border: "none", color: "#000", fontWeight: 700, display: "flex", alignItems: "center", justifyContent: "center", cursor: "pointer", flexShrink: 0 }}>
            <Send size={16} />
          </button>
        </div>
      </div>

      {sheetOpen && (
        <div onClick={() => setSheetOpen(false)}
          style={{ position: "absolute", inset: 0, background: "rgba(0,0,0,0.55)", display: "flex", alignItems: "flex-end", animation: "fadeIn 0.18s ease-out", zIndex: 20 }}>
          <div onClick={e => e.stopPropagation()}
            style={{ width: "100%", background: C.card, borderTop: `1px solid ${C.border}`, borderRadius: "16px 16px 0 0", padding: "10px 14px 18px", animation: "slideUp 0.22s ease-out" }}>
            <div style={{ width: 38, height: 4, background: C.border, borderRadius: 2, margin: "0 auto 12px" }} />
            <div style={{ display: "flex", alignItems: "center", justifyContent: "space-between", marginBottom: 12 }}>
              <div style={{ fontSize: 13, fontWeight: 700, color: C.text }}>Anexar ao chat</div>
              <button onClick={() => setSheetOpen(false)}
                style={{ width: 36, height: 36, borderRadius: 10, background: "transparent", border: "none", color: C.muted, display: "flex", alignItems: "center", justifyContent: "center", cursor: "pointer" }}>
                <X size={18} />
              </button>
            </div>

            <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: 8 }}>
              {tile(Paperclip, "Documento", "PDF, DOC ou texto p/ biblioteca", () => setSheetOpen(false), C.blue)}
              {tile(Pin, "Marcar TEMP", tempMode ? "Ligado — toque p/ desligar" : "Arquivo que muda com freq.", () => { setTempMode(v => !v); }, C.amber, tempMode)}
              {tile(ImageIcon, "Imagem", "Viriato analisa a foto", () => setSheetOpen(false), C.green)}
              {tile(Camera, "Câmera", "Tirar foto agora", () => setSheetOpen(false), "#a78bfa")}
            </div>
          </div>
        </div>
      )}

      <style>{`
        @keyframes fadeIn { from { opacity: 0; } to { opacity: 1; } }
        @keyframes slideUp { from { transform: translateY(100%); } to { transform: translateY(0); } }
      `}</style>
    </div>
  );
}
