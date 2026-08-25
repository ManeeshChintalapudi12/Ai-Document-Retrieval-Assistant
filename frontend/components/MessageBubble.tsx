"use client";

import type { ChatMessage } from "@/lib/types";
import { SourcesPanel } from "./SourcesPanel";

type MessageBubbleProps = {
  message: ChatMessage;
};

function LockIcon() {
  return (
    <svg aria-hidden="true" viewBox="0 0 20 20" className="h-4 w-4 fill-current">
      <path d="M10 1a4 4 0 0 0-4 4v3H5a2 2 0 0 0-2 2v7a2 2 0 0 0 2 2h10a2 2 0 0 0 2-2v-7a2 2 0 0 0-2-2h-1V5a4 4 0 0 0-4-4Zm-2 7V5a2 2 0 1 1 4 0v3H8Z" />
    </svg>
  );
}

export function MessageBubble({ message }: MessageBubbleProps) {
  const isUser = message.role === "user";
  const isDenied = Boolean(message.accessDenied);

  if (isUser) {
    return (
      <div className="ml-auto max-w-[80%] rounded-3xl rounded-tr-md bg-accent-600 px-4 py-3 text-sm text-white shadow-soft">
        {message.content}
      </div>
    );
  }

  return (
    <div className={`max-w-[86%] rounded-3xl rounded-tl-md border px-4 py-4 shadow-soft ${isDenied ? "border-warning-600/50 bg-warning-50 text-warning-700" : "border-white/10 bg-white/5 text-slate-100"}`}>
      <div className="flex items-start gap-2 text-sm leading-6">
        {isDenied ? <LockIcon /> : null}
        <p>{message.content}</p>
      </div>
      <div className="mt-3 text-xs uppercase tracking-[0.18em] text-slate-400">
        Confidence {(message.confidenceScore ?? 0).toFixed(2)}
      </div>
      <SourcesPanel sources={message.sources ?? []} />
    </div>
  );
}
