export interface SubmissionForm {
  company_name: string;
  website_url: string;
  email_domain: string;
  file: File | null;
}

export interface SubmissionResponse {
  submission_id: string;
  status: "queued";
}

export interface SubmissionState {
  submission_id: string;
  status: string;
  fsc_codes: FscCodeAssignment[] | null;
}

export type Stage = "ingest" | "crawl" | "classify";
export type StageStatus = "started" | "done" | "failed";

export interface ProgressPayload {
  stage: Stage;
  status: StageStatus;
  detail: string | null;
}

export interface FscCodeAssignment {
  code: string;
  title: string;
  rationale: string;
  confidence: number;
}

export interface ResultPayload {
  fsc_codes: FscCodeAssignment[];
}

export interface ErrorPayload {
  message: string;
}

export type AppPhase = "idle" | "submitting" | "streaming" | "done" | "error";

export interface SSEHandlers {
  onProgress: (p: ProgressPayload) => void;
  onResult: (r: ResultPayload) => void;
  onError: (e: ErrorPayload) => void;
}
