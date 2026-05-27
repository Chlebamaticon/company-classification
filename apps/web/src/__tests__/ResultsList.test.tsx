import { describe, it, expect } from "vitest";
import { render, screen } from "@testing-library/react";
import ResultsList from "../components/ResultsList";
import type { FscCodeAssignment } from "../types";

const CODES: FscCodeAssignment[] = [
  {
    code: "3408",
    title: "Machining Centers and Way-Type Machines",
    rationale: "Company manufactures CNC machining centers.",
    confidence: 0.92,
  },
  {
    code: "5945",
    title: "Relay and Solenoid",
    rationale: "Produces industrial relay modules.",
    confidence: 0.65,
  },
];

describe("ResultsList", () => {
  it("renders all codes in table", () => {
    render(<ResultsList codes={CODES} />);
    expect(screen.getByText("3408")).toBeInTheDocument();
    expect(screen.getByText("5945")).toBeInTheDocument();
  });

  it("displays titles", () => {
    render(<ResultsList codes={CODES} />);
    expect(
      screen.getByText("Machining Centers and Way-Type Machines"),
    ).toBeInTheDocument();
    expect(screen.getByText("Relay and Solenoid")).toBeInTheDocument();
  });

  it("shows confidence percentages", () => {
    render(<ResultsList codes={CODES} />);
    expect(screen.getByText("92%")).toBeInTheDocument();
    expect(screen.getByText("65%")).toBeInTheDocument();
  });

  it("renders table headers", () => {
    render(<ResultsList codes={CODES} />);
    expect(screen.getByText("Code")).toBeInTheDocument();
    expect(screen.getByText("Title")).toBeInTheDocument();
    expect(screen.getByText("Confidence")).toBeInTheDocument();
  });

  it("renders empty state for zero codes", () => {
    render(<ResultsList codes={[]} />);
    expect(screen.getByText("No FSC codes returned.")).toBeInTheDocument();
  });

  it("renders leading-zero codes correctly", () => {
    render(
      <ResultsList
        codes={[
          { code: "0100", title: "Nut/Bolt", rationale: "R", confidence: 0.5 },
        ]}
      />,
    );
    expect(screen.getByText("0100")).toBeInTheDocument();
  });
});
