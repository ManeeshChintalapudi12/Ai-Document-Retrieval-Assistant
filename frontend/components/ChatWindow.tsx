"use client";

import { FormEvent, useMemo, useState } from "react";
import { sendChatMessage } from "@/lib/api";
import type { ChatMessage, RoleOption } from "@/lib/types";
import { MessageBubble } from "./MessageBubble";
import { RoleSelector } from "./RoleSelector";

type ChatWindowProps = {
  roleOptions: RoleOption[];
};

const DEFAULT_ROLE = "user-hr";

export function ChatWindow({ roleOptions }: ChatWindowProps) {
  const [selectedUserId, setSelectedUserId] = useState(DEFAULT_ROLE);
  const [draft, setDraft] = useState("");
  const [messages, setMessages] = useState<ChatMessage[]>([]);
  const [error, setError] = useState<string | null>(null);
  const [isSending, setIsSending] = useState(false);

  const selectedRole = useMemo(
    () => roleOptions.find((option) => option.userId === selectedUserId) ?? roleOptions[0],
    [roleOptions, selectedUserId],
  );

  async function handleSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    const question = draft.trim();
    if (!question) {
      return;
    }

    setError(null);
    setDraft("");
    setIsSending(true);

    const userMessage: ChatMessage = {
      id: crypto.randomUUID(),
      role: "user",
      content: question,
    };

    setMessages((current) => [...current, userMessage]);

    try {
      const response = await sendChatMessage(question, selectedUserId);
      const assistantMessage: ChatMessage = {
        id: crypto.randomUUID(),
        role: "assistant",
        content: response.answer,
        sources: response.sources,
        confidenceScore: response.confidence_score,
        accessDenied: response.access_denied,
      };
      setMessages((current) => [...current, assistantMessage]);
    } catch (apiError) {
      setError(apiError instanceof Error ? apiError.message : "Something went wrong");
    } finally {
      setIsSending(false);
    }
  }

  return (
    <div className="grid min-h-[calc(100vh-2rem)] gap-6 lg:grid-cols-[280px_1fr]">
      <aside className="rounded-[32px] border border-white/10 bg-white/5 p-6 shadow-soft backdrop-blur">
        <div className="space-y-2">
          <p className="text-xs uppercase tracking-[0.28em] text-slate-400">Enterprise RAG</p>
          <h1 className="text-2xl font-semibold text-white">RBAC Chat</h1>
          <p className="text-sm leading-6 text-slate-300">
            Simulate access as HR, Engineering, Finance, or Admin and inspect how guardrails and metadata filtering behave.
          </p>
        </div>

        <div className="mt-6 space-y-4">
          <RoleSelector value={selectedUserId} options={roleOptions} onChange={setSelectedUserId} />
          <div className="rounded-2xl border border-white/10 bg-slate-950/30 p-4 text-sm text-slate-300">
            <div className="text-xs uppercase tracking-[0.2em] text-slate-400">Active role</div>
            <div className="mt-2 font-medium text-white">{selectedRole.label}</div>
            <div className="text-xs text-slate-400">{selectedRole.department}</div>
          </div>
        </div>
      </aside>

      <section className="flex flex-col rounded-[32px] border border-white/10 bg-slate-950/40 shadow-soft backdrop-blur">
        <div className="border-b border-white/10 px-6 py-4">
          <p className="text-sm uppercase tracking-[0.28em] text-slate-400">Conversation</p>
        </div>

        <div className="flex-1 space-y-4 overflow-y-auto px-6 py-6">
          {messages.length === 0 ? (
            <div className="rounded-3xl border border-dashed border-white/10 bg-white/5 p-8 text-sm leading-6 text-slate-300">
              Start with a policy question, a compensation query, or a prompt-injection attempt to see RBAC and guardrails in action.
            </div>
          ) : null}

          {messages.map((message) => (
            <MessageBubble key={message.id} message={message} />
          ))}
        </div>

        <form onSubmit={handleSubmit} className="border-t border-white/10 p-4">
          <div className="flex flex-col gap-3 sm:flex-row">
            <input
              value={draft}
              onChange={(event) => setDraft(event.target.value)}
              placeholder="Ask about a company document..."
              className="min-h-[52px] flex-1 rounded-2xl border border-white/10 bg-white/5 px-4 text-sm text-white outline-none transition placeholder:text-slate-500 focus:border-accent-500 focus:ring-2 focus:ring-accent-500/25"
            />
            <button
              type="submit"
              disabled={isSending}
              className="rounded-2xl bg-accent-600 px-5 py-3 text-sm font-semibold text-white transition hover:bg-accent-500 disabled:cursor-not-allowed disabled:opacity-60"
            >
              {isSending ? "Sending..." : "Send"}
            </button>
          </div>
          {error ? <p className="mt-3 text-sm text-warning-100">{error}</p> : null}
        </form>
      </section>
    </div>
  );
}
