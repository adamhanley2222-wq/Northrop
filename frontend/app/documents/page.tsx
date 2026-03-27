"use client";

import Link from "next/link";
import { useEffect, useState } from "react";

import { apiFetch } from "@/lib/api";
import { getToken } from "@/lib/auth";

type DocumentItem = {
  id: string;
  title: string;
  document_type: string;
  original_filename: string;
  parse_status: string;
};

export default function DocumentsPage() {
  const [documents, setDocuments] = useState<DocumentItem[]>([]);
  const [error, setError] = useState("");

  useEffect(() => {
    const token = getToken();
    if (!token) {
      setError("Please login first.");
      return;
    }

    apiFetch("/api/documents", token)
      .then(async (response) => {
        if (!response.ok) {
          throw new Error("Unable to load documents");
        }
        return response.json();
      })
      .then((data) => setDocuments(data))
      .catch((err: Error) => setError(err.message));
  }, []);

  return (
    <main className="mx-auto max-w-5xl px-6 py-12">
      <div className="flex items-center justify-between">
        <h1 className="text-2xl font-semibold">Documents</h1>
        <Link className="rounded bg-slate-900 px-4 py-2 text-white" href="/upload">Upload</Link>
      </div>
      {error ? <p className="mt-3 text-red-700">{error}</p> : null}
      <ul className="mt-6 space-y-3">
        {documents.map((doc) => (
          <li className="rounded border bg-white p-4" key={doc.id}>
            <Link href={`/documents/${doc.id}`}>
              <p className="font-medium">{doc.title}</p>
              <p className="text-sm text-slate-600">{doc.original_filename} · {doc.document_type} · {doc.parse_status}</p>
            </Link>
          </li>
        ))}
      </ul>
    </main>
  );
}
