"use client";

import type { RoleOption } from "@/lib/types";

type RoleSelectorProps = {
  value: string;
  options: RoleOption[];
  onChange: (value: string) => void;
};

export function RoleSelector({ value, options, onChange }: RoleSelectorProps) {
  return (
    <label className="flex flex-col gap-2 text-sm text-slate-300">
      <span className="font-medium tracking-wide text-slate-200">Mock login</span>
      <select
        value={value}
        onChange={(event) => onChange(event.target.value)}
        className="rounded-2xl border border-white/10 bg-white/5 px-4 py-3 text-sm text-white outline-none transition focus:border-accent-500 focus:ring-2 focus:ring-accent-500/30"
      >
        {options.map((option) => (
          <option key={option.userId} value={option.userId} className="bg-ink-900 text-white">
            {option.label} · {option.department}
          </option>
        ))}
      </select>
    </label>
  );
}
