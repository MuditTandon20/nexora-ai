"use client";
import { useState } from "react";
import Link from "next/link";
import { useRouter } from "next/navigation";
import { ArrowRight, BookOpen, LockKeyhole } from "lucide-react";
import { post, setCsrf } from "@/lib/api";

export default function Login() {
  const router = useRouter();
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [error, setError] = useState("");
  const [busy, setBusy] = useState(false);
  return (
    <main className="login-page">
      <section className="login-story">
        <Link href="/" className="brand light">
          <span className="brand-icon">
            N<span>✦</span>
          </span>
          nexora
        </Link>
        <div>
          <BookOpen size={42} />
          <h1>
            Great teaching
            <br />
            starts with
            <br />
            <em>a little space.</em>
          </h1>
          <p>
            Let’s make room for the moments
            <br />
            that make a difference.
          </p>
        </div>
        <small>LESS ADMIN. MORE TEACHING. BETTER LEARNING.</small>
      </section>
      <section className="login-form">
        <div>
          <span className="eyebrow">YOUR SCHOOL WORKSPACE</span>
          <h2>Good to see you.</h2>
          <p>Sign in with your school-issued account.</p>
          <form
            onSubmit={async (e) => {
              e.preventDefault();
              setBusy(true);
              setError("");
              try {
                const result = await post<{ csrf_token: string }>(
                  "/auth/login",
                  { email, password },
                );
                setCsrf(result.csrf_token);
                router.push("/app");
              } catch (e) {
                setError((e as Error).message);
              } finally {
                setBusy(false);
              }
            }}
          >
            <label>
              School email
              <input
                type="email"
                autoComplete="username"
                value={email}
                onChange={(e) => setEmail(e.target.value)}
                placeholder="you@school.edu.in"
                required
              />
            </label>
            <label>
              Password
              <input
                type="password"
                autoComplete="current-password"
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                placeholder="Your password"
                required
              />
            </label>
            {error && (
              <div className="alert" role="alert">
                {error}
              </div>
            )}
            <button disabled={busy} className="button full">
              {busy ? "Signing in…" : "Sign in to Nexora"}
              <ArrowRight size={17} />
            </button>
          </form>
          <div className="privacy-note">
            <LockKeyhole size={16} /> A private space for your school community.
          </div>
          <details className="demo-details">
            <summary>Running the local demo?</summary>
            <p>
              After seeding, use admin@nexora.demo, teacher@nexora.demo, or
              student@nexora.demo. Password: <code>NexoraDemo!2026</code>.
              Synthetic data only.
            </p>
          </details>
        </div>
      </section>
    </main>
  );
}
