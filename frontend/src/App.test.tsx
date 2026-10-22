import { cleanup, fireEvent, render, screen, waitFor, within } from "@testing-library/react";
import { afterEach, describe, expect, it, vi } from "vitest";

import App from "./App";

afterEach(() => {
  cleanup();
  vi.unstubAllGlobals();
});

describe("scrape page", () => {
  it("submits a URL and renders the extracted Markdown", async () => {
    const fetchMock = vi.fn().mockResolvedValue({
      ok: true,
      status: 200,
      json: async () => ({
        url: "https://example.com/article",
        final_url: "https://example.com/article",
        status_code: 200,
        content_type: "text/html",
        title: "Test article",
        description: "An article description",
        language: "en",
        canonical_url: null,
        links: ["https://example.com/related"],
        markdown: "# Test article\n\nExtracted body.",
        cleaned_html: "<h1>Test article</h1><p>Extracted body.</p>",
        content_hash: "a".repeat(64),
      }),
    });
    vi.stubGlobal("fetch", fetchMock);

    render(<App />);
    fireEvent.change(screen.getByLabelText("PAGE URL"), {
      target: { value: "https://example.com/article" },
    });
    fireEvent.click(screen.getByRole("button", { name: /distill page/i }));

    expect(await screen.findByRole("region", { name: "Scrape result" })).toBeInTheDocument();
    expect(screen.getByRole("heading", { level: 2, name: "Test article" })).toBeInTheDocument();
    expect(screen.getByText("Extracted body.")).toBeInTheDocument();
    const result = screen.getByRole("region", { name: "Scrape result" });
    expect(within(result).getByText("1", { selector: ".result-stats strong" })).toBeInTheDocument();
    expect(fetchMock).toHaveBeenCalledWith(
      "/scrape",
      expect.objectContaining({
        method: "POST",
        body: JSON.stringify({ url: "https://example.com/article", include_images: false }),
      }),
    );
  });

  it("shows API errors accessibly", async () => {
    vi.stubGlobal(
      "fetch",
      vi.fn().mockResolvedValue({
        ok: false,
        status: 403,
        json: async () => ({ error: "BlockedByRobots", detail: "URL is disallowed by robots.txt" }),
      }),
    );

    render(<App />);
    fireEvent.change(screen.getByLabelText("PAGE URL"), {
      target: { value: "https://example.com/private" },
    });
    fireEvent.click(screen.getByRole("button", { name: /distill page/i }));

    await waitFor(() => expect(screen.getByRole("alert")).toHaveTextContent("URL is disallowed"));
  });
});
