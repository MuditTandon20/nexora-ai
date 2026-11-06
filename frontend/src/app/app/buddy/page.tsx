"use client";
import { useEffect, useState } from "react";
import { Send, Sparkles } from "lucide-react";
import { api, post } from "@/lib/api";
import { ErrorMessage, PageHeading } from "@/components/workspace";
import type { Material } from "../notes/page";
type Reply = {
  answer: string;
  source_quote: string;
  follow_up: string;
  insufficient_context: boolean;
};
export default function Buddy() {
  const [materials, setMaterials] = useState<Material[]>([]);
  const [materialId, setMaterialId] = useState("");
  const [language, setLanguage] = useState("en");
  const [configured, setConfigured] = useState(false);
  const [limit, setLimit] = useState(20);
  const [messages, setMessages] = useState<
    { question: string; reply: Reply }[]
  >([]);
  const [question, setQuestion] = useState("");
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState("");
  useEffect(() => {
    Promise.all([
      api<Material[]>("/materials"),
      api<{ configured: boolean; daily_limit: number }>("/ai/status"),
    ])
      .then(([m, s]) => {
        setMaterials(m.filter((x) => x.approved));
        setConfigured(s.configured);
        setLimit(s.daily_limit);
      })
      .catch((e) => setError(e.message));
  }, []);
  return (
    <>
      <PageHeading
        eyebrow="CURIOSITY HAS A COMPANION"
        title="Let’s figure it out, together."
        description="Choose a chapter. Ask a question. Take one small step toward understanding."
      />
      <div className="buddy-grid">
        <aside className="panel buddy-config">
          <h2>Your learning space</h2>
          <label>
            Approved chapter
            <select
              value={materialId}
              onChange={(e) => {
                setMaterialId(e.target.value);
                setMessages([]);
                setError("");
              }}
              disabled={busy}
            >
              <option value="">Choose a chapter</option>
              {materials.map((m) => (
                <option key={m.id} value={m.id}>
                  {m.title}
                </option>
              ))}
            </select>
          </label>
          <label>
            Explain in
            <select
              value={language}
              onChange={(e) => setLanguage(e.target.value)}
              disabled={busy}
            >
              <option value="en">English</option>
              <option value="hi">हिन्दी · Hindi</option>
            </select>
          </label>
          <p className="buddy-hint">
            A study companion grounded in your approved chapter. It can make
            mistakes: check the quoted source and ask your teacher when unsure.
            <br />
            <br />
            Up to {limit} AI requests per day. Your conversation is kept only in
            this page’s memory.
          </p>
        </aside>
        <section className="panel buddy-chat">
          <header className="buddy-chat-header">
            <span className="icon-tile lilac">
              <Sparkles size={21} />
            </span>
            <div>
              <strong>Nexora Study Buddy</strong>
              <small>A little help for your next aha! moment.</small>
            </div>
          </header>
          <div className="chat-messages" aria-live="polite">
            {!messages.length && (
              <div className="chat-welcome">
                <span>✳</span>
                <h2>
                  Big questions.
                  <br />
                  Small, thoughtful steps.
                </h2>
                <p>
                  {configured
                    ? "Pick your chapter and tell me what you’re curious about."
                    : "Your school has not connected an AI provider yet. Approved notes and Arena challenges are still available."}
                </p>
              </div>
            )}
            {messages.map((m, i) => (
              <div key={i}>
                <div className="message question">{m.question}</div>
                <div className="message answer">
                  <p>{m.reply.answer}</p>
                  {m.reply.source_quote && (
                    <blockquote className="source-quote">
                      From your chapter: “{m.reply.source_quote}”
                    </blockquote>
                  )}
                  {m.reply.insufficient_context && (
                    <span className="badge amber">
                      More chapter context needed
                    </span>
                  )}
                  <div className="follow-up">{m.reply.follow_up}</div>
                </div>
              </div>
            ))}
            {busy && (
              <p className="subtle" role="status">
                Looking through your chapter…
              </p>
            )}
            <ErrorMessage error={error} />
          </div>
          <form
            className="chat-input"
            onSubmit={async (e) => {
              e.preventDefault();
              setBusy(true);
              setError("");
              try {
                const reply = await post<Reply>("/ai/tutor", {
                  material_id: Number(materialId),
                  language,
                  question,
                });
                setMessages((prev) => [...prev, { question, reply }]);
                setQuestion("");
              } catch (e) {
                setError((e as Error).message);
              } finally {
                setBusy(false);
              }
            }}
          >
            <label>
              <span className="sr-only">Your chapter question</span>
              <textarea
                value={question}
                onChange={(e) => setQuestion(e.target.value)}
                placeholder="What would you like to understand?"
                rows={2}
                minLength={3}
                maxLength={1000}
                required
                disabled={busy || !configured}
              />
            </label>
            <button
              className="button"
              disabled={
                busy || !materialId || !configured || question.trim().length < 3
              }
              aria-label="Ask Study Buddy"
            >
              <Send size={17} />
            </button>
          </form>
          <p className="chat-privacy">
            Keep questions about your chapter. Please don’t share personal
            details.
          </p>
        </section>
      </div>
    </>
  );
}
