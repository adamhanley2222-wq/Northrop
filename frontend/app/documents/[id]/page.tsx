"use client";

import { useParams } from "next/navigation";
import { useEffect, useState } from "react";

import { apiFetch } from "@/lib/api";
import { getToken } from "@/lib/auth";

type DocumentDetail = {
  id: string;
  title: string;
  parse_status: string;
  original_filename: string;
};

type Section = {
  id: string;
  heading: string;
  section_order: number;
  raw_text: string;
  page_start?: number | null;
  page_end?: number | null;
};

type Chunk = {
  id: string;
  chunk_order: number;
  text: string;
  structural_path: string;
  metadata_json: Record<string, unknown>;
  page_ref_start?: number | null;
  page_ref_end?: number | null;
  published: boolean;
};

export default function DocumentDetailPage() {
  const params = useParams<{ id: string }>();
  const [detail, setDetail] = useState<DocumentDetail | null>(null);
  const [sections, setSections] = useState<Section[]>([]);
  const [chunks, setChunks] = useState<Chunk[]>([]);
  const [metadataDrafts, setMetadataDrafts] = useState<Record<string, string>>({});
  const [statusMessage, setStatusMessage] = useState("");
  const [error, setError] = useState("");

  async function loadAll() {
    const token = getToken();
    if (!token) {
      setError("Please login first.");
      return;
    }

    const [docResponse, sectionsResponse, chunksResponse] = await Promise.all([
      apiFetch(`/api/documents/${params.id}`, token),
      apiFetch(`/api/documents/${params.id}/sections`, token),
      apiFetch(`/api/documents/${params.id}/chunks`, token),
    ]);

    if (!docResponse.ok || !sectionsResponse.ok || !chunksResponse.ok) {
      setError("Unable to load document details");
      return;
    }

    const [docData, sectionData, chunkData] = await Promise.all([
      docResponse.json(),
      sectionsResponse.json(),
      chunksResponse.json(),
    ]);

    setDetail(docData);
    setSections(sectionData);
    setChunks(chunkData);

    const drafts: Record<string, string> = {};
    for (const chunk of chunkData) {
      drafts[chunk.id] = JSON.stringify(chunk.metadata_json, null, 2);
    }
    setMetadataDrafts(drafts);
  }

  useEffect(() => {
    loadAll().catch((err: Error) => setError(err.message));
  }, [params.id]);

  async function reparseDocument() {
    const token = getToken();
    if (!token) {
      return;
    }
    setStatusMessage("Reparsing...");
    const response = await apiFetch(`/api/documents/${params.id}/reparse`, token, { method: "POST" });
    if (!response.ok) {
      setStatusMessage("Reparse failed");
      return;
    }
    setStatusMessage("Reparse complete");
    await loadAll();
  }

  async function publishDocument() {
    const token = getToken();
    if (!token) {
      return;
    }
    setStatusMessage("Publishing...");
    const response = await apiFetch(`/api/documents/${params.id}/publish`, token, { method: "POST" });
    if (!response.ok) {
      setStatusMessage("Publish failed");
      return;
    }
    setStatusMessage("Publish complete");
    await loadAll();
  }

  async function saveChunkMetadata(chunkId: string) {
    const token = getToken();
    if (!token) {
      return;
    }

    const raw = metadataDrafts[chunkId] ?? "{}";
    let parsed: Record<string, unknown>;

    try {
      parsed = JSON.parse(raw);
    } catch {
      setStatusMessage("Metadata must be valid JSON.");
      return;
    }

    const response = await apiFetch(`/api/chunks/${chunkId}/metadata`, token, {
      method: "PATCH",
      body: JSON.stringify({ metadata_json: parsed }),
    });

    if (!response.ok) {
      setStatusMessage(`Failed to save metadata for chunk ${chunkId}`);
      return;
    }

    setStatusMessage(`Saved metadata for chunk ${chunkId}`);
    await loadAll();
  }

  return (
    <main className="mx-auto max-w-6xl px-6 py-12">
      {error ? <p className="text-red-700">{error}</p> : null}
      {statusMessage ? <p className="mb-4 rounded border bg-amber-50 p-3 text-amber-800">{statusMessage}</p> : null}

      {detail ? (
        <>
          <div className="flex flex-wrap items-center justify-between gap-3">
            <div>
              <h1 className="text-2xl font-semibold">{detail.title}</h1>
              <p className="mt-1 text-slate-600">{detail.original_filename} · status: {detail.parse_status}</p>
            </div>
            <div className="flex gap-2">
              <button className="rounded border px-3 py-2" onClick={reparseDocument} type="button">Reparse</button>
              <button className="rounded bg-slate-900 px-3 py-2 text-white" onClick={publishDocument} type="button">Publish</button>
            </div>
          </div>

          <h2 className="mt-8 text-lg font-medium">Sections ({sections.length})</h2>
          <div className="mt-3 space-y-3">
            {sections.map((section) => (
              <article className="rounded border bg-white p-4" key={section.id}>
                <h3 className="font-medium">{section.section_order}. {section.heading}</h3>
                <p className="text-xs text-slate-500">
                  pages: {section.page_start ?? "-"} to {section.page_end ?? "-"}
                </p>
                <p className="mt-2 whitespace-pre-wrap text-sm text-slate-700">{section.raw_text.slice(0, 1200)}</p>
              </article>
            ))}
          </div>

          <h2 className="mt-8 text-lg font-medium">Chunks ({chunks.length})</h2>
          <div className="mt-3 space-y-4">
            {chunks.map((chunk) => (
              <article className="rounded border bg-white p-4" key={chunk.id}>
                <p className="text-sm font-medium">Chunk {chunk.chunk_order} · {chunk.structural_path}</p>
                <p className="text-xs text-slate-500">
                  pages: {chunk.page_ref_start ?? "-"} to {chunk.page_ref_end ?? "-"} · published: {chunk.published ? "yes" : "no"}
                </p>
                <p className="mt-2 whitespace-pre-wrap text-sm text-slate-700">{chunk.text}</p>
                <label className="mt-3 block text-xs font-medium text-slate-700">Metadata JSON</label>
                <textarea
                  className="mt-1 w-full rounded border p-2 font-mono text-xs"
                  rows={6}
                  value={metadataDrafts[chunk.id] ?? "{}"}
                  onChange={(event) => {
                    setMetadataDrafts((prev) => ({ ...prev, [chunk.id]: event.target.value }));
                  }}
                />
                <button className="mt-2 rounded border px-3 py-1 text-sm" onClick={() => saveChunkMetadata(chunk.id)} type="button">
                  Save metadata
                </button>
              </article>
            ))}
          </div>
        </>
      ) : null}
    </main>
  );
}
