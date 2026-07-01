import { ArrowLeft, Send, Sparkles, User } from "lucide-react";
import { useEffect, useMemo, useRef, useState } from "react";

import { Skeleton } from "@/components/ui/skeleton";
import { Spinner } from "@/components/ui/spinner";
import { errorMessage } from "@/lib/api";
import { formatClock, formatRelative } from "@/lib/datetime";
import { cn } from "@/lib/utils";
import {
  useConversationMessages,
  useConversations,
  useSendMessage,
  useToggleAI,
  type Conversation,
  type Message,
} from "./api";

const AVATAR_PALETTE = [
  "linear-gradient(135deg,#7C3AED,#A78BFA)",
  "linear-gradient(135deg,#0D9488,#2DD4BF)",
  "linear-gradient(135deg,#2563EB,#60A5FA)",
  "linear-gradient(135deg,#D97706,#FBBF24)",
  "linear-gradient(135deg,#DB2777,#F472B6)",
];

function displayName(c: Conversation): string {
  return c.patient_nome || c.external_number;
}

function nameInitial(name: string): string {
  const first = name.replace(/^\+\d+/, "#").trim();
  return /[a-zA-Z]/.test(first[0]) ? first[0].toUpperCase() : "#";
}

function avatarGradient(index: number): string {
  return AVATAR_PALETTE[index % AVATAR_PALETTE.length];
}

// ─── Message Bubble ──────────────────────────────────────────────────────────
function MessageBubble({ msg }: { msg: Message }) {
  const isPatient = msg.sender === "patient";

  const bubbleStyle: React.CSSProperties =
    msg.sender === "ai"
      ? { background: "var(--bubble-ia-bg)", color: "var(--bubble-ia-text)", border: "1px solid var(--bubble-ia-border)", borderRadius: "16px 4px 16px 16px" }
      : isPatient
      ? { background: "hsl(var(--secondary))", color: "hsl(var(--secondary-foreground))", borderRadius: "4px 16px 16px 16px" }
      : { background: "#7C3AED", color: "#fff", borderRadius: "16px 4px 16px 16px" };

  const chipLabel = msg.sender === "ai" ? "IA" : isPatient ? "Paciente" : "Clínica";
  const chipColor = msg.sender === "ai" ? "#0D9488" : isPatient ? "hsl(var(--muted-foreground))" : "#7C3AED";

  return (
    <div
      className={cn("animate-bubble-in flex flex-col", isPatient ? "items-start" : "items-end")}
    >
      <div className={cn("mb-1 flex items-center gap-1.5 px-1 text-[11px]")} style={{ color: chipColor }}>
        {msg.sender === "ai" && <Sparkles className="h-3 w-3" />}
        {isPatient && <User className="h-3 w-3" />}
        <span className="font-bold">{chipLabel}</span>
        <span className="text-muted-foreground">{formatClock(msg.created_at)}</span>
      </div>
      <div
        className="max-w-[64%] px-3.5 py-2.5 text-sm leading-relaxed"
        style={bubbleStyle}
      >
        {msg.text}
      </div>
    </div>
  );
}

// ─── Conversation List ───────────────────────────────────────────────────────
function ConvRow({ c, index, active, onSelect }: { c: Conversation; index: number; active: boolean; onSelect: () => void }) {
  const initial = nameInitial(displayName(c));
  const bg = avatarGradient(index);
  return (
    <button
      onClick={onSelect}
      className={cn(
        "flex w-full items-start gap-3 rounded-[13px] px-3.5 py-3 text-left transition-all",
        active
          ? "[background:hsl(var(--nav-active-bg))] [box-shadow:inset_0_0_0_1px_hsl(var(--nav-active-ring))]"
          : "hover:bg-secondary",
      )}
    >
      <div className="relative shrink-0">
        <div
          className="flex h-11 w-11 items-center justify-center rounded-full text-base font-bold text-white"
          style={{ background: bg }}
        >
          {initial}
        </div>
        {c.ai_enabled && (
          <span className="absolute -bottom-0.5 -right-0.5 flex h-[18px] w-[18px] items-center justify-center rounded-full border-2 border-card bg-teal">
            <Sparkles className="h-2 w-2 text-white" />
          </span>
        )}
      </div>
      <div className="min-w-0 flex-1">
        <div className="flex items-center gap-1.5">
          <span className={cn("flex-1 truncate text-sm text-foreground", c.unread ? "font-extrabold" : "font-bold")}>
            {displayName(c)}
          </span>
          <span className="shrink-0 text-[11px] text-muted-foreground">{formatRelative(c.last_message_at)}</span>
        </div>
        <div className="mt-0.5 flex items-center gap-1">
          {c.last_message_sender === "ai" && <Sparkles className="h-3 w-3 shrink-0 text-primary" />}
          <span className={cn("truncate text-xs", c.unread ? "font-semibold text-foreground" : "text-muted-foreground")}>
            {c.last_message_preview ?? "—"}
          </span>
        </div>
      </div>
      {c.unread && <span className="mt-1.5 h-2 w-2 shrink-0 rounded-full bg-primary" />}
    </button>
  );
}

// ─── Thread ──────────────────────────────────────────────────────────────────
function Thread({ conversation, index }: { conversation: Conversation; index: number }) {
  const messages = useConversationMessages(conversation.id);
  const send = useSendMessage(conversation.id);
  const toggleAI = useToggleAI(conversation.id);
  const [text, setText] = useState("");
  const bottomRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages.data]);

  function handleSend() {
    const value = text.trim();
    if (!value || conversation.ai_enabled) return;
    send.mutate(value, { onSuccess: () => setText("") });
  }

  const initial = nameInitial(displayName(conversation));
  const bg = avatarGradient(index);

  return (
    <div className="flex min-h-0 flex-1 flex-col">
      {/* Cabeçalho thread */}
      <div
        className="flex h-[70px] shrink-0 items-center gap-3 border-b px-[22px]"
        style={{ background: "var(--glass)", backdropFilter: "blur(8px)" }}
      >
        <div
          className="flex h-[42px] w-[42px] shrink-0 items-center justify-center rounded-full text-base font-bold text-white"
          style={{ background: bg }}
        >
          {initial}
        </div>
        <div className="min-w-0 flex-1">
          <div className="truncate text-[15px] font-bold text-foreground">{displayName(conversation)}</div>
          <div className="truncate text-[12.5px] tabular-nums text-muted-foreground">{conversation.external_number}</div>
        </div>

        {/* AI Toggle */}
        <div className="flex shrink-0 items-center gap-2 rounded-xl border bg-secondary px-2.5 py-2 sm:gap-3 sm:px-3.5">
          <div className="flex flex-col items-end leading-tight">
            <span className="text-[13px] font-bold text-foreground">Atendimento por IA</span>
            <span className="text-[11.5px] font-semibold" style={{ color: conversation.ai_enabled ? "#0D9488" : "#D97706" }}>
              {conversation.ai_enabled ? "IA ativa" : "IA pausada"}
            </span>
          </div>
          <button
            onClick={() => toggleAI.mutate()}
            disabled={toggleAI.isPending}
            className="relative h-6 w-10 shrink-0 rounded-full border-none outline-none transition-all disabled:opacity-50"
            style={{ background: conversation.ai_enabled ? "#0D9488" : "#D4D4D8" }}
          >
            <span
              className="absolute top-[3px] h-[18px] w-[18px] rounded-full bg-white shadow-[0_1px_3px_rgba(0,0,0,.2)] transition-all"
              style={{ left: conversation.ai_enabled ? "21px" : "3px" }}
            />
          </button>
        </div>
      </div>

      {/* Mensagens */}
      <div
        className="min-h-0 flex-1 overflow-y-auto px-[26px] py-6"
        style={{ background: "linear-gradient(180deg, hsl(var(--background)), hsl(var(--background)))" }}
      >
        {messages.isLoading ? (
          <div className="flex justify-center p-6">
            <Spinner className="text-primary" />
          </div>
        ) : (
          <div className="flex flex-col gap-3.5">
            <div className="mb-1 text-center">
              <span className="rounded-full bg-card px-3 py-1 text-[11.5px] font-semibold text-muted-foreground shadow-sm">
                Hoje
              </span>
            </div>
            {(messages.data ?? []).map((m) => (
              <MessageBubble key={m.id} msg={m} />
            ))}
            <div ref={bottomRef} />
          </div>
        )}
      </div>

      {/* Composer */}
      <div
        className="shrink-0 border-t px-[22px] pb-[18px] pt-3.5"
        style={{ background: "var(--glass)", backdropFilter: "blur(8px)" }}
      >
        {conversation.ai_enabled ? (
          <div className="flex items-center gap-2 rounded-xl border border-teal/30 bg-teal-bg px-3.5 py-3 text-[13px] font-semibold text-teal">
            <Sparkles className="h-4 w-4 shrink-0" />
            A IA está respondendo automaticamente. Pause para assumir a conversa.
          </div>
        ) : (
          <div>
            {send.isError && (
              <p className="mb-2 text-xs text-destructive">{errorMessage(send.error)}</p>
            )}
            <div className="flex items-end gap-2.5">
              <textarea
                value={text}
                onChange={(e) => setText(e.target.value)}
                onKeyDown={(e) => {
                  if (e.key === "Enter" && !e.shiftKey) {
                    e.preventDefault();
                    handleSend();
                  }
                }}
                placeholder="Escreva uma mensagem… (Enter envia)"
                rows={1}
                className="max-h-32 flex-1 resize-none rounded-[13px] border border-input bg-card px-4 py-3 text-sm leading-relaxed text-foreground placeholder:text-muted-foreground focus:border-primary focus:outline-none focus:ring-2 focus:ring-primary/20 transition-all"
              />
              <button
                onClick={handleSend}
                disabled={send.isPending || !text.trim()}
                className="flex h-[46px] w-[46px] shrink-0 items-center justify-center rounded-[13px] bg-primary text-white shadow-[0_4px_12px_rgba(124,58,237,.3)] transition-all hover:-translate-y-px disabled:opacity-50"
              >
                {send.isPending ? <Spinner className="h-4 w-4" /> : <Send className="h-[19px] w-[19px]" />}
              </button>
            </div>
          </div>
        )}
      </div>
    </div>
  );
}

// ─── Page ─────────────────────────────────────────────────────────────────────
export function ConversationsPage() {
  const [search, setSearch] = useState("");
  const conversations = useConversations(search.trim() || undefined);
  const [activeId, setActiveId] = useState<string | null>(null);

  const items = conversations.data ?? [];
  const active = useMemo(() => items.find((c) => c.id === activeId) ?? null, [items, activeId]);
  const activeIndex = useMemo(() => items.findIndex((c) => c.id === activeId), [items, activeId]);

  return (
    <div className="flex h-full min-h-[520px] flex-col">
      <div className="flex min-h-0 flex-1 overflow-hidden rounded-[18px] border bg-card shadow-[0_1px_2px_rgba(16,24,40,.04)]">
        {/* Lista */}
        <div
          className={cn(
            "w-full shrink-0 border-r bg-card md:w-[340px]",
            active && "hidden md:flex md:flex-col",
          )}
        >
          <div className="border-b px-[18px] py-[18px]">
            <h2 className="mb-3 text-lg font-extrabold tracking-tight text-foreground">Conversas</h2>
            <div className="relative">
              <svg className="absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-muted-foreground" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2"><circle cx="11" cy="11" r="8" /><path d="m21 21-4.3-4.3" /></svg>
              <input
                value={search}
                onChange={(e) => setSearch(e.target.value)}
                placeholder="Buscar conversa..."
                className="w-full rounded-[10px] border border-input bg-secondary py-2 pl-9 pr-3 text-[13.5px] text-foreground placeholder:text-muted-foreground focus:border-primary focus:bg-card focus:outline-none focus:ring-2 focus:ring-primary/20 transition-all"
              />
            </div>
          </div>

          <div className="flex-1 overflow-y-auto p-2.5">
            {conversations.isLoading ? (
              <div className="flex flex-col gap-2 p-1">
                <Skeleton className="h-14 w-full rounded-[13px]" />
                <Skeleton className="h-14 w-full rounded-[13px]" />
                <Skeleton className="h-14 w-full rounded-[13px]" />
              </div>
            ) : items.length === 0 ? (
              <p className="p-6 text-center text-sm text-muted-foreground">
                {search.trim()
                  ? "Nenhuma conversa encontrada para essa busca."
                  : "Nenhuma conversa ainda. Quando um paciente mandar mensagem no WhatsApp, ela aparece aqui."}
              </p>
            ) : (
              <div className="flex flex-col gap-0.5">
                {items.map((c, i) => (
                  <ConvRow
                    key={c.id}
                    c={c}
                    index={i}
                    active={activeId === c.id}
                    onSelect={() => setActiveId(c.id)}
                  />
                ))}
              </div>
            )}
          </div>
        </div>

        {/* Thread */}
        <div className={cn("min-w-0 flex-1", !active && "hidden md:flex")}>
          {active ? (
            <div className="flex h-full min-h-0 flex-col">
              {/* Botão voltar mobile */}
              <button
                onClick={() => setActiveId(null)}
                className="flex items-center gap-1.5 border-b px-4 py-2 text-sm text-muted-foreground md:hidden"
              >
                <ArrowLeft className="h-4 w-4" />
                Voltar
              </button>
              <Thread conversation={active} index={activeIndex} />
            </div>
          ) : (
            <div className="flex h-full flex-col items-center justify-center gap-3 p-6 text-center">
              <div className="flex h-12 w-12 items-center justify-center rounded-full bg-accent text-primary">
                <Sparkles className="h-6 w-6" />
              </div>
              <p className="text-sm font-semibold text-foreground">Selecione uma conversa</p>
              <p className="max-w-xs text-xs text-muted-foreground">
                Veja o histórico do paciente com a recepcionista virtual (Gemini) e responda manualmente quando precisar assumir.
              </p>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
