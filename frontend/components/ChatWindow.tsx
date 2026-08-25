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

const NAV_ITEMS = ["Assistant", "Documents", "Collections", "Access Control", "Audit Logs", "Data Sources", "Settings"];

const SOURCE_DOCUMENTS = [
  ["PDF", "AI Usage Policy", "Updated today"],
  ["DOC", "Employee Handbook", "Updated today"],
  ["TXT", "Security Policy", "Updated today"],
  ["TXT", "Incident Response", "Updated today"],
];

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
    <div className="app-shell">
      <aside className="sidebar">
        <div className="brand-mark">✦</div>
        <nav className="nav-list" aria-label="Primary navigation">
          {NAV_ITEMS.map((item, index) => (
            <button key={item} type="button" className={`nav-item ${index === 0 ? "nav-item-active" : ""}`}>
              <span className="nav-icon">{["▣", "▤", "▥", "♢", "▧", "◉", "⚙"][index]}</span>
              {item}
            </button>
          ))}
        </nav>
        <div className="sidebar-status">
          <span className="status-dot" />
          <div><span className="status-label">System Status</span><strong>Operational</strong></div>
          <div className="secure-row">⌑ <span>All systems secure</span></div>
        </div>
      </aside>

      <main className="workspace">
        <header className="workspace-header">
          <div>
            <p className="eyebrow">Secure enterprise search</p>
            <h1>Knowledge Assistant</h1>
            <p>Secure RAG-powered search and answers from your enterprise data</p>
          </div>
          <div className="header-controls">
            <RoleSelector value={selectedUserId} options={roleOptions} onChange={setSelectedUserId} />
            <button type="button" className="icon-button" aria-label="Open filters">☷</button>
          </div>
        </header>

        <section className="conversation-panel">
          <div className="conversation-scroll">
            {messages.length === 0 ? (
              <div className="empty-state">
                <div className="assistant-badge">✦</div>
                <h2>Ask your enterprise knowledge base</h2>
                <p>Search authorized company documents and receive answers with source citations.</p>
              </div>
            ) : null}
            {messages.map((message) => <MessageBubble key={message.id} message={message} />)}
          </div>
          <form onSubmit={handleSubmit} className="composer">
            <input value={draft} onChange={(event) => setDraft(event.target.value)} placeholder="Ask a question or search your documents..." aria-label="Search documents" />
            <button type="submit" disabled={isSending} className="send-button" aria-label="Send question">{isSending ? "..." : "➤"}</button>
          </form>
          {error ? <p className="error-message">{error}</p> : <p className="privacy-note">⌑ Responses are generated using authorized enterprise data only.</p>}
        </section>
      </main>

      <aside className="inspector-rail">
        <section className="rail-section">
          <div className="section-heading"><h2>Source Documents</h2><button type="button">View all</button></div>
          <div className="source-list">
            {SOURCE_DOCUMENTS.map(([type, name, updated]) => <div className="source-row" key={name}><span className={`file-icon file-${type.toLowerCase()}`}>{type}</span><div><span className="source-type">Document</span><strong>{name}</strong><small>{updated}</small></div><span className="chevron">›</span></div>)}
          </div>
        </section>
        <section className="rail-section">
          <div className="section-heading"><h2>Role &amp; Permissions</h2><button type="button">View all</button></div>
          <div className="permission-card"><span className="permission-icon">♢</span><div><strong>{selectedRole.label} user</strong><div className="permission-tags"><span>Documents: Read</span><span>Query: Allowed</span></div></div></div>
          <div className="permission-card"><span className="permission-icon permission-blue">⌑</span><div><strong>RBAC enforced</strong><div className="permission-tags"><span>Metadata filtered</span><span>Guardrails active</span></div></div></div>
        </section>
        <section className="rail-section vector-section"><div className="section-heading"><h2>Vector Database</h2><span className="live-label"><span className="status-dot" /> Live</span></div><div className="vector-visual"><span className="cluster cluster-one" /><span className="cluster cluster-two" /><span className="cluster cluster-three" /></div><p className="vector-caption">⌑ Secure embeddings store</p></section>
      </aside>
    </div>
  );
}
