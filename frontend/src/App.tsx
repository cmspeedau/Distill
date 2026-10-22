import { useState } from "react";
import type { FormEvent } from "react";
import ReactMarkdown from "react-markdown";

import { ApiError, scrapeUrl, type ScrapeResponse } from "./api/scrape";

export default function App() {
  const [url, setUrl] = useState("");
  const [includeImages, setIncludeImages] = useState(false);
  const [result, setResult] = useState<ScrapeResponse | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);
  const [copied, setCopied] = useState(false);

  async function handleSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setLoading(true);
    setError(null);
    setResult(null);
    setCopied(false);

    try {
      const response = await scrapeUrl(url.trim(), includeImages);
      setResult(response);
    } catch (cause) {
      setError(cause instanceof ApiError ? cause.message : "Could not reach Distill. Try again.");
    } finally {
      setLoading(false);
    }
  }

  async function copyMarkdown() {
    if (!result) return;
    try {
      await navigator.clipboard.writeText(result.markdown);
      setCopied(true);
      window.setTimeout(() => setCopied(false), 1800);
    } catch {
      setError("Clipboard access is unavailable in this browser.");
    }
  }

  return (
    <div className="app-shell">
      <aside className="sidebar" aria-label="Main navigation">
        <a className="brand" href="#top" aria-label="Distill home">
          <span className="brand-mark" aria-hidden="true">D</span>
          <span className="brand-name">distill<span className="brand-dot">.</span></span>
        </a>
        <div className="side-section-label">WORKSPACE</div>
        <nav className="side-nav">
          <a className="side-link active" href="#scrape" aria-current="page">
            <span className="nav-icon" aria-hidden="true">↧</span> Scrape URL
          </a>
          <span className="side-link disabled" aria-disabled="true" title="Available in a later phase">
            <span className="nav-icon" aria-hidden="true">▤</span> Ledger
            <span className="nav-soon">SOON</span>
          </span>
          <span className="side-link disabled" aria-disabled="true" title="Available in a later phase">
            <span className="nav-icon" aria-hidden="true">⌕</span> Search
            <span className="nav-soon">SOON</span>
          </span>
        </nav>
        <div className="sidebar-bottom">
          <div className="connection-status"><span className="status-dot" /> SELF-HOSTED INSTANCE</div>
          <div className="sidebar-version">DISTILL · LOCAL INSTANCE</div>
        </div>
      </aside>

      <main className="main-area" id="top">
        <header className="topbar">
          <div className="breadcrumb"><span>Workspace</span><span className="crumb-sep">/</span><strong>Scrape URL</strong></div>
          <div className="topbar-right"><span className="instance-pill"><span className="status-dot" /> LOCAL</span></div>
        </header>

        <div className="content-wrap" id="scrape">
          <section className="intro">
            <div className="eyebrow"><span className="eyebrow-line" /> WEB EXTRACTION</div>
            <h1>Turn any page into<br /><span>clean Markdown.</span></h1>
            <p className="intro-copy">Paste a URL. Distill extracts the useful content and leaves the clutter behind.</p>
          </section>

          <form className="scrape-form" onSubmit={handleSubmit}>
            <label className="input-label" htmlFor="page-url">PAGE URL</label>
            <div className="input-row">
              <span className="url-symbol" aria-hidden="true">↗</span>
              <input
                id="page-url"
                aria-label="Page URL"
                type="url"
                inputMode="url"
                autoComplete="url"
                placeholder="https://example.com/article"
                value={url}
                onChange={(event) => setUrl(event.target.value)}
                required
                aria-describedby={error ? "scrape-error" : "url-hint"}
              />
              <button className="scrape-button" type="submit" disabled={loading || !url.trim()}>
                {loading ? <><span className="spinner" /> Processing</> : <>Distill page <span aria-hidden="true">→</span></>}
              </button>
            </div>
            <div className="form-options">
            <label className="image-option">
              <input
                type="checkbox"
                checked={includeImages}
                onChange={(event) => setIncludeImages(event.target.checked)}
              />
              <span>Include images</span>
            </label>
            <div className="form-footnote" id="url-hint"><span className="shield-icon" aria-hidden="true">◇</span> Public HTTP and HTTPS pages · robots.txt respected</div>
          </div>
          </form>

          {error && <div className="error-banner" role="alert" id="scrape-error"><span aria-hidden="true">!</span>{error}</div>}

          {loading && (
            <section className="loading-panel" aria-live="polite">
              <span className="large-spinner" />
              <div><strong>Distilling page</strong><p>Checking access rules and extracting content…</p></div>
            </section>
          )}

          {result && <ResultPanel result={result} onCopy={copyMarkdown} copied={copied} />}

          {!result && !loading && !error && (
            <section className="empty-state">
              <div className="empty-art" aria-hidden="true">
                <div className="art-page"><span /><span /><span /><span /><span /></div>
                <div className="art-arrow">→</div>
                <div className="art-lines"><i /><i /><i /><i /></div>
              </div>
              <strong>Your extracted page will appear here</strong>
              <p>Content, metadata, and links — ready to use.</p>
            </section>
          )}

          <footer className="page-footer"><span>SAFE BY DEFAULT</span><span>SSRF PROTECTION · SIZE LIMITS · NO TRACKING</span></footer>
        </div>
      </main>
    </div>
  );
}

function ResultPanel({
  result,
  onCopy,
  copied,
}: {
  result: ScrapeResponse;
  onCopy: () => void;
  copied: boolean;
}) {
  return (
    <section className="result-panel" aria-label="Scrape result">
      <div className="result-heading">
        <div className="result-title-wrap">
          <div className="result-kicker"><span className="status-dot" /> EXTRACTION COMPLETE</div>
          <h2>{result.title || "Untitled page"}</h2>
          <a className="result-url" href={result.final_url} target="_blank" rel="noreferrer">{result.final_url}<span aria-hidden="true"> ↗</span></a>
        </div>
        <button className="copy-button" type="button" onClick={onCopy}>{copied ? "Copied ✓" : "Copy Markdown"}</button>
      </div>
      <div className="result-stats">
        <div><span>STATUS</span><strong><i className="status-dot" /> {result.status_code}</strong></div>
        <div><span>LINKS FOUND</span><strong>{result.links.length}</strong></div>
        <div><span>CONTENT HASH</span><strong className="hash-value">{result.content_hash.slice(0, 12)}…</strong></div>
      </div>
      <div className="markdown-pane">
        <div className="pane-toolbar"><span><i /> MARKDOWN PREVIEW</span><span>{result.markdown.length.toLocaleString()} CHARACTERS</span></div>
        <article className="markdown-content"><ReactMarkdown>{result.markdown || "_No extractable text was found on this page._"}</ReactMarkdown></article>
      </div>
      {result.description && <p className="result-description">{result.description}</p>}
      {result.links.length > 0 && (
        <details className="links-details">
          <summary>Extracted links <span>{result.links.length}</span></summary>
          <ul>{result.links.map((link) => <li key={link}><a href={link} target="_blank" rel="noreferrer">{link}</a></li>)}</ul>
        </details>
      )}
    </section>
  );
}
