import { useEffect, useRef, useState, type FormEvent } from "react";
import { useLocation, useNavigate } from "react-router-dom";
import { Bot, X, Send, Sparkles, ShieldAlert, ArrowRight, RotateCcw, FileSearch, LoaderCircle } from "lucide-react";
import { useDocuments } from "../context/DocumentContext";

type Message = { id: number; role: "assistant" | "user"; text: string; link?: { label: string; path: string } };
const greeting: Message = { id: 1, role: "assistant", text: "Namaste! I'm Maadhyam's demo assistant. I can guide you through this workspace and summarize document details you've entered manually. I cannot read uploaded files or verify government requirements yet." };
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
  const navigate = useNavigate();
  const [open, setOpen] = useState(false);
  const [input, setInput] = useState("");
  const [messages, setMessages] = useState<Message[]>([greeting]);
  const [thinking, setThinking] = useState(false);
  const nextId = useRef(2);
  const bottomRef = useRef<HTMLDivElement>(null);
  const timerRef = useRef<ReturnType<typeof setTimeout> | null>(null);
  const page = getPage(location.pathname);

  useEffect(() => { if (open) bottomRef.current?.scrollIntoView({ behavior: "smooth", block: "end" }); }, [messages, thinking, open]);
  useEffect(() => () => { if (timerRef.current) clearTimeout(timerRef.current); }, []);

  function reply(question: string): Omit<Message, "id" | "role"> {
    const q = question.toLowerCase();
    if (/how many|document count|number of documents|my documents|show my documents/.test(q)) {
      const reviewed = documents.filter(d => d.status === "reviewed").length;
      return { text: `Your current browser session has ${documents.length} document${documents.length === 1 ? "" : "s"}; ${reviewed} marked self-reviewed. This is a local count, not a government verification.`, link: { label: "Open Document Vault", path: "/documents" } };
    }
    if (/missing|incomplete|empty field|details/.test(q) && /document|field|detail|missing/.test(q)) {
      const incomplete = documents.filter(d => !d.metadata.printedName?.trim() || !d.metadata.dateOfBirth || !d.metadata.residentialAddress?.trim());
      return { text: documents.length === 0 ? "No documents have been added to this browser session. Upload a fictional sample file to try the demo." : `${incomplete.length} of ${documents.length} document(s) have at least one blank manually entered field (name, DOB, or address). A blank field may be normal for that document type; it is not automatically a problem.`, link: { label: "Review document details", path: "/documents" } };
    }
    if (/discrepan|mismatch|compare|difference/.test(q)) return { text: "Open Document Vault and select Analyze documents. The demo compares manually entered fields and flags possible differences. It does not read the file itself or determine which value is correct.", link: { label: "Analyze in Document Vault", path: "/documents" } };
    if (/passport/.test(q)) return { text: "The Passport Guided Journey helps you organize preparation based on your answers. It is a planning demo, not an official eligibility or document-acceptance check. Verify current requirements with Passport Seva before applying.", link: { label: "Open Passport Journey", path: "/services/passport/journey" } };
    if (/planner|next step|what should i do next|resolution/.test(q)) return { text: "The Resolution Planner provides a sample sequence of preparation tasks and dependencies. Open it to see the interactive checklist. The demo assistant cannot yet read its completion state.", link: { label: "Open Resolution Planner", path: "/planner" } };
    if (/application|track|draft/.test(q)) return { text: "My Applications currently contains demo application records and a preparation checklist. These are not real submitted applications, and no government status is being fetched.", link: { label: "Open My Applications", path: "/applications" } };
    if (/aadhaar|address|pan/.test(q)) return { text: "You can enter the details printed on each sample document in Document Vault and compare them. A different address or spelling does not necessarily mean a document is invalid; official correction guidance is not connected yet.", link: { label: "Open Document Vault", path: "/documents" } };
    if (/epfo|\bpf\b/.test(q)) return { text: "EPFO-specific workflows are not connected in this demo. You can explore available service cards, but I cannot confirm eligibility or live EPFO procedures.", link: { label: "Explore services", path: "/services" } };
    if (/what can|help|start|where/.test(q)) return { text: "I can navigate you to services, the Passport Guided Journey, Document Vault, My Applications and Resolution Planner. I can also count your local documents and identify blank manual metadata fields. All answers are demo guidance, not live AI or official rules.", link: { label: "Explore services", path: "/services" } };
    return { text: "I understand your question. This is a rule-based frontend demo, not Gemini. I can't read uploaded documents, verify government rules, or provide reliable case-specific answers yet. Try a suggested question or open the relevant workspace." };
  }

  function submit(content: string) {
    const clean = content.trim();
    if (!clean || thinking) return;
    setMessages(prev => [...prev, { id: nextId.current++, role: "user", text: clean }]);
    setInput("");
    setThinking(true);
    timerRef.current = setTimeout(() => {
      setMessages(prev => [...prev, { id: nextId.current++, role: "assistant", ...reply(clean) }]);
      setThinking(false);
      timerRef.current = null;
    }, 550);
  }
  function sendMessage(event: FormEvent<HTMLFormElement>) { event.preventDefault(); submit(input); }
  function resetChat() {
    if (timerRef.current) clearTimeout(timerRef.current);
    timerRef.current = null;
    setThinking(false);
    setMessages([greeting]);
    setInput("");
  }

  return (
    <div className="fixed bottom-4 right-4 z-50 sm:bottom-7 sm:right-7">
      {open && (
        <section role="dialog" aria-label="Maadhyam AI assistant" className="mb-3 flex h-[min(660px,78dvh)] w-[min(430px,calc(100vw-32px))] flex-col overflow-hidden rounded-2xl border border-slate-200 bg-white shadow-2xl dark:!border-[#253947] dark:!bg-[#162430]">
          <div className="flex items-center justify-between gap-2 bg-[#173f68] px-4 py-4 text-white dark:!bg-[#163b42]">
            <div className="flex min-w-0 items-center gap-3"><div className="rounded-xl bg-white/15 p-2"><Bot size={22}/></div><div><h2 className="font-semibold">Maadhyam AI</h2><p className="text-xs text-slate-200">Frontend demo · No Gemini connection</p></div></div>
            <div className="flex items-center gap-1"><button type="button" onClick={resetChat} aria-label="Clear chat" title="Clear chat" className="rounded-lg p-2 hover:bg-white/10"><RotateCcw size={17}/></button><button type="button" onClick={() => setOpen(false)} aria-label="Close AI assistant" className="rounded-lg p-2 hover:bg-white/10"><X size={20}/></button></div>
          </div>
          <div className="flex items-start gap-2 border-b border-amber-100 bg-amber-50 px-4 py-3 text-xs leading-5 text-amber-900 dark:!border-[#544331] dark:!bg-[#29271f] dark:!text-[#ffcf91]"><ShieldAlert size={16} className="mt-0.5 shrink-0"/><span>Simulated responses only. Uploaded files and government rules are not verified.</span></div>
          <div className="flex-1 space-y-4 overflow-y-auto bg-[#f8fafc] p-4 dark:!bg-[#090f16]" aria-live="polite" aria-relevant="additions text">
            {messages.map(message => <div key={message.id} className={`flex ${message.role === "user" ? "justify-end" : "justify-start"}`}><div className={`max-w-[90%] rounded-2xl px-4 py-3 text-sm leading-6 ${message.role === "user" ? "bg-[#173f68] text-white dark:!bg-[#16665d]" : "border border-slate-200 bg-white text-slate-700 dark:!border-[#253947] dark:!bg-[#162430] dark:!text-[#eaf4f7]"}`}><p className="whitespace-pre-wrap">{message.text}</p>{message.link && <button type="button" onClick={() => { navigate(message.link!.path); setOpen(false); }} className="mt-3 inline-flex items-center gap-1.5 font-semibold text-[#126a70] hover:underline">{message.link.label}<ArrowRight size={15}/></button>}</div></div>)}
            {thinking && <div className="flex items-center gap-2 text-xs text-slate-500"><LoaderCircle size={15} className="animate-spin"/> Preparing demo response…</div>}
            <div ref={bottomRef}/>
          </div>
          <div className="border-t border-slate-200 bg-white px-3 pt-3 dark:!border-[#253947] dark:!bg-[#162430]"><div className="mb-2 flex items-center gap-2 text-xs font-semibold text-slate-500"><FileSearch size={14}/> Suggested for this page</div><div className="flex flex-wrap gap-2 pb-3">{pagePrompts[page].map(prompt => <button key={prompt} type="button" disabled={thinking} onClick={() => submit(prompt)} className="max-w-full rounded-full border border-[#b9dada] bg-[#f2f8f8] px-3 py-2 text-left text-xs font-medium leading-5 text-[#126a70] hover:bg-[#e2f1f0] dark:!border-[#34545a] dark:!bg-[#1b343c] dark:!text-[#2fe9c2] dark:hover:!bg-[#24434b] disabled:opacity-50">{prompt}</button>)}</div></div>
          <form onSubmit={sendMessage} className="flex gap-2 border-t border-slate-100 bg-white p-3 dark:!border-[#253947] dark:!bg-[#162430]"><input value={input} onChange={event => setInput(event.target.value)} placeholder="Ask Maadhyam…" aria-label="Message to Maadhyam AI" maxLength={500} className="min-w-0 flex-1 rounded-xl border border-slate-200 px-4 py-3 text-sm outline-none focus:border-[#147d83] dark:!border-[#34545a] dark:!bg-[#0c1720] dark:!text-[#eaf4f7] dark:focus:!border-[#2fe9c2]"/><button type="submit" disabled={!input.trim() || thinking} aria-label="Send message" className="rounded-xl bg-[#147d83] px-4 text-white dark:!bg-[#16665d] dark:!text-white disabled:cursor-not-allowed disabled:opacity-40"><Send size={18}/></button></form>
        </section>
      )}
      <button type="button" onClick={() => setOpen(prev => !prev)} aria-label={open ? "Close Maadhyam AI" : "Open Maadhyam AI"} aria-expanded={open} className="flex items-center gap-3 rounded-full bg-[#173f68] px-5 py-4 text-white shadow-xl transition hover:bg-[#245782] dark:!bg-[#16665d] dark:hover:!bg-[#1b8174]">{open ? <X size={22}/> : <Sparkles size={22}/>}<span className="text-sm font-semibold">{open ? "Close" : "Ask Maadhyam AI"}</span></button>
    </div>
  );
}
