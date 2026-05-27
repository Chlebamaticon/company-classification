import { describe, it, expect } from "vitest";
import { parseSSEEvent } from "../api";

describe("parseSSEEvent", () => {
  it("parses a progress event", () => {
    const data = JSON.stringify({
      stage: "crawl",
      status: "started",
      detail: "Fetching…",
    });
    const result = parseSSEEvent("progress", data);
    expect(result).toEqual({
      kind: "progress",
      payload: { stage: "crawl", status: "started", detail: "Fetching…" },
    });
  });

  it("parses a result event with fsc_codes array", () => {
    const data = JSON.stringify({
      fsc_codes: [
        {
          code: "3408",
          title: "Machining Centers",
          rationale: "Makes CNC machines",
          confidence: 0.92,
        },
      ],
    });
    const result = parseSSEEvent("result", data);
    expect(result).toEqual({
      kind: "result",
      payload: {
        fsc_codes: [
          {
            code: "3408",
            title: "Machining Centers",
            rationale: "Makes CNC machines",
            confidence: 0.92,
          },
        ],
      },
    });
  });

  it("parses an error event", () => {
    const data = JSON.stringify({ message: "LLM timeout" });
    const result = parseSSEEvent("error", data);
    expect(result).toEqual({
      kind: "error",
      payload: { message: "LLM timeout" },
    });
  });

  it("returns null for unknown event type", () => {
    const data = JSON.stringify({ foo: "bar" });
    expect(parseSSEEvent("heartbeat", data)).toBeNull();
  });

  it("returns null for malformed JSON", () => {
    expect(parseSSEEvent("progress", "not json{")).toBeNull();
  });

  it("returns null for empty string data", () => {
    expect(parseSSEEvent("result", "")).toBeNull();
  });

  it("handles progress event with null detail", () => {
    const data = JSON.stringify({
      stage: "ingest",
      status: "done",
      detail: null,
    });
    const result = parseSSEEvent("progress", data);
    expect(result).toEqual({
      kind: "progress",
      payload: { stage: "ingest", status: "done", detail: null },
    });
  });

  it("preserves 4-digit code as string, not number", () => {
    const data = JSON.stringify({
      fsc_codes: [
        { code: "0100", title: "T", rationale: "R", confidence: 0.5 },
      ],
    });
    const result = parseSSEEvent("result", data);
    expect(result?.kind).toBe("result");
    if (result?.kind === "result") {
      expect(typeof result.payload.fsc_codes[0]!.code).toBe("string");
      expect(result.payload.fsc_codes[0]!.code).toBe("0100");
    }
  });
});
