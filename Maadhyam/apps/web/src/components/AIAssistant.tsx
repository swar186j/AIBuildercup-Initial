import { useEffect, useLayoutEffect, useRef, useState, type FormEvent } from "react";
import { useLocation, useNavigate } from "react-router-dom";
import { Bot, X, Send, Sparkles, ShieldAlert, ArrowRight, RotateCcw, FileSearch, LoaderCircle } from "lucide-react";
import { useDocuments } from "../context/DocumentContext";
import { askCitizen } from "../services/citizenIntelligence";

type Message = { id: number; role: "assistant" | "user"; text: string; link?: { label: string; path: string } };
const greeting: Message = { id: 1, role: "assistant", text: "Namaste! I'm Maadhyam's demo assistant. I can guide you through this workspace and summarize document details you've entered manually. I use reviewed Vault metadata, not uploaded file contents. I cannot verify government eligibility or acceptance." };
const pagePrompts: Record<string, string[]> = {
  documents: ["How many documents do I have?", "What document details are missing?", "How do I check discrepancies?"],
  applications: ["How do I track an application?", "What should I do next?", "Where are my documents?"],
  planner: ["How does the resolution planner work?", "What should I do next?", "Show my documents"],
  passport: ["Help me with passport preparation", "Where do I start?", "How do I check discrepancies?"],
  default: ["Help me with passport preparation", "What can Maadhyam do?", "Show my documents"],
};

function getPage(path: string) {
  if (path.startsWith("/documents")) return "documents";
  if (path.startsWith("/applications")) return "applications";
  if (path.startsWith("/planner")) return "planner";
  if (path.includes("passport")) return "passport";
  return "default";
}

export default function AIAssistant() {
  const { documents } = useDocuments();
  const location = useLocation();
  const page = getPage(location.pathname);
  const navigate = useNavigate();
  const [open, setOpen] = useState(false);
  useEffect(()=>{const show=()=>setOpen(true);window.addEventListener('maadhyam-open-assistant',show);return()=>window.removeEventListener('maadhyam-open-assistant',show);},[]);
  const [input, setInput] = useState("");
  const [messages, setMessages] = useState<Message[]>([greeting]);
  const [thinkingFor, setThinkingFor] = useState<typeof documents | null>(null);
  const thinking = thinkingFor === documents;
  const [useGemini, setUseGemini] = useState(false);
  const [fictionalConsent, setFictionalConsent] = useState(false);
  const nextId = useRef(2);
  const bottomRef = useRef<HTMLDivElement>(null);
  const generation=useRef(0);
  const panelRef=useRef<HTMLElement>(null);
  const openerRef=useRef<HTMLButtonElement>(null);
  const timerRef = useRef<ReturnType<typeof setTimeout> | null>(null);

  useEffect(() => { if (open) bottomRef.current?.scrollIntoView({ behavior: "smooth", block: "end" }); }, [messages, thinking, open]);
  useEffect(() => () => { if (timerRef.current) clearTimeout(timerRef.current); }, []);

  useLayoutEffect(()=>{generation.current+=1;},[documents]);
  useEffect(()=>{
    if(!open)return;
    panelRef.current?.querySelector<HTMLInputElement>('input[aria-label="Message to Maadhyam AI"]')?.focus();
    const escape=(event:KeyboardEvent)=>{if(event.key==='Escape'){setOpen(false);openerRef.current?.focus();}};
    document.addEventListener('keydown',escape);
    return()=>document.removeEventListener('keydown',escape);
  },[open]);
  function submit(content: string) {
    const clean = content.trim();
    if (!clean || thinking || (useGemini && !fictionalConsent)) return;
    setMessages(prev => [...prev, { id: nextId.current++, role: "user", text: clean }]);
    setInput("");
    const current=++generation.current;
    setThinkingFor(documents);
    askCitizen(documents, clean, useGemini, useGemini && fictionalConsent)
      .then(result => {if(current===generation.current)setMessages(prev => [...prev, { id: nextId.current++, role: "assistant", text: result.answer }]);})
      .catch(() => {if(current===generation.current)setMessages(prev => [...prev, { id: nextId.current++, role: "assistant", text: "Assistant unavailable. Check backend connection or turn off Gemini mode for local guidance." }]);})
      .finally(() => {if(current===generation.current)setThinkingFor(null);});
  }
  function sendMessage(event: FormEvent<HTMLFormElement>) { event.preventDefault(); submit(input); }
  function resetChat() {
    generation.current+=1;
    if (timerRef.current) clearTimeout(timerRef.current);
    timerRef.current = null;
    setThinkingFor(null);
    setMessages([greeting]);
    setInput("");
    setFictionalConsent(false);
    setUseGemini(false);
  }

  return (
    <div className="fixed bottom-4 right-4 z-50 sm:bottom-7 sm:right-7">
      {open && (
        <section ref={panelRef} role="dialog" aria-label="Maadhyam AI assistant" className="mb-3 flex h-[min(660px,78dvh)] w-[min(430px,calc(100vw-32px))] flex-col overflow-hidden rounded-2xl border border-slate-200 bg-white shadow-2xl dark:!border-[#253947] dark:!bg-[#162430]">
          <div className="flex items-center justify-between gap-2 bg-[#173f68] px-4 py-4 text-white dark:!bg-[#163b42]">
            <div className="flex min-w-0 items-center gap-3"><div className="rounded-xl bg-white/15 p-2"><Bot size={22}/></div><div><h2 className="font-semibold">Maadhyam AI</h2><p className="text-xs text-slate-200">Context-aware · local by default</p></div></div>
            <div className="flex items-center gap-1"><button type="button" onClick={resetChat} aria-label="Clear chat" title="Clear chat" className="rounded-lg p-2 hover:bg-white/10"><RotateCcw size={17}/></button><button type="button" onClick={() => setOpen(false)} aria-label="Close AI assistant" className="rounded-lg p-2 hover:bg-white/10"><X size={20}/></button></div>
          </div>
          <div className="flex items-start gap-2 border-b border-amber-100 bg-amber-50 px-4 py-3 text-xs leading-5 text-amber-900 dark:!border-[#544331] dark:!bg-[#29271f] dark:!text-[#ffcf91]"><ShieldAlert size={16} className="mt-0.5 shrink-0"/><span>Uses reviewed metadata. Gemini is optional for fictional demo data only. No government verification.</span></div>
          <div className="flex-1 space-y-4 overflow-y-auto bg-[#f8fafc] p-4 dark:!bg-[#090f16]" aria-live="polite" aria-relevant="additions text">
            {messages.map(message => <div key={message.id} className={`flex ${message.role === "user" ? "justify-end" : "justify-start"}`}><div className={`max-w-[90%] rounded-2xl px-4 py-3 text-sm leading-6 ${message.role === "user" ? "bg-[#173f68] text-white dark:!bg-[#16665d]" : "border border-slate-200 bg-white text-slate-700 dark:!border-[#253947] dark:!bg-[#162430] dark:!text-[#eaf4f7]"}`}><p className="whitespace-pre-wrap">{message.text}</p>{message.link && <button type="button" onClick={() => { navigate(message.link!.path); setOpen(false); }} className="mt-3 inline-flex items-center gap-1.5 font-semibold text-[#126a70] hover:underline">{message.link.label}<ArrowRight size={15}/></button>}</div></div>)}
            {thinking && <div className="flex items-center gap-2 text-xs text-slate-500"><LoaderCircle size={15} className="animate-spin"/> Preparing demo response…</div>}
            <div ref={bottomRef}/>
          </div>
          <div className="border-t border-slate-200 bg-white px-3 pt-3 dark:!border-[#253947] dark:!bg-[#162430]"><div className="mb-2 flex items-center gap-2 text-xs font-semibold text-slate-500"><FileSearch size={14}/> Suggested for this page</div><div className="flex flex-wrap gap-2 pb-3">{pagePrompts[page].map(prompt => <button key={prompt} type="button" disabled={thinking} onClick={() => submit(prompt)} className="max-w-full rounded-full border border-[#b9dada] bg-[#f2f8f8] px-3 py-2 text-left text-xs font-medium leading-5 text-[#126a70] hover:bg-[#e2f1f0] dark:!border-[#34545a] dark:!bg-[#1b343c] dark:!text-[#2fe9c2] dark:hover:!bg-[#24434b] disabled:opacity-50">{prompt}</button>)}</div></div>
          <label className="flex items-center gap-2 px-4 py-2 text-xs text-[#A7BBC8]"><input type="checkbox" checked={useGemini} onChange={e => { setUseGemini(e.target.checked); setFictionalConsent(false); }} /> Use Gemini (fictional demo metadata only)</label>
          {useGemini && <label className="flex items-start gap-2 px-4 pb-2 text-xs text-[#A7BBC8]"><input type="checkbox" aria-label="Confirm all metadata is fictional" checked={fictionalConsent} onChange={e => setFictionalConsent(e.target.checked)} /><span>I confirm all document metadata in this demo is fictional. Reviewed applicant metadata will be sent to Gemini; do not use real personal data.</span></label>}
          <form onSubmit={sendMessage} className="flex gap-2 border-t border-slate-100 bg-white p-3 dark:!border-[#253947] dark:!bg-[#162430]"><input value={input} onChange={event => setInput(event.target.value)} placeholder="Ask Maadhyam…" aria-label="Message to Maadhyam AI" maxLength={500} className="min-w-0 flex-1 rounded-xl border border-slate-200 px-4 py-3 text-sm outline-none focus:border-[#147d83] dark:!border-[#34545a] dark:!bg-[#0c1720] dark:!text-[#eaf4f7] dark:focus:!border-[#2fe9c2]"/><button type="submit" disabled={!input.trim() || thinking || (useGemini && !fictionalConsent)} aria-label="Send message" className="rounded-xl bg-[#147d83] px-4 text-white dark:!bg-[#16665d] dark:!text-white disabled:cursor-not-allowed disabled:opacity-40"><Send size={18}/></button></form>
        </section>
      )}
      <button ref={openerRef} type="button" onClick={() => setOpen(prev => !prev)} aria-label={open ? "Close Maadhyam AI" : "Open Maadhyam AI"} aria-expanded={open} className="flex items-center gap-3 rounded-full bg-[#173f68] px-5 py-4 text-white shadow-xl transition hover:bg-[#245782] dark:!bg-[#16665d] dark:hover:!bg-[#1b8174]">{open ? <X size={22}/> : <Sparkles size={22}/>}<span className="text-sm font-semibold">{open ? "Close" : "Ask Maadhyam AI"}</span></button>
    </div>
  );
}
