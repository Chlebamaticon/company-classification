import { useState, useCallback, type FormEvent, type ChangeEvent } from "react";
import type { SubmissionForm as FormData } from "../types";

interface Props {
  onSubmit: (form: FormData) => void;
  disabled: boolean;
}

const URL_RE = /^https?:\/\/.+\..+/;

export default function SubmissionForm({ onSubmit, disabled }: Props) {
  const [companyName, setCompanyName] = useState("");
  const [websiteUrl, setWebsiteUrl] = useState("");
  const [emailDomain, setEmailDomain] = useState("");
  const [file, setFile] = useState<File | null>(null);
  const [errors, setErrors] = useState<Record<string, string>>({});

  const validate = useCallback((): Record<string, string> => {
    const e: Record<string, string> = {};
    if (!companyName.trim()) e.company_name = "Company name is required.";
    if (websiteUrl.trim() && !URL_RE.test(websiteUrl.trim()))
      e.website_url = "Enter a valid URL (http:// or https://).";
    if (!websiteUrl.trim() && !file)
      e.source = "Provide a Website URL or upload a Document.";
    return e;
  }, [companyName, websiteUrl, file]);

  const handleSubmit = (e: FormEvent) => {
    e.preventDefault();
    const errs = validate();
    setErrors(errs);
    if (Object.keys(errs).length > 0) return;
    onSubmit({
      company_name: companyName.trim(),
      website_url: websiteUrl.trim(),
      email_domain: emailDomain.trim() || "",
      file,
    });
  };

  const handleFile = (e: ChangeEvent<HTMLInputElement>) => {
    setFile(e.target.files?.[0] ?? null);
  };

  return (
    <form onSubmit={handleSubmit} className="space-y-5">
      <div>
        <label htmlFor="company_name" className="block text-sm font-medium text-gray-700">
          Company Name <span className="text-red-500">*</span>
        </label>
        <input
          id="company_name"
          type="text"
          value={companyName}
          onChange={(e) => setCompanyName(e.target.value)}
          disabled={disabled}
          className="mt-1 block w-full rounded-md border border-gray-300 px-3 py-2 shadow-sm focus:border-blue-500 focus:outline-none focus:ring-1 focus:ring-blue-500 disabled:bg-gray-100"
        />
        {errors.company_name && <p className="mt-1 text-sm text-red-600">{errors.company_name}</p>}
      </div>

      <div>
        <label htmlFor="website_url" className="block text-sm font-medium text-gray-700">
          Website URL
        </label>
        <input
          id="website_url"
          type="text"
          value={websiteUrl}
          onChange={(e) => setWebsiteUrl(e.target.value)}
          disabled={disabled}
          placeholder="https://example.com"
          className="mt-1 block w-full rounded-md border border-gray-300 px-3 py-2 shadow-sm focus:border-blue-500 focus:outline-none focus:ring-1 focus:ring-blue-500 disabled:bg-gray-100"
        />
        {errors.website_url && <p className="mt-1 text-sm text-red-600">{errors.website_url}</p>}
      </div>

      <div>
        <label htmlFor="email_domain" className="block text-sm font-medium text-gray-700">
          Email Domain <span className="text-gray-400">(optional)</span>
        </label>
        <input
          id="email_domain"
          type="text"
          value={emailDomain}
          onChange={(e) => setEmailDomain(e.target.value)}
          disabled={disabled}
          placeholder="example.com"
          className="mt-1 block w-full rounded-md border border-gray-300 px-3 py-2 shadow-sm focus:border-blue-500 focus:outline-none focus:ring-1 focus:ring-blue-500 disabled:bg-gray-100"
        />
      </div>

      <div>
        <label htmlFor="file" className="block text-sm font-medium text-gray-700">
          Supporting Document
        </label>
        <input
          id="file"
          type="file"
          onChange={handleFile}
          disabled={disabled}
          className="mt-1 block w-full text-sm text-gray-500 file:mr-4 file:rounded-md file:border-0 file:bg-blue-50 file:px-4 file:py-2 file:text-sm file:font-semibold file:text-blue-700 hover:file:bg-blue-100"
        />
      </div>

      {errors.source && <p className="text-sm text-red-600">{errors.source}</p>}

      <button
        type="submit"
        disabled={disabled}
        className="w-full rounded-md bg-blue-600 px-4 py-2.5 text-sm font-semibold text-white shadow-sm hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-blue-500 focus:ring-offset-2 disabled:cursor-not-allowed disabled:bg-blue-300"
      >
        {disabled ? "Processing…" : "Classify FSC Codes"}
      </button>
    </form>
  );
}
