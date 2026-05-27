import { describe, it, expect, vi } from "vitest";
import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import SubmissionForm from "../components/SubmissionForm";

describe("SubmissionForm", () => {
  it("shows validation errors when submitted empty", async () => {
    const onSubmit = vi.fn();
    const user = userEvent.setup();
    render(<SubmissionForm onSubmit={onSubmit} disabled={false} />);

    await user.click(screen.getByRole("button", { name: /classify/i }));

    expect(screen.getByText("Company name is required.")).toBeInTheDocument();
    expect(screen.getByText("Website URL is required.")).toBeInTheDocument();
    expect(onSubmit).not.toHaveBeenCalled();
  });

  it("shows URL format error for bad URL", async () => {
    const onSubmit = vi.fn();
    const user = userEvent.setup();
    render(<SubmissionForm onSubmit={onSubmit} disabled={false} />);

    await user.type(screen.getByLabelText(/company name/i), "Acme Corp");
    await user.type(screen.getByLabelText(/website url/i), "not-a-url");
    await user.click(screen.getByRole("button", { name: /classify/i }));

    expect(
      screen.getByText("Enter a valid URL (http:// or https://)."),
    ).toBeInTheDocument();
    expect(onSubmit).not.toHaveBeenCalled();
  });

  it("calls onSubmit with correct data when valid", async () => {
    const onSubmit = vi.fn();
    const user = userEvent.setup();
    render(<SubmissionForm onSubmit={onSubmit} disabled={false} />);

    await user.type(screen.getByLabelText(/company name/i), "Acme Corp");
    await user.type(
      screen.getByLabelText(/website url/i),
      "https://acme.com",
    );
    await user.click(screen.getByRole("button", { name: /classify/i }));

    expect(onSubmit).toHaveBeenCalledOnce();
    expect(onSubmit).toHaveBeenCalledWith({
      company_name: "Acme Corp",
      website_url: "https://acme.com",
      email_domain: "",
      file: null,
    });
  });

  it("disables inputs and button when disabled=true", () => {
    render(<SubmissionForm onSubmit={vi.fn()} disabled={true} />);
    expect(screen.getByLabelText(/company name/i)).toBeDisabled();
    expect(screen.getByLabelText(/website url/i)).toBeDisabled();
    expect(screen.getByRole("button")).toBeDisabled();
    expect(screen.getByRole("button")).toHaveTextContent("Processing…");
  });
});
