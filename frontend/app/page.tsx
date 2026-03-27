import Link from "next/link";

export default function HomePage() {
  return (
    <main className="mx-auto max-w-4xl px-6 py-12">
      <h1 className="text-3xl font-semibold">MD Strategic Review AI</h1>
      <p className="mt-2 text-slate-700">Phase 1 complete scaffold with working auth + document flow.</p>
      <div className="mt-6 grid gap-3 sm:grid-cols-2">
        <Link className="rounded border bg-white p-4" href="/login">Login</Link>
        <Link className="rounded border bg-white p-4" href="/documents">Documents</Link>
        <Link className="rounded border bg-white p-4" href="/upload">Upload</Link>
        <Link className="rounded border bg-white p-4" href="/query">Query</Link>
      </div>
    </main>
  );
}
