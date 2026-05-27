import type { FscCodeAssignment } from "../types";

interface Props {
  codes: FscCodeAssignment[];
}

function ConfidenceBadge({ value }: { value: number }) {
  const pct = Math.round(value * 100);
  const color =
    pct >= 80
      ? "text-green-700 bg-green-50"
      : pct >= 50
        ? "text-yellow-700 bg-yellow-50"
        : "text-red-700 bg-red-50";
  return (
    <span
      className={`inline-block rounded px-2 py-0.5 text-xs font-semibold ${color}`}
    >
      {pct}%
    </span>
  );
}

export default function ResultsList({ codes }: Props) {
  if (!codes || codes.length === 0) {
    return <p className="text-sm text-gray-500">No FSC codes returned.</p>;
  }

  return (
    <div className="rounded-lg border border-gray-200 bg-white shadow-sm overflow-hidden">
      <h3 className="px-4 py-3 text-sm font-semibold text-gray-600 uppercase tracking-wide border-b border-gray-100">
        Classified FSC Codes
      </h3>
      <table className="w-full text-sm text-left">
        <thead className="bg-gray-50 text-xs uppercase text-gray-500">
          <tr>
            <th className="px-4 py-2">Code</th>
            <th className="px-4 py-2">Title</th>
            <th className="px-4 py-2 text-right">Confidence</th>
          </tr>
        </thead>
        <tbody className="divide-y divide-gray-100">
          {codes.map((c) => (
            <tr key={c.code} className="hover:bg-gray-50">
              <td className="px-4 py-2 font-mono font-bold text-blue-700">
                {c.code}
              </td>
              <td className="px-4 py-2 text-gray-800">{c.title}</td>
              <td className="px-4 py-2 text-right">
                <ConfidenceBadge value={c.confidence} />
              </td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}
