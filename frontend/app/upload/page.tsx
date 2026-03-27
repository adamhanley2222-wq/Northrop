"use client";

import { FormEvent, useState } from "react";

import { apiFetch } from "@/lib/api";
import { getToken } from "@/lib/auth";

export default function UploadPage() {
  const [title, setTitle] = useState("");
  const [documentType, setDocumentType] = useState("quarterly_report");
  const [file, setFile] = useState<File | null>(null);
  const [message, setMessage] = useState("");

  async function onSubmit(event: FormEvent) {
    event.preventDefault();
    setMessage("");

    const token = getToken();
    if (!token) {
      setMessage("Please login first.");
      return;
    }

    if (!file) {
      setMessage("Please select a file.");
      return;
    }

    const formData = new FormData();
    formData.append("title", title);
    formData.append("document_type", documentType);
    formData.append("file", file);

    const response = await apiFetch("/api/documents/upload", token, {
      method: "POST",
      body: formData,
    });

    if (!response.ok) {
      setMessage("Upload failed.");
      return;
    }

    const data = await response.json();
    setMessage(`Uploaded ${data.title} (${data.parse_status})`);
  }

  return (
    <main className="mx-auto max-w-xl px-6 py-12">
      <h1 className="text-2xl font-semibold">Upload document</h1>
      <form className="mt-6 space-y-3" onSubmit={onSubmit}>
        <input className="w-full rounded border p-2" placeholder="Document title" value={title} onChange={(e) => setTitle(e.target.value)} />
        <select className="w-full rounded border p-2" value={documentType} onChange={(e) => setDocumentType(e.target.value)}>
          <option value="annual_strategy">Annual strategy</option>
          <option value="quarterly_report">Quarterly report</option>
          <option value="supporting_doc">Supporting doc</option>
        </select>
        <input accept=".pdf,.docx" className="w-full rounded border p-2" type="file" onChange={(e) => setFile(e.target.files?.[0] ?? null)} />
        <button className="rounded bg-slate-900 px-4 py-2 text-white" type="submit">Upload</button>
      </form>
      {message ? <p className="mt-4 text-sm text-slate-700">{message}</p> : null}
    </main>
  );
}
