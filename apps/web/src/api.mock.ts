import type {
  SubmissionForm,
  SubmissionResponse,
  SSEHandlers,
} from "./types";

const FAKE_ID = "00000000-0000-0000-0000-000000000001";

const SCRIPT: Array<{ delay: number; fn: (h: SSEHandlers) => void }> = [
  { delay: 300, fn: (h) => h.onProgress({ stage: "ingest", status: "started", detail: null }) },
  { delay: 800, fn: (h) => h.onProgress({ stage: "ingest", status: "done", detail: null }) },
  { delay: 400, fn: (h) => h.onProgress({ stage: "crawl", status: "started", detail: "Fetching website…" }) },
  { delay: 1200, fn: (h) => h.onProgress({ stage: "crawl", status: "done", detail: null }) },
  { delay: 300, fn: (h) => h.onProgress({ stage: "classify", status: "started", detail: "Running LLM classification…" }) },
  { delay: 2000, fn: (h) => h.onProgress({ stage: "classify", status: "done", detail: null }) },
  {
    delay: 500,
    fn: (h) =>
      h.onResult({
        fsc_codes: [
          { code: "3408", title: "Machining Centers and Way-Type Machines", rationale: "Company manufactures CNC machining centers and multi-axis milling equipment.", confidence: 0.92 },
          { code: "3411", title: "Boring Machines", rationale: "Product line includes horizontal boring mills for large workpieces.", confidence: 0.78 },
          { code: "5945", title: "Relay and Solenoid", rationale: "Subsidiary produces industrial relay modules and solenoid actuators.", confidence: 0.65 },
        ],
      }),
  },
];

export async function postSubmission(
  _form: SubmissionForm,
): Promise<SubmissionResponse> {
  await new Promise((r) => setTimeout(r, 400));
  return { submission_id: FAKE_ID, status: "queued" };
}

export function subscribeEvents(
  _submissionId: string,
  handlers: SSEHandlers,
): () => void {
  const timers: ReturnType<typeof setTimeout>[] = [];
  let cumulative = 0;

  for (const step of SCRIPT) {
    cumulative += step.delay;
    timers.push(setTimeout(() => step.fn(handlers), cumulative));
  }

  return () => timers.forEach(clearTimeout);
}
