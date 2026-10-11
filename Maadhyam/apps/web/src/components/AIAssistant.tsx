import { useState } from "react";
import {
  Bot,
  X,
  Send,
  Sparkles,
  ShieldAlert,
} from "lucide-react";

type Message = {
  id: number;
  role: "assistant" | "user";
  text: string;
};

const initialMessages: Message[] = [
  {
    id: 1,
    role: "assistant",
    text:
      "Namaste! I'm Maadhyam's AI assistant. I can help you explore services and understand document-related questions. I'm currently in demo mode.",
  },
];

function demoReply(message: string): string {
  const query = message.toLowerCase();

  if (query.includes("passport")) {
    return "For passport applications, document requirements can vary by applicant and application type. In the full version, I'll help check your documents against verified Passport Seva rules.";
  }

  if (query.includes("aadhaar") || query.includes("address")) {
    return "Address differences can affect some application workflows. In the full version, I'll compare document fields and show verified correction options.";
  }

  if (query.includes("epfo") || query.includes("pf")) {
    return "I can help you explore EPFO documentation workflows. Verified requirements and case-specific guidance will be available after the rules engine is connected.";
  }

  return "I understand your question. This is a frontend demonstration, so I can't verify eligibility, analyze uploaded documents, or provide case-specific government rules yet.";
}

export default function AIAssistant() {
  const [open, setOpen] = useState(false);
  const [input, setInput] = useState("");
  const [messages, setMessages] = useState(initialMessages);

  function sendMessage(event: React.FormEvent<HTMLFormElement>) {
    event.preventDefault();

    const content = input.trim();
    if (!content) return;

    setMessages((previous) => [
      ...previous,
      {
        id: Date.now(),
        role: "user",
        text: content,
      },
      {
        id: Date.now() + 1,
        role: "assistant",
        text: demoReply(content),
      },
    ]);

    setInput("");
  }

  return (
    <div className="fixed bottom-5 right-5 z-50 sm:bottom-7 sm:right-7">
      {open && (
        <section
          role="dialog"
          aria-label="Maadhyam AI assistant"
          className="mb-4 flex h-[min(560px,75dvh)] w-[min(390px,calc(100vw-40px))] flex-col overflow-hidden rounded-2xl border border-slate-200 bg-white shadow-2xl"
        >
          <div className="flex items-center justify-between bg-[#173f68] px-5 py-4 text-white">
            <div className="flex items-center gap-3">
              <div className="rounded-xl bg-white/15 p-2">
                <Bot size={23} />
              </div>

              <div>
                <h2 className="font-semibold">Maadhyam AI</h2>
                <p className="text-xs text-blue-100">
                  Demo assistant · Not connected to Gemini
                </p>
              </div>
            </div>

            <button
              aria-label="Close AI assistant"
              onClick={() => setOpen(false)}
              className="rounded-lg p-2 hover:bg-white/10"
            >
              <X size={20} />
            </button>
          </div>

          <div className="flex items-start gap-2 border-b border-amber-100 bg-amber-50 px-4 py-3 text-xs text-amber-900">
            <ShieldAlert size={16} className="mt-0.5 shrink-0" />
            Demo responses only. No documents or government rules are being verified.
          </div>

          <div
            aria-live="polite"
            className="flex-1 space-y-4 overflow-y-auto bg-[#f8fafc] p-4"
          >
            {messages.map((message) => (
              <div
                key={message.id}
                className={`flex ${
                  message.role === "user"
                    ? "justify-end"
                    : "justify-start"
                }`}
              >
                <div
                  className={`max-w-[88%] rounded-2xl px-4 py-3 text-sm leading-6 ${
                    message.role === "user"
                      ? "bg-[#173f68] text-white"
                      : "border border-slate-200 bg-white text-slate-700"
                  }`}
                >
                  {message.text}
                </div>
              </div>
            ))}
          </div>

          <form
            onSubmit={sendMessage}
            className="flex gap-2 border-t border-slate-200 bg-white p-3"
          >
            <input
              value={input}
              onChange={(event) => setInput(event.target.value)}
              placeholder="Ask Maadhyam..."
              aria-label="Message to Maadhyam AI"
              className="min-w-0 flex-1 rounded-xl border border-slate-200 px-4 py-3 text-sm outline-none focus:border-[#147d83]"
            />

            <button
              type="submit"
              disabled={!input.trim()}
              aria-label="Send message"
              className="rounded-xl bg-[#147d83] px-4 text-white disabled:cursor-not-allowed disabled:opacity-40"
            >
              <Send size={18} />
            </button>
          </form>
        </section>
      )}

      <button
        onClick={() => setOpen((previous) => !previous)}
        aria-label={open ? "Close Maadhyam AI" : "Open Maadhyam AI"}
        aria-expanded={open}
        className="flex items-center gap-3 rounded-full bg-[#173f68] px-5 py-4 text-white shadow-xl transition hover:bg-[#245782]"
      >
        {open ? <X size={22} /> : <Sparkles size={22} />}
        <span className="text-sm font-semibold">
          {open ? "Close" : "Ask Maadhyam AI"}
        </span>
      </button>
    </div>
  );
}