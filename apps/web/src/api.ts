import type {
  SubmissionForm,
  SubmissionResponse,
  SSEHandlers,
  ProgressPayload,
  ResultPayload,
  ErrorPayload,
} from "./types";

const BASE = "/api";

export async function postSubmission(
  form: SubmissionForm,
): Promise<SubmissionResponse> {
  const body = new FormData();
  body.append("company_name", form.company_name);
  body.append("website_url", form.website_url);
  if (form.email_domain) body.append("email_domain", form.email_domain);
  if (form.file) body.append("file", form.file);

  const res = await fetch(`${BASE}/submissions`, { method: "POST", body });

  if (!res.ok) {
    const text = await res.text().catch(() => "Unknown error");
    throw new Error(`Submission failed (${res.status}): ${text}`);
  }

  return res.json() as Promise<SubmissionResponse>;
}

export function parseSSEEvent(
  type: string,
  data: string,
): { kind: "progress"; payload: ProgressPayload }
  | { kind: "result"; payload: ResultPayload }
  | { kind: "error"; payload: ErrorPayload }
  | null {
  try {
    const parsed: unknown = JSON.parse(data);
    switch (type) {
      case "progress":
        return { kind: "progress", payload: parsed as ProgressPayload };
      case "result":
        return { kind: "result", payload: parsed as ResultPayload };
      case "error":
        return { kind: "error", payload: parsed as ErrorPayload };
      default:
        return null;
    }
  } catch {
    return null;
  }
}

export function subscribeEvents(
  submissionId: string,
  handlers: SSEHandlers,
): () => void {
  const url = `${BASE}/submissions/${submissionId}/events`;
  const es = new EventSource(url);

  es.addEventListener("progress", (e: MessageEvent) => {
    const parsed = parseSSEEvent("progress", e.data as string);
    if (parsed?.kind === "progress") handlers.onProgress(parsed.payload);
  });

  es.addEventListener("result", (e: MessageEvent) => {
    const parsed = parseSSEEvent("result", e.data as string);
    if (parsed?.kind === "result") handlers.onResult(parsed.payload);
  });

  es.addEventListener("error", (e: MessageEvent) => {
    if (e.data) {
      const parsed = parseSSEEvent("error", e.data as string);
      if (parsed?.kind === "error") handlers.onError(parsed.payload);
    } else {
      handlers.onError({ message: "Connection lost" });
    }
  });

  es.onerror = () => {
    if (es.readyState === EventSource.CLOSED) {
      handlers.onError({ message: "SSE connection closed unexpectedly" });
    }
  };

  return () => es.close();
}
