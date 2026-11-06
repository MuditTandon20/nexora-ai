"use client";
import { useEffect, useState } from "react";
import { BookOpen, Check, Save, Sparkles } from "lucide-react";
import { api, post } from "@/lib/api";
import {
  Empty,
  ErrorMessage,
  PageHeading,
  useWorkspace,
} from "@/components/workspace";
import type { Material } from "../notes/page";
type Question = {
  id?: number;
  kind: "mcq" | "short_answer";
  question: string;
  options: string[];
  answer: string;
  explanation: string;
  source_quote: string;
  topic: string;
};
type Pack = {
  id: number;
  title: string;
  summary: string;
  published: boolean;
  questions: Question[];
  flashcards: { front: string; back: string }[];
};
type QuizSummary = {
  id: number;
  title: string;
  published: boolean;
  class_id: number;
  model: string;
  prompt_version: string;
  language: string;
};
export default function Studio() {
  const { user, classes, notice } = useWorkspace();
  const [materials, setMaterials] = useState<Material[]>([]);
  const [quizzes, setQuizzes] = useState<QuizSummary[]>([]);
  const [materialId, setMaterialId] = useState("");
  const [language, setLanguage] = useState("en");
  const [configured, setConfigured] = useState(false);
  const [statusLoaded, setStatusLoaded] = useState(false);
  const [pack, setPack] = useState<Pack | null>(null);
  const [error, setError] = useState("");
  const [busy, setBusy] = useState(false);
  const [dirty, setDirty] = useState(false);
  const load = async () => {
    const [m, q, s] = await Promise.all([
      api<Material[]>("/materials"),
      api<QuizSummary[]>("/quizzes"),
      api<{ configured: boolean }>("/ai/status"),
    ]);
    setMaterials(m.filter((x) => x.approved));
    setQuizzes(q);
    setConfigured(s.configured);
    setStatusLoaded(true);
  };
  useEffect(() => {
    if (user.role !== "student") load().catch((e) => setError(e.message));
  }, [user.role]);
  const updateQuestion = (
    index: number,
    key: keyof Question,
    value: unknown,
  ) => {
    setPack((prev) =>
      prev
        ? {
            ...prev,
            questions: prev.questions.map((q, i) =>
              i === index ? { ...q, [key]: value } : q,
            ),
          }
        : null,
    );
    setDirty(true);
  };
  const save = async () => {
    if (!pack) return;
    await api(`/quizzes/${pack.id}`, {
      method: "PUT",
      body: JSON.stringify(pack),
    });
    setDirty(false);
    await load();
  };
  if (user.role === "student")
    return (
      <Empty
        title="A space for teachers"
        description="Published learning packs are available in Nexora Arena."
      />
    );
  return (
    <>
      <PageHeading
        eyebrow="A LITTLE HELP. A LOT OF POSSIBILITY."
        title="Your AI learning studio."
        description="Turn approved chapter content into a reusable learning pack. Review every question before publishing."
      />
      <div className="ai-intro">
        <span className="icon-tile">
          <Sparkles size={26} />
        </span>
        <p>
          Chapter-grounded questions, a short summary, and flashcards.
          <br />
          <strong>
            You make the final call. AI drafts stay private until you approve
            them.
          </strong>
        </p>
      </div>
      {statusLoaded && !configured && (
        <div className="alert">
          AI is not connected. Configure an approved provider on the backend to
          generate packs. You can explore the teacher-authored demo pack in
          Arena.
        </div>
      )}
      <ErrorMessage error={error} />
      <section className="panel ai-config">
        <form
          onSubmit={async (e) => {
            e.preventDefault();
            setBusy(true);
            setError("");
            try {
              const q = await post<{ id: number }>("/ai/generate", {
                material_id: Number(materialId),
                language,
              });
              setPack(await api<Pack>(`/quizzes/${q.id}`));
              setDirty(false);
              await load();
              notice(
                "Draft ready. Please check the facts and language before publishing.",
              );
            } catch (e) {
              setError((e as Error).message);
            } finally {
              setBusy(false);
            }
          }}
        >
          <div className="form-row">
            <label>
              Approved chapter
              <select
                value={materialId}
                onChange={(e) => setMaterialId(e.target.value)}
                required
              >
                <option value="">Select your source material</option>
                {materials.map((m) => (
                  <option value={m.id} key={m.id}>
                    {m.title}
                  </option>
                ))}
              </select>
            </label>
            <label>
              Language
              <select
                value={language}
                onChange={(e) => setLanguage(e.target.value)}
              >
                <option value="en">English</option>
                <option value="hi">हिन्दी · Hindi</option>
              </select>
            </label>
          </div>
          <button
            className="button mt"
            disabled={busy || !configured || !materialId}
          >
            <Sparkles size={16} />
            {busy ? "Building a thoughtful draft…" : "Generate learning pack"}
          </button>
        </form>
      </section>
      {pack && (
        <section className="panel pack-editor">
          <div className="section-heading">
            <div>
              <span className="eyebrow">
                {pack.published ? "PUBLISHED LEARNING PACK" : "TEACHER REVIEW"}
              </span>
              <h2>{pack.title}</h2>
            </div>
            <button
              className="text-link"
              onClick={() => {
                setPack(null);
                setDirty(false);
              }}
            >
              Close
            </button>
          </div>
          {pack.published && (
            <p className="subtle">
              This published version is frozen so practice results stay
              reproducible.
            </p>
          )}
          <fieldset disabled={pack.published || busy}>
            <label>
              Pack title
              <input
                value={pack.title}
                maxLength={160}
                onChange={(e) => {
                  setPack({ ...pack, title: e.target.value });
                  setDirty(true);
                }}
              />
            </label>
            <label>
              Chapter summary
              <textarea
                value={pack.summary}
                rows={4}
                maxLength={5000}
                onChange={(e) => {
                  setPack({ ...pack, summary: e.target.value });
                  setDirty(true);
                }}
              />
            </label>
            <h2>Questions & supporting evidence</h2>
            {pack.questions.map((q, i) => (
              <div className="question-editor" key={i}>
                <span className="badge lilac">
                  Question {i + 1} ·{" "}
                  {q.kind === "mcq" ? "Multiple choice" : "Short answer"}
                </span>
                <label>
                  Question
                  <textarea
                    value={q.question}
                    maxLength={1000}
                    onChange={(e) =>
                      updateQuestion(i, "question", e.target.value)
                    }
                  />
                </label>
                {q.kind === "mcq" && (
                  <div className="editor-options">
                    {q.options.map((option, j) => (
                      <label key={j}>
                        Option {String.fromCharCode(65 + j)}
                        <input
                          value={option}
                          onChange={(e) =>
                            updateQuestion(
                              i,
                              "options",
                              q.options.map((o, k) =>
                                k === j ? e.target.value : o,
                              ),
                            )
                          }
                        />
                      </label>
                    ))}
                  </div>
                )}
                <label>
                  Correct answer
                  {q.kind === "mcq" ? (
                    <select
                      value={q.answer}
                      onChange={(e) =>
                        updateQuestion(i, "answer", e.target.value)
                      }
                    >
                      {q.options.map((o, j) => (
                        <option key={j} value={o}>
                          {o}
                        </option>
                      ))}
                    </select>
                  ) : (
                    <textarea
                      value={q.answer}
                      onChange={(e) =>
                        updateQuestion(i, "answer", e.target.value)
                      }
                    />
                  )}
                </label>
                <label>
                  Explanation
                  <textarea
                    value={q.explanation}
                    onChange={(e) =>
                      updateQuestion(i, "explanation", e.target.value)
                    }
                  />
                </label>
                <label>
                  Topic
                  <input
                    value={q.topic}
                    maxLength={100}
                    onChange={(e) => updateQuestion(i, "topic", e.target.value)}
                  />
                </label>
                <label>
                  Exact supporting quote from the chapter
                  <textarea
                    value={q.source_quote}
                    onChange={(e) =>
                      updateQuestion(i, "source_quote", e.target.value)
                    }
                  />
                </label>
              </div>
            ))}
            <h2>Flashcards</h2>
            {pack.flashcards.map((card, i) => (
              <div className="question-editor" key={i}>
                <label>
                  Front
                  <input
                    value={card.front}
                    onChange={(e) => {
                      setPack({
                        ...pack,
                        flashcards: pack.flashcards.map((c, j) =>
                          j === i ? { ...c, front: e.target.value } : c,
                        ),
                      });
                      setDirty(true);
                    }}
                  />
                </label>
                <label>
                  Back
                  <textarea
                    value={card.back}
                    onChange={(e) => {
                      setPack({
                        ...pack,
                        flashcards: pack.flashcards.map((c, j) =>
                          j === i ? { ...c, back: e.target.value } : c,
                        ),
                      });
                      setDirty(true);
                    }}
                  />
                </label>
              </div>
            ))}
          </fieldset>
          {!pack.published && (
            <div className="panel-footer">
              <button
                className="button secondary"
                disabled={busy || !dirty}
                onClick={async () => {
                  setBusy(true);
                  setError("");
                  try {
                    await save();
                    notice("Your edits are saved.");
                  } catch (e) {
                    setError((e as Error).message);
                  } finally {
                    setBusy(false);
                  }
                }}
              >
                <Save size={16} />
                Save edits
              </button>
              <button
                className="button"
                disabled={busy}
                onClick={async () => {
                  setBusy(true);
                  setError("");
                  try {
                    await save();
                    await post(`/quizzes/${pack.id}/publish`);
                    setPack({ ...pack, published: true });
                    await load();
                    notice(
                      "Learning pack approved and published to your class.",
                    );
                  } catch (e) {
                    setError((e as Error).message);
                  } finally {
                    setBusy(false);
                  }
                }}
              >
                <Check size={16} />
                Approve & publish
              </button>
            </div>
          )}
          <ErrorMessage error={error} />
        </section>
      )}
      <section className="panel quiz-pack-list">
        <div className="section-heading">
          <h2>Your reusable learning packs</h2>
          <BookOpen size={19} />
        </div>
        {quizzes.map((q) => (
          <div className="quiz-pack-row" key={q.id}>
            <span className="icon-tile lilac">
              <Sparkles size={18} />
            </span>
            <div>
              <h3>{q.title}</h3>
              <p>
                {classes.find((c) => c.id === q.class_id)?.name} ·{" "}
                {q.language === "hi" ? "Hindi" : "English"} · {q.model} ·{" "}
                {q.prompt_version}
              </p>
            </div>
            <span className={`badge ${q.published ? "green" : "amber"}`}>
              {q.published ? "Published" : "Draft"}
            </span>
            <button
              className="button secondary compact"
              disabled={busy}
              onClick={async () => {
                setError("");
                try {
                  setPack(await api<Pack>(`/quizzes/${q.id}`));
                  setDirty(false);
                } catch (e) {
                  setError((e as Error).message);
                }
              }}
            >
              {q.published ? "View" : "Review & edit"}
            </button>
          </div>
        ))}
        {!quizzes.length && (
          <Empty
            title="A fresh page"
            description="Generate your first pack from an approved chapter."
          />
        )}
      </section>
    </>
  );
}
