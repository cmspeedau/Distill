export interface ScrapeResponse {
  url: string;
  final_url: string;
  status_code: number;
  content_type: string;
  title: string | null;
  description: string | null;
  language: string | null;
  canonical_url: string | null;
  links: string[];
  markdown: string;
  cleaned_html: string;
  content_hash: string;
}

export class ApiError extends Error {
  constructor(
    message: string,
    readonly status: number,
    readonly code: string,
  ) {
    super(message);
    this.name = "ApiError";
  }
}

export async function scrapeUrl(
  url: string,
  includeImages = false,
  signal?: AbortSignal,
): Promise<ScrapeResponse> {
  const response = await fetch("/scrape", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ url, include_images: includeImages }),
    signal,
  });

  const data: unknown = await response.json();
  if (!response.ok) {
    const errorData = isRecord(data) ? data : {};
    throw new ApiError(
      typeof errorData.detail === "string" ? errorData.detail : "The scrape request failed.",
      response.status,
      typeof errorData.error === "string" ? errorData.error : "ApiError",
    );
  }

  if (!isScrapeResponse(data)) {
    throw new ApiError("The server returned an invalid response.", response.status, "InvalidResponse");
  }
  return data;
}

function isRecord(value: unknown): value is Record<string, unknown> {
  return typeof value === "object" && value !== null;
}

function isScrapeResponse(value: unknown): value is ScrapeResponse {
  if (!isRecord(value)) return false;
  return (
    typeof value.url === "string" &&
    typeof value.final_url === "string" &&
    typeof value.status_code === "number" &&
    typeof value.content_type === "string" &&
    (typeof value.title === "string" || value.title === null) &&
    (typeof value.description === "string" || value.description === null) &&
    (typeof value.language === "string" || value.language === null) &&
    (typeof value.canonical_url === "string" || value.canonical_url === null) &&
    Array.isArray(value.links) &&
    value.links.every((link) => typeof link === "string") &&
    typeof value.markdown === "string" &&
    typeof value.cleaned_html === "string" &&
    typeof value.content_hash === "string"
  );
}
