"use client";

import { FormEvent, useState } from "react";

import { apiFetch } from "@/lib/api";
import { getToken } from "@/lib/auth";

type QueryResult = {
  session_id: string;
  query_record_id: string;
  intent: string;
  direct_answer: string;
  source_backed_statements: string[];
  inferred_observations: string[];
  key_evidence: Array<{ chunk_id: string; document_title: string; quote: string; metadata: Record<string, unknown> }>;
  comparison_view?: Record<string, unknown> | null;
  gaps: string[];
  executive_questions: string[];
  sources: Array<{ document_title: string; chunk_id: string; page_ref_start?: number | null; page_ref_end?: number | null }>;
  debug?: Record<string, unknown> | null;
};

const feedbackOptions = ["helpful", "incomplete", "incorrect", "needs_more_evidence", "needs_more_challenge"] as const;

export default function QueryPage() {
  const [question, setQuestion] = useState("");
  const [result, setResult] = useState<QueryResult | null>(null);
  const [sessionId, setSessionId] = useState<string | null>(null);
  const [status, setStatus] = useState("");

  async function onSubmit(event: FormEvent) {
    event.preventDefault();
    const token = getToken();
    if (!token) {
      setStatus("Please login first.");
      return;
    }

    setStatus("Running query...");
    const response = await apiFetch("/api/query", token, {
      method: "POST",
      body: JSON.stringify({ question, session_id: sessionId, filters: {} }),
    });

    if (!response.ok) {
      setStatus("Query failed.");
      return;
    }

    const data = await response.json();
    setResult(data);
    setSessionId(data.session_id);
    setStatus("Query complete.");
  }

  async function submitFeedback(feedbackType: (typeof feedbackOptions)[number]) {
    const token = getToken();
    if (!token || !result) {
      return;
    }

    const response = await apiFetch("/api/query/feedback", token, {
      method: "POST",
      body: JSON.stringify({ query_record_id: result.query_record_id, feedback_type: feedbackType }),
    });

    if (!response.ok) {
      setStatus("Failed to submit feedback.");
      return;
    }

    setStatus(`Feedback submitted: ${feedbackType}`);
  }

  return (
    <main className="mx-auto max-w-5xl px-6 py-12">
      <h1 className="text-2xl font-semibold">Executive query</h1>
      <form className="mt-5 flex gap-2" onSubmit={onSubmit}>
        <input className="flex-1 rounded border p-2" value={question} onChange={(e) => setQuestion(e.target.value)} placeholder="Ask a strategy or performance question" />
        <button className="rounded bg-slate-900 px-4 py-2 text-white" type="submit">Ask</button>
      </form>
      {status ? <p className="mt-3 text-sm text-slate-700">{status}</p> : null}

      {result ? (
        <section className="mt-8 space-y-6">
          <div className="rounded border bg-white p-4">
            <h2 className="text-lg font-medium">Direct answer</h2>
            <p className="mt-2 text-sm">{result.direct_answer}</p>
            <p className="mt-2 text-xs text-slate-500">Intent: {result.intent}</p>
          </div>

          <div className="rounded border bg-white p-4">
            <h2 className="text-lg font-medium">Key evidence</h2>
            <ul className="mt-2 list-disc space-y-2 pl-5 text-sm">
              {result.key_evidence.map((item) => (
                <li key={item.chunk_id}>
                  <p className="font-medium">{item.document_title}</p>
                  <p>{item.quote}</p>
                </li>
              ))}
            </ul>
          </div>

          <div className="rounded border bg-white p-4">
            <h2 className="text-lg font-medium">Source-backed statements</h2>
            <ul className="mt-2 list-disc space-y-1 pl-5 text-sm">
              {result.source_backed_statements.map((statement, idx) => (
                <li key={idx}>{statement}</li>
              ))}
            </ul>
          </div>

          <div className="rounded border bg-white p-4">
            <h2 className="text-lg font-medium">Inferred observations</h2>
            <ul className="mt-2 list-disc space-y-1 pl-5 text-sm">
              {result.inferred_observations.map((item, idx) => (
                <li key={idx}>{item}</li>
              ))}
            </ul>
          </div>

          <div className="rounded border bg-white p-4">
            <h2 className="text-lg font-medium">Gaps</h2>
            <ul className="mt-2 list-disc space-y-1 pl-5 text-sm">
              {result.gaps.map((gap, idx) => (
                <li key={idx}>{gap}</li>
              ))}
            </ul>
          </div>

          <div className="rounded border bg-white p-4">
            <h2 className="text-lg font-medium">Executive follow-up questions</h2>
            <ul className="mt-2 list-disc space-y-1 pl-5 text-sm">
              {result.executive_questions.map((item, idx) => (
                <li key={idx}>{item}</li>
              ))}
            </ul>
          </div>

          <div className="rounded border bg-white p-4">
            <h2 className="text-lg font-medium">Sources</h2>
            <ul className="mt-2 list-disc space-y-1 pl-5 text-sm">
              {result.sources.map((source, idx) => (
                <li key={idx}>
                  {source.document_title} · chunk {source.chunk_id} · pages {source.page_ref_start ?? "-"}-{source.page_ref_end ?? "-"}
                </li>
              ))}
            </ul>
          </div>

          <div className="rounded border bg-white p-4">
            <h2 className="text-lg font-medium">Feedback</h2>
            <div className="mt-3 flex flex-wrap gap-2">
              {feedbackOptions.map((option) => (
                <button className="rounded border px-3 py-1 text-sm" key={option} onClick={() => submitFeedback(option)} type="button">
                  {option}
                </button>
              ))}
            </div>
          </div>

          <div className="rounded border bg-white p-4">
            <h2 className="text-lg font-medium">Debug context</h2>
            <pre className="mt-2 overflow-auto rounded bg-slate-50 p-3 text-xs">
              {JSON.stringify(result.debug ?? {}, null, 2)}
            </pre>
          </div>
        </section>
      ) : null}
    </main>
  );
}
