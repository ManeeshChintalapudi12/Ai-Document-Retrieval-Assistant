"use client";

import { useState } from "react";
import { basename } from "path";
import type { RAGSource } from "@/lib/types";

type SourcesPanelProps = {
  sources: RAGSource[];
};

export function SourcesPanel({ sources }: SourcesPanelProps) {
  const [open, setOpen] = useState(false);

  if (sources.length === 0) {
    return null;
  }

  return (
    <div className="mt-3 rounded-2xl border border-white/10 bg-white/5 p-3">
      <button
        type="button"
        onClick={() => setOpen((current) => !current)}
        className="flex w-full items-center justify-between text-left text-xs font-semibold uppercase tracking-[0.2em] text-slate-300"
      >
        <span>Sources</span>
        <span>{open ? "−" : "+"}</span>
      </button>
      {open ? (
        <ul className="mt-3 space-y-2 text-sm text-slate-200">
          {sources.map((source, index) => (
            <li key={`${source.doc_name}-${source.page}-${index}`} className="rounded-xl border border-white/5 bg-slate-950/40 px-3 py-2">
              <div className="font-medium text-white">{basename(source.doc_name)}</div>
              <div className="text-xs text-slate-400">Page {source.page ?? "N/A"}</div>
            </li>
          ))}
        </ul>
      ) : null}
    </div>
  );
}
