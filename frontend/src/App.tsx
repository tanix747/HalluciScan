import {
  Activity,
  AlertCircle,
  CheckCircle2,
  ChevronDown,
  CircleAlert,
  ExternalLink,
  FileSearch,
  Loader2,
  RotateCcw,
  SearchCheck,
  Send,
  ShieldCheck,
  XCircle,
} from "lucide-react";
import type { LucideIcon } from "lucide-react";
import { useEffect, useMemo, useState } from "react";
import type { FormEvent } from "react";
//const API_BASE = "https://halluciscan-backend.onrender.com";
type HealthState = "checking" | "online" | "offline";
type AnalysisState = "idle" | "loading" | "success" | "error";
type ClaimStatus = "SUPPORTED" | "CONTRADICTED" | "INSUFFICIENT_EVIDENCE";

type Evidence = {
  title: string;
  url: string;
  content: string;
};

type Claim = {
  text: string;
  status: ClaimStatus;
  confidence: number;
  reason: string;
  evidence: Evidence[];
};

type AnalyzeResponse = {
  request_id: string;
  processing_time_ms: number;
  claims: Claim[];
};

type Summary = {
  total: number;
  supported: number;
  contradicted: number;
  insufficient: number;
};

const sampleText =
  "Linux was invented by Bill Gates in 1998. Python was created by Guido van Rossum and first appeared in 1991.";

const EVIDENCE_SNIPPET_MAX_CHARS = 280;

const statusConfig = {
  SUPPORTED: {
    label: "Supported",
    icon: CheckCircle2,
    badge: "border-emerald-400/50 bg-emerald-400/10 text-emerald-200",
    accent: "text-emerald-300",
    bar: "bg-emerald-400",
  },
  CONTRADICTED: {
    label: "Contradicted",
    icon: XCircle,
    badge: "border-rose-400/50 bg-rose-400/10 text-rose-200",
    accent: "text-rose-300",
    bar: "bg-rose-400",
  },
  INSUFFICIENT_EVIDENCE: {
    label: "Insufficient",
    icon: CircleAlert,
    badge: "border-amber-400/50 bg-amber-400/10 text-amber-200",
    accent: "text-amber-300",
    bar: "bg-amber-300",
  },
} satisfies Record<ClaimStatus, { label: string; icon: LucideIcon; badge: string; accent: string; bar: string }>;

function App() {
  const [health, setHealth] = useState<HealthState>("checking");
  const [text, setText] = useState(sampleText);
  const [analysisState, setAnalysisState] = useState<AnalysisState>("idle");
  const [result, setResult] = useState<AnalyzeResponse | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [progress, setProgress] = useState(0);

  useEffect(() => {
    const controller = new AbortController();

    async function checkHealth() {
      try {
        const response = await fetch("/api/health", {
        signal: controller.signal,
      });
        setHealth(response.ok ? "online" : "offline");
      } catch {
        setHealth("offline");
      }
    }

    void checkHealth();

    return () => controller.abort();
  }, []);

  useEffect(() => {
    if (analysisState !== "loading") {
      setProgress(0);
      return;
    }

    const interval = window.setInterval(() => {
      setProgress((current) => Math.min(current + Math.max(2, (92 - current) * 0.08), 92));
    }, 420);

    return () => window.clearInterval(interval);
  }, [analysisState]);

  const summary = useMemo<Summary>(() => {
    const claims = result?.claims ?? [];

    return {
      total: claims.length,
      supported: claims.filter((claim) => claim.status === "SUPPORTED").length,
      contradicted: claims.filter((claim) => claim.status === "CONTRADICTED").length,
      insufficient: claims.filter((claim) => claim.status === "INSUFFICIENT_EVIDENCE").length,
    };
  }, [result]);

  async function handleAnalyze(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();

    const normalizedText = text.trim();
    if (!normalizedText) {
      setAnalysisState("error");
      setError("Paste a response before running analysis.");
      setResult(null);
      return;
    }

    const controller = new AbortController();
    const timeoutId = window.setTimeout(() => controller.abort(), 120_000);

    setAnalysisState("loading");
    setError(null);
    setResult(null);
    setProgress(8);

    try {
      const response = await fetch("/api/analyze", {
        method: "POST",
        headers: {
        "Content-Type": "application/json",
       },
       body: JSON.stringify({ text: normalizedText }),
       signal: controller.signal,
      });

      if (!response.ok) {
        throw new Error(resolveHttpError(response.status));
      }

      const payload: unknown = await response.json();
      const parsed = parseAnalyzeResponse(payload);

      setProgress(100);
      setResult(parsed);
      setAnalysisState("success");
    } catch (caughtError) {
      setResult(null);
      setAnalysisState("error");
      setError(resolveClientError(caughtError));
    } finally {
      window.clearTimeout(timeoutId);
    }
  }

  const healthStyles = {
    checking: "border-sky-400/40 bg-sky-400/10 text-sky-200",
    online: "border-emerald-400/40 bg-emerald-400/10 text-emerald-200",
    offline: "border-rose-400/40 bg-rose-400/10 text-rose-200",
  }[health];

  const isLoading = analysisState === "loading";

  return (
    <main className="min-h-screen bg-ink text-slate-100">
      <section className="mx-auto flex min-h-screen w-full max-w-7xl flex-col px-4 py-5 sm:px-6 lg:px-8">
        <header className="flex flex-wrap items-center justify-between gap-4 border-b border-line pb-5">
          <div className="flex items-center gap-3">
            <div className="grid size-10 place-items-center rounded-lg border border-signal/40 bg-signal/10">
              <ShieldCheck className="size-5 text-signal" aria-hidden="true" />
            </div>
            <div>
              <p className="text-lg font-semibold tracking-normal">HalluciScan</p>
              <p className="text-sm text-slate-400">Explainable hallucination detection</p>
            </div>
          </div>
          <div className={`flex items-center gap-2 rounded-full border px-3 py-1.5 text-sm ${healthStyles}`}>
            <Activity className="size-4" aria-hidden="true" />
            <span>{health === "checking" ? "Checking API" : `API ${health}`}</span>
          </div>
        </header>

        <div className="grid flex-1 gap-6 py-6 lg:grid-cols-[0.9fr_1.1fr]">
          <section className="space-y-5">
            <div className="space-y-4">
              <div className="inline-flex items-center gap-2 rounded-full border border-signal/30 bg-signal/10 px-3 py-1 text-sm text-signal">
                <SearchCheck className="size-4" aria-hidden="true" />
                Live evidence pipeline
              </div>
              <h1 className="max-w-2xl text-4xl font-semibold leading-tight tracking-normal sm:text-5xl">
                Verify factual claims against evidence.
              </h1>
              <p className="max-w-xl text-base leading-7 text-slate-300">
                Paste an AI-generated response and review each claim with confidence, explanation,
                and source evidence from the backend pipeline.
              </p>
            </div>

            <form onSubmit={handleAnalyze} className="rounded-lg border border-line bg-panel p-4 shadow-glow sm:p-5">
              <div className="flex items-center justify-between gap-3">
                <label htmlFor="analysis-text" className="text-sm font-medium text-slate-200">
                  AI response
                </label>
                <span className="text-xs text-slate-500">{text.trim().length.toLocaleString()} chars</span>
              </div>
              <textarea
                id="analysis-text"
                value={text}
                onChange={(event) => setText(event.target.value)}
                disabled={isLoading}
                className="mt-3 min-h-80 w-full resize-y rounded-lg border border-line bg-ink/80 p-4 text-sm leading-6 text-slate-100 outline-none transition placeholder:text-slate-600 focus:border-signal disabled:cursor-wait disabled:opacity-70"
                placeholder="Paste an AI-generated answer here..."
              />
              <div className="mt-4 flex flex-col gap-3 sm:flex-row">
                <button
                  type="submit"
                  disabled={isLoading}
                  className="flex min-h-11 flex-1 items-center justify-center gap-2 rounded-lg bg-signal px-4 py-3 text-sm font-semibold text-ink transition hover:bg-[#47e8c4] disabled:cursor-wait disabled:opacity-70"
                >
                  {isLoading ? <Loader2 className="size-4 animate-spin" aria-hidden="true" /> : <Send className="size-4" aria-hidden="true" />}
                  {isLoading ? "Analyzing" : "Analyze"}
                </button>
                <button
                  type="button"
                  disabled={isLoading}
                  onClick={() => {
                    setText("");
                    setResult(null);
                    setError(null);
                    setAnalysisState("idle");
                  }}
                  className="flex min-h-11 items-center justify-center gap-2 rounded-lg border border-line px-4 py-3 text-sm font-medium text-slate-200 transition hover:border-slate-500 disabled:cursor-not-allowed disabled:opacity-60"
                >
                  <RotateCcw className="size-4" aria-hidden="true" />
                  Clear
                </button>
              </div>
            </form>
          </section>

          <section className="min-h-[520px] space-y-4">
            {analysisState === "idle" && <EmptyState />}
            {analysisState === "loading" && <LoadingState progress={progress} />}
            {analysisState === "error" && <ErrorState message={error ?? "Analysis failed."} />}
            {analysisState === "success" && result && <Results result={result} summary={summary} />}
          </section>
        </div>
      </section>
    </main>
  );
}

function EmptyState() {
  return (
    <div className="flex h-full min-h-[520px] items-center justify-center rounded-lg border border-line bg-panel/60 p-8">
      <div className="max-w-md text-center">
        <div className="mx-auto grid size-12 place-items-center rounded-lg border border-line bg-ink/70">
          <FileSearch className="size-6 text-signal" aria-hidden="true" />
        </div>
        <h2 className="mt-5 text-xl font-semibold tracking-normal">Analysis results</h2>
        <p className="mt-2 text-sm leading-6 text-slate-400">
          Claim verdicts, confidence, explanations, and source evidence will appear here.
        </p>
      </div>
    </div>
  );
}

function LoadingState({ progress }: { progress: number }) {
  return (
    <div className="flex h-full min-h-[520px] items-center justify-center rounded-lg border border-line bg-panel p-8">
      <div className="w-full max-w-md text-center">
        <Loader2 className="mx-auto size-10 animate-spin text-signal" aria-hidden="true" />
        <h2 className="mt-5 text-xl font-semibold tracking-normal">Running evidence analysis</h2>
        <p className="mt-2 text-sm leading-6 text-slate-400">
          Extracting claims, searching sources, reranking evidence, and verifying verdicts.
        </p>
        <div className="mt-6 h-2 overflow-hidden rounded-full bg-ink">
          <div className="h-full rounded-full bg-signal transition-all duration-500" style={{ width: `${progress}%` }} />
        </div>
        <p className="mt-3 text-sm text-slate-400">{Math.round(progress)}%</p>
      </div>
    </div>
  );
}

function ErrorState({ message }: { message: string }) {
  return (
    <div className="rounded-lg border border-rose-400/30 bg-rose-400/10 p-5">
      <div className="flex gap-3">
        <AlertCircle className="mt-0.5 size-5 shrink-0 text-rose-300" aria-hidden="true" />
        <div>
          <h2 className="text-base font-semibold text-rose-100">Analysis failed</h2>
          <p className="mt-1 text-sm leading-6 text-rose-100/80">{message}</p>
        </div>
      </div>
    </div>
  );
}

function Results({ result, summary }: { result: AnalyzeResponse; summary: Summary }) {
  return (
    <div className="space-y-4">
      <SummaryCard result={result} summary={summary} />
      {result.claims.length === 0 ? (
        <div className="rounded-lg border border-line bg-panel p-6 text-sm text-slate-300">
          No factual claims were extracted from this response.
        </div>
      ) : (
        result.claims.map((claim, index) => <ClaimCard key={`${claim.text}-${index}`} claim={claim} index={index} />)
      )}
    </div>
  );
}

function SummaryCard({ result, summary }: { result: AnalyzeResponse; summary: Summary }) {
  const metrics = [
    { label: "Total", value: summary.total, className: "text-slate-100" },
    { label: "Supported", value: summary.supported, className: "text-emerald-300" },
    { label: "Contradicted", value: summary.contradicted, className: "text-rose-300" },
    { label: "Insufficient", value: summary.insufficient, className: "text-amber-300" },
  ];

  return (
    <section className="rounded-lg border border-line bg-panel p-5">
      <div className="flex flex-wrap items-start justify-between gap-3">
        <div>
          <h2 className="text-lg font-semibold tracking-normal">Summary</h2>
          <p className="mt-1 text-sm text-slate-400">
            Request {result.request_id.slice(0, 8)} - {result.processing_time_ms.toLocaleString()} ms
          </p>
        </div>
      </div>
      <div className="mt-5 grid grid-cols-2 gap-3 sm:grid-cols-4">
        {metrics.map((metric) => (
          <div key={metric.label} className="rounded-lg border border-line bg-ink/60 p-4">
            <p className="text-xs uppercase tracking-[0.12em] text-slate-500">{metric.label}</p>
            <p className={`mt-2 text-2xl font-semibold ${metric.className}`}>{metric.value}</p>
          </div>
        ))}
      </div>
    </section>
  );
}

function ClaimCard({ claim, index }: { claim: Claim; index: number }) {
  const config = statusConfig[claim.status];
  const Icon = config.icon;
  const confidencePercent = Math.round(claim.confidence * 100);

  return (
    <article className="rounded-lg border border-line bg-panel p-5">
      <div className="flex flex-col gap-4 sm:flex-row sm:items-start sm:justify-between">
        <div className="min-w-0 flex-1">
          <p className="text-xs uppercase tracking-[0.12em] text-slate-500">Claim {index + 1}</p>
          <h3 className="mt-2 text-lg font-semibold leading-7 tracking-normal text-slate-100">{claim.text}</h3>
        </div>
        <span className={`inline-flex w-fit items-center gap-2 rounded-full border px-3 py-1.5 text-sm ${config.badge}`}>
          <Icon className="size-4" aria-hidden="true" />
          {config.label}
        </span>
      </div>

      <div className="mt-5 grid gap-4 sm:grid-cols-[160px_1fr]">
        <div className="rounded-lg border border-line bg-ink/60 p-4">
          <p className="text-xs uppercase tracking-[0.12em] text-slate-500">Confidence</p>
          <p className={`mt-2 text-3xl font-semibold ${config.accent}`}>{confidencePercent}%</p>
          <div className="mt-3 h-1.5 overflow-hidden rounded-full bg-slate-800">
            <div className={`h-full rounded-full ${config.bar}`} style={{ width: `${confidencePercent}%` }} />
          </div>
        </div>
        <div className="rounded-lg border border-line bg-ink/60 p-4">
          <p className="text-xs uppercase tracking-[0.12em] text-slate-500">Explanation</p>
          <p className="mt-2 text-sm leading-6 text-slate-300">{claim.reason}</p>
        </div>
      </div>

      <EvidenceList evidence={claim.evidence} />
    </article>
  );
}

function EvidenceList({ evidence }: { evidence: Evidence[] }) {
  const [isOpen, setIsOpen] = useState(true);

  return (
    <section className="mt-4 rounded-lg border border-line bg-ink/40">
      <button
        type="button"
        onClick={() => setIsOpen((current) => !current)}
        className="flex w-full items-center justify-between gap-3 px-4 py-3 text-left text-sm font-medium text-slate-200"
      >
        <span>Evidence ({evidence.length})</span>
        <ChevronDown className={`size-4 transition ${isOpen ? "rotate-180" : ""}`} aria-hidden="true" />
      </button>

      {isOpen && (
        <div className="space-y-3 border-t border-line p-4">
          {evidence.length === 0 ? (
            <p className="text-sm text-slate-400">No evidence was available for this claim.</p>
          ) : (
            evidence.map((item) => (
              <div key={`${item.url}-${item.title}`} className="space-y-3 rounded-lg border border-line bg-panel/70 p-4">
                <div className="min-w-0">
                  <h4 className="break-words text-sm font-semibold leading-6 text-slate-100">
                    {item.title || getPublisherName(item.url)}
                  </h4>
                  <p className="mt-1 text-xs font-medium uppercase tracking-[0.12em] text-slate-500">
                    {getPublisherName(item.url)}
                  </p>
                </div>
                <p className="text-sm leading-6 text-slate-400">{truncateEvidenceSnippet(item.content)}</p>
                <a
                  href={item.url}
                  target="_blank"
                  rel="noopener noreferrer"
                  className="inline-flex w-fit items-center gap-2 text-sm font-medium text-signal transition hover:text-[#47e8c4]"
                >
                  <span>Read Source</span>
                  <ExternalLink className="size-4 shrink-0" aria-hidden="true" />
                </a>
              </div>
            ))
          )}
        </div>
      )}
    </section>
  );
}

function truncateEvidenceSnippet(content: string): string {
  const normalized = content.replace(/\s+/g, " ").trim();

  if (normalized.length <= EVIDENCE_SNIPPET_MAX_CHARS) {
    return normalized;
  }

  const truncated = normalized.slice(0, EVIDENCE_SNIPPET_MAX_CHARS).trimEnd();
  return `${truncated.replace(/[.,;:\s]+$/, "")}...`;
}

function getPublisherName(url: string): string {
  try {
    const hostname = new URL(url).hostname.toLowerCase().replace(/^www\./, "");

    if (hostname.includes("wikipedia.org")) {
      return "Wikipedia";
    }

    if (hostname.includes("britannica.com")) {
      return "Britannica";
    }

    if (hostname.includes("theverge.com")) {
      return "The Verge";
    }

    if (hostname === "bbc.co.uk" || hostname.endsWith(".bbc.co.uk") || hostname.includes("bbc.com")) {
      return "BBC";
    }

    if (hostname.includes("microsoft.com")) {
      return "Microsoft Docs";
    }

    const domainPart = hostname.split(".").at(-2) ?? hostname;
    return domainPart
      .split("-")
      .filter(Boolean)
      .map((part) => part.charAt(0).toUpperCase() + part.slice(1))
      .join(" ");
  } catch {
    return "Source";
  }
}

function parseAnalyzeResponse(payload: unknown): AnalyzeResponse {
  if (!isRecord(payload)) {
    throw new Error("The backend returned an invalid response.");
  }

  const claims = payload.claims;

  if (
    typeof payload.request_id !== "string" ||
    typeof payload.processing_time_ms !== "number" ||
    !Array.isArray(claims)
  ) {
    throw new Error("The backend returned an invalid response.");
  }

  return {
    request_id: payload.request_id,
    processing_time_ms: payload.processing_time_ms,
    claims: claims.map(parseClaim),
  };
}

function parseClaim(value: unknown): Claim {
  if (!isRecord(value) || typeof value.text !== "string" || !isClaimStatus(value.status)) {
    throw new Error("The backend returned an invalid claim response.");
  }

  if (typeof value.confidence !== "number" || typeof value.reason !== "string" || !Array.isArray(value.evidence)) {
    throw new Error("The backend returned an invalid claim response.");
  }

  return {
    text: value.text,
    status: value.status,
    confidence: Math.max(0, Math.min(1, value.confidence)),
    reason: value.reason,
    evidence: value.evidence.map(parseEvidence),
  };
}

function parseEvidence(value: unknown): Evidence {
  if (
    !isRecord(value) ||
    typeof value.title !== "string" ||
    typeof value.url !== "string" ||
    typeof value.content !== "string"
  ) {
    throw new Error("The backend returned invalid evidence.");
  }

  return {
    title: value.title,
    url: value.url,
    content: value.content,
  };
}

function isRecord(value: unknown): value is Record<string, unknown> {
  return typeof value === "object" && value !== null;
}

function isClaimStatus(value: unknown): value is ClaimStatus {
  return value === "SUPPORTED" || value === "CONTRADICTED" || value === "INSUFFICIENT_EVIDENCE";
}

function resolveHttpError(statusCode: number): string {
  if (statusCode === 422) {
    return "The request was rejected. Check that the response text is not empty.";
  }

  if (statusCode === 429) {
    return "The backend is rate limited. Try again in a moment.";
  }

  if (statusCode >= 500) {
    return "The backend could not complete the analysis.";
  }

  return "The analysis request failed.";
}

function resolveClientError(error: unknown): string {
  if (error instanceof DOMException && error.name === "AbortError") {
    return "The analysis timed out before the backend responded.";
  }

  if (error instanceof TypeError) {
    return "The backend is unavailable. Confirm the API server is running.";
  }

  if (error instanceof Error) {
    return error.message;
  }

  return "The analysis request failed.";
}

export default App;
