"use client";

import { FormEvent, useState } from "react";
import { useRouter } from "next/navigation";

import { apiUrl } from "@/lib/api";
import { setToken } from "@/lib/auth";

export default function LoginPage() {
  const router = useRouter();
  const [email, setEmail] = useState("admin@example.com");
  const [password, setPassword] = useState("admin1234");
  const [error, setError] = useState("");

  async function onSubmit(event: FormEvent) {
    event.preventDefault();
    setError("");

    const response = await fetch(apiUrl("/api/auth/login"), {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ email, password }),
    });

    if (!response.ok) {
      setError("Login failed. Check credentials.");
      return;
    }

    const data = await response.json();
    setToken(data.access_token);
    router.push("/documents");
  }

  return (
    <main className="mx-auto max-w-md px-6 py-12">
      <h1 className="text-2xl font-semibold">Admin Login</h1>
      <form className="mt-6 space-y-4" onSubmit={onSubmit}>
        <input className="w-full rounded border p-2" value={email} onChange={(e) => setEmail(e.target.value)} />
        <input className="w-full rounded border p-2" type="password" value={password} onChange={(e) => setPassword(e.target.value)} />
        <button className="rounded bg-slate-900 px-4 py-2 text-white" type="submit">Sign in</button>
      </form>
      {error ? <p className="mt-3 text-sm text-red-700">{error}</p> : null}
      <p className="mt-4 text-xs text-slate-600">Dev default: admin@example.com / admin1234</p>
    </main>
  );
}
