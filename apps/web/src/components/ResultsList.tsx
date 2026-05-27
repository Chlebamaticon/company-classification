import { useState } from "react";
import type { FscCodeAssignment } from "../types";

interface Props {
  codes: FscCodeAssignment[];
}

function ConfidenceBar({ value }: { value: number }) {
  const pct = Math.round(value * 100);
  const color =
    pct >= 80 ? "bg-green-500" : pct >= 50 ? "bg-yellow-500" : "bg-red-400";
  return (
    <div className="flex items-center gap-2">
      <div className="h-2 w-24 rounded-full bg-gray-200">
        <div
          className={`h-2 rounded-full ${color}`}
          style={{ width: `${pct}%` }}
        />
      </div>
      <span className="text-xs text-gray-500">{pct}%</span>
    </div>
  );
}

function CodeCard({ code, title, rationale, confidence }: FscCodeAssignment) {
  const [open, setOpen] = useState(false);

  return (
    <div className="rounded-lg border border-gray-200 bg-white p-4 shadow-sm">
      <div className="flex items-start justify-between gap-4">
        <div>
          <span className="font-mono text-2xl font-bold text-blue-700">
            {code}
          </span>
          <p className="mt-1 text-sm font-medium text-gray-800">{title}</p>
        </div>
        <ConfidenceBar value={confidence} />
      </div>
      <button
        type="button"
        onClick={() => setOpen(!open)}
        className="mt-2 text-xs font-medium text-blue-600 hover:underline"
      >
        {open ? "Hide rationale" : "Show rationale"}
      </button>
      {open && (
        <p className="mt-2 text-sm leading-relaxed text-gray-600">
          {rationale}
        </p>
      )}
    </div>
  );
}

export default function ResultsList({ codes }: Props) {
  if (codes.length === 0) {
    return <p className="text-sm text-gray-500">No FSC codes returned.</p>;
  }

  return (
    <div className="space-y-3">
      <h3 className="text-sm font-semibold text-gray-600 uppercase tracking-wide">
        Classified FSC Codes
      </h3>
      {codes.map((c) => (
        <CodeCard key={c.code} {...c} />
      ))}
    </div>
  );
}
