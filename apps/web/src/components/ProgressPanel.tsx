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

function StatusDot({ status }: { status: StageStatus | "pending" }) {
  const colors: Record<string, string> = {
    pending: "bg-gray-300",
    started: "bg-yellow-400 animate-pulse",
    done: "bg-green-500",
    failed: "bg-red-500",
  };
  return (
    <span
      className={`inline-block h-3 w-3 rounded-full ${colors[status] ?? colors.pending}`}
      role="img"
      aria-label={status}
    />
  );
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
              <StatusDot status={status} />
              <span className={status === "started" ? "font-medium text-yellow-700" : status === "done" ? "text-green-700" : "text-gray-700"}>
                {label}
              </span>
            </li>
          );
        })}
      </ul>
    </div>
  );
}
