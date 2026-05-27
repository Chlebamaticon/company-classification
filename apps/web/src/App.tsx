import { useCallback, useRef, useState } from "react";
import type {
  AppPhase,
  FscCodeAssignment,
  ProgressPayload,
  Stage,
  StageStatus,
  SubmissionForm as FormData,
} from "./types";
import SubmissionForm from "./components/SubmissionForm";
import ProgressPanel from "./components/ProgressPanel";
import ResultsList from "./components/ResultsList";
import ErrorBanner from "./components/ErrorBanner";

const useMock = import.meta.env.VITE_USE_MOCK === "true";
const api = useMock ? await import("./api.mock") : await import("./api");

const INITIAL_STAGES: Record<Stage, StageStatus | "pending"> = {
  ingest: "pending",
  crawl: "pending",
  classify: "pending",
};

export default function App() {
  const [phase, setPhase] = useState<AppPhase>("idle");
  const [stages, setStages] = useState<Record<Stage, StageStatus | "pending">>({
    ...INITIAL_STAGES,
  });
  const [results, setResults] = useState<FscCodeAssignment[]>([]);
  console.log(results);
  const [errorMsg, setErrorMsg] = useState("");
  const cleanupRef = useRef<(() => void) | null>(null);

  const reset = useCallback(() => {
    cleanupRef.current?.();
    cleanupRef.current = null;
    setPhase("idle");
    setStages({ ...INITIAL_STAGES });
    setResults([]);
    setErrorMsg("");
  }, []);

  const handleSubmit = useCallback(async (form: FormData) => {
    setPhase("submitting");
    setStages({
      ...INITIAL_STAGES,
      ...(!form.file ? { ingest: "skipped" as const } : {}),
      ...(!form.website_url ? { crawl: "skipped" as const } : {}),
    });
    setResults([]);
    setErrorMsg("");

    try {
      const { submission_id } = await api.postSubmission(form);
      setPhase("streaming");

      const cleanup = api.subscribeEvents(submission_id, {
        onProgress: (p: ProgressPayload) => {
          setStages((prev) => ({ ...prev, [p.stage]: p.status }));
        },
        onResult: (r) => {
          setResults(r.fsc_codes ?? []);
          setPhase("done");
          cleanupRef.current?.();
        },
        onError: (e) => {
          setErrorMsg(e.message);
          setPhase("error");
          cleanupRef.current?.();
        },
      });

      cleanupRef.current = cleanup;
    } catch (err) {
      setErrorMsg(err instanceof Error ? err.message : "Unknown error");
      setPhase("error");
    }
  }, []);

  const showForm = phase === "idle" || phase === "error";
  const showProgress =
    phase === "submitting" || phase === "streaming" || phase === "done";
  const showResults = phase === "done";

  return (
    <div className="mx-auto max-w-2xl px-4 py-10">
      <header className="mb-8 text-center">
        <h1 className="text-3xl font-bold tracking-tight text-gray-900">
          SalesPatriot
        </h1>
        <p className="mt-1 text-sm text-gray-500">
          Federal Supply Classification — AI-powered code assignment
        </p>
      </header>

      {phase === "error" && errorMsg && (
        <div className="mb-6">
          <ErrorBanner message={errorMsg} onDismiss={reset} />
        </div>
      )}

      {showForm && (
        <div className="rounded-xl border border-gray-200 bg-white p-6 shadow-sm">
          <SubmissionForm
            onSubmit={handleSubmit}
            disabled={phase !== "idle" && phase !== "error"}
          />
        </div>
      )}

      {showProgress && (
        <div className="mt-6">
          <ProgressPanel stageStatuses={stages} />
        </div>
      )}

      {showResults && (
        <div className="mt-6 space-y-4">
          <ResultsList codes={results} />
          <button
            type="button"
            onClick={reset}
            className="w-full rounded-md border border-gray-300 px-4 py-2 text-sm font-medium text-gray-700 shadow-sm hover:bg-gray-50"
          >
            Start New Classification
          </button>
        </div>
      )}
    </div>
  );
}
