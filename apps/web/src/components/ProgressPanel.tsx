import type { Stage, StageStatus } from "../types";

interface StageInfo {
  stage: Stage;
  label: string;
}

const STAGES: StageInfo[] = [
  { stage: "ingest", label: "Document Ingestion" },
  { stage: "crawl", label: "Website Crawl" },
  { stage: "classify", label: "FSC Classification" },
];

function statusIcon(status: StageStatus | "pending"): string {
  switch (status) {
    case "started":
      return "⏳";
    case "done":
      return "✅";
    case "failed":
      return "❌";
    default:
      return "○";
  }
}

interface Props {
  stageStatuses: Record<Stage, StageStatus | "pending">;
}

export default function ProgressPanel({ stageStatuses }: Props) {
  return (
    <div className="rounded-lg border border-gray-200 bg-white p-4 shadow-sm">
      <h3 className="mb-3 text-sm font-semibold text-gray-600 uppercase tracking-wide">
        Progress
      </h3>
      <ul className="space-y-2">
        {STAGES.map(({ stage, label }) => {
          const status = stageStatuses[stage];
          return (
            <li key={stage} className="flex items-center gap-2 text-sm">
              <span className="text-base" role="img" aria-label={status}>
                {statusIcon(status)}
              </span>
              <span className={status === "started" ? "font-medium text-blue-600" : "text-gray-700"}>
                {label}
              </span>
            </li>
          );
        })}
      </ul>
    </div>
  );
}
