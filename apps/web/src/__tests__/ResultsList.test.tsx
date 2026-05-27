import { describe, it, expect } from "vitest";
import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
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
  it("renders all code cards", () => {
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

  it("rationale is hidden by default and toggles on click", async () => {
    const user = userEvent.setup();
    render(<ResultsList codes={CODES} />);

    expect(
      screen.queryByText("Company manufactures CNC machining centers."),
    ).not.toBeInTheDocument();

    const buttons = screen.getAllByText("Show rationale");
    await user.click(buttons[0]!);

    expect(
      screen.getByText("Company manufactures CNC machining centers."),
    ).toBeInTheDocument();

    await user.click(screen.getAllByText("Hide rationale")[0]!);
    expect(
      screen.queryByText("Company manufactures CNC machining centers."),
    ).not.toBeInTheDocument();
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
