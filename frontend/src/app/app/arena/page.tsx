"use client";
import { useEffect, useState } from "react";
import { ArrowRight, BookOpen, Check, Sparkles, Swords } from "lucide-react";
import { api, post } from "@/lib/api";
import { Empty, ErrorMessage, useWorkspace } from "@/components/workspace";
type Quiz = { id: number; title: string; published: boolean; class_id: number };
type State = {
  daily_quiz_id: number | null;
  daily_completed: boolean;
  badges: { name: string; description: string; icon: string }[];
  completed_challenges: number;
  history: {
    id: number;
    quiz_id: number;
    score: number;
    total: number;
    day: string;
    mode: string;
  }[];
};
type Detail = {
  id: number;
  title: string;
  summary: string;
  questions: {
    id: number;
    kind: string;
    question: string;
    options: string[];
    topic: string;
  }[];
  flashcards: { front: string; back: string }[];
};
type Feedback = {
  correct: boolean;
  answer: string;
  explanation: string;
  source_quote: string;
};
export default function Arena() {
  const { user, notice } = useWorkspace();
  const student = user.role === "student";
  const [quizzes, setQuizzes] = useState<Quiz[]>([]);
  const [state, setState] = useState<State | null>(null);
  const [selected, setSelected] = useState("");
  const [detail, setDetail] = useState<Detail | null>(null);
  const [mode, setMode] = useState<"daily" | "class">("daily");
  const [playing, setPlaying] = useState(false);
  const [index, setIndex] = useState(0);
  const [answers, setAnswers] = useState<Record<number, string>>({});
  const [choice, setChoice] = useState("");
  const [feedback, setFeedback] = useState<Feedback | null>(null);
  const [result, setResult] = useState<{
    score: number;
    total: number;
    message: string;
  } | null>(null);
  const [error, setError] = useState("");
  const [busy, setBusy] = useState(false);
  const [flipped, setFlipped] = useState<Record<number, boolean>>({});
  const [practiceAnswers, setPracticeAnswers] = useState<
    Record<
      number,
      { answer: string; explanation: string; source_quote: string }
    >
  >({});
  const load = async () => {
    const [q, s] = await Promise.all([
      api<Quiz[]>("/quizzes"),
      api<State>("/arena"),
    ]);
    setQuizzes(q.filter((x) => x.published));
    setState(s);
  };
  useEffect(() => {
    load().catch((e) => setError(e.message));
  }, []);
  const start = async (id: number, m: "daily" | "class", play = true) => {
    setBusy(true);
    setError("");
    try {
      const d = await api<Detail>(`/quizzes/${id}`);
      if (play) {
        d.questions = d.questions.filter((q) => q.kind === "mcq");
        if (m === "daily") d.questions = d.questions.slice(0, 5);
      }
      setDetail(d);
      setMode(m);
      setIndex(0);
      setAnswers({});
      setChoice("");
      setFeedback(null);
      setResult(null);
      setPlaying(play);
      setFlipped({});
      setPracticeAnswers({});
    } catch (e) {
      setError((e as Error).message);
    } finally {
      setBusy(false);
    }
  };
  const current = detail?.questions[index];
  if (playing && detail && current)
    return (
      <div className="quiz-play">
        <button
          className="text-link"
          onClick={() => {
            setPlaying(false);
            setDetail(null);
          }}
        >
          ← Back to Arena
        </button>
        <section className="panel mt">
          {result ? (
            <div className="result-card">
              <span className="result-star">✦</span>
              <h2>A little wiser than before.</h2>
              <p>{result.message}</p>
              <div className="result-score">
                {result.score}
                <span className="subtle"> / {result.total}</span>
              </div>
              <p>
                This is practice feedback. Your teacher makes academic
                decisions.
              </p>
              <button
                className="button mt"
                onClick={() => {
                  setPlaying(false);
                  setDetail(null);
                }}
              >
                Back to your learning space <ArrowRight size={16} />
              </button>
            </div>
          ) : (
            <>
              <div className="quiz-progress">
                <span>
                  {mode === "daily"
                    ? "DAILY BRAIN CHALLENGE"
                    : "CLASS QUIZ CHALLENGE"}
                </span>
                <span>
                  {index + 1} / {detail.questions.length}
                </span>
              </div>
              <progress value={index + 1} max={detail.questions.length} />
              <h2>{current.question}</h2>
              <div className="answer-options">
                {current.options.map((o, i) => (
                  <button
                    key={i}
                    disabled={!!feedback || busy}
                    className={choice === o ? "selected" : ""}
                    onClick={() => setChoice(o)}
                  >
                    <span>{String.fromCharCode(65 + i)}</span>
                    {o}
                  </button>
                ))}
              </div>
              {feedback ? (
                <>
                  <div
                    className={`quiz-feedback ${feedback.correct ? "" : "incorrect"}`}
                    role="status"
                  >
                    <h3>
                      {feedback.correct
                        ? "That’s a thoughtful answer."
                        : "A chance to discover something."}
                    </h3>
                    {!feedback.correct && (
                      <p>
                        <strong>Answer: {feedback.answer}</strong>
                      </p>
                    )}
                    <p>{feedback.explanation}</p>
                    <blockquote className="source-quote">
                      {feedback.source_quote}
                    </blockquote>
                  </div>
                  <button
                    className="button full mt"
                    disabled={busy}
                    onClick={async () => {
                      if (index < detail.questions.length - 1) {
                        setIndex(index + 1);
                        setChoice("");
                        setFeedback(null);
                      } else {
                        setBusy(true);
                        setError("");
                        try {
                          const r = await post<{
                            score: number;
                            total: number;
                            message: string;
                          }>(`/quizzes/${detail.id}/attempts`, {
                            mode,
                            answers,
                          });
                          setResult(r);
                          await load();
                          notice("Challenge complete. Your curiosity counts.");
                        } catch (e) {
                          setError((e as Error).message);
                        } finally {
                          setBusy(false);
                        }
                      }
                    }}
                  >
                    {busy
                      ? "Saving your progress…"
                      : index < detail.questions.length - 1
                        ? "Next question"
                        : "Complete challenge"}
                    <ArrowRight size={16} />
                  </button>
                </>
              ) : (
                <button
                  className="button full mt"
                  disabled={!choice || busy}
                  onClick={async () => {
                    setBusy(true);
                    setError("");
                    try {
                      setFeedback(
                        await post<Feedback>(`/quizzes/${detail.id}/check`, {
                          mode,
                          answers: { [current.id]: choice },
                        }),
                      );
                      setAnswers((prev) => ({ ...prev, [current.id]: choice }));
                    } catch (e) {
                      setError((e as Error).message);
                    } finally {
                      setBusy(false);
                    }
                  }}
                >
                  {busy ? "Checking…" : "Check my answer"}
                  <Check size={16} />
                </button>
              )}
              <ErrorMessage error={error} />
            </>
          )}
        </section>
      </div>
    );
  return (
    <>
      <div className="arena-heading">
        <div>
          <span className="eyebrow">
            <Swords size={16} /> NEXORA ARENA
          </span>
          <h1>
            Small challenges.
            <br />
            Big little discoveries.
          </h1>
          <p>
            A place to play with ideas. No rankings, no rush. Just room to grow.
          </p>
        </div>
        <span className="arena-mark">✳</span>
      </div>
      <ErrorMessage error={error} />
      <div className="arena-modes">
        <section className="panel arena-mode daily">
          <span className="icon-tile amber">
            <Sparkles size={24} />
          </span>
          <h2>The daily brain challenge</h2>
          <p>
            Five short questions from a teacher-approved chapter. A little spark
            for today’s learning.
          </p>
          <button
            className="button"
            disabled={busy || !state?.daily_quiz_id || !!state?.daily_completed}
            onClick={() => {
              if (state?.daily_quiz_id)
                start(state.daily_quiz_id, "daily", student);
            }}
          >
            {state?.daily_completed
              ? "Today’s challenge completed"
              : student
                ? "Let’s give it a go"
                : "Preview today’s chapter"}
            <ArrowRight size={16} />
          </button>
          {!state?.daily_quiz_id && (
            <p className="subtle mt">
              Your teacher will publish your first challenge soon.
            </p>
          )}
        </section>
        <section className="panel arena-mode">
          <span className="icon-tile green">
            <BookOpen size={24} />
          </span>
          <h2>Your classroom, your challenge</h2>
          <p>
            A little chapter practice, with summaries and flashcards to make the
            ideas stick.
          </p>
          <label>
            <span className="sr-only">Choose class challenge</span>
            <select
              value={selected}
              onChange={(e) => setSelected(e.target.value)}
            >
              <option value="">Choose an approved learning pack</option>
              {quizzes.map((q) => (
                <option key={q.id} value={q.id}>
                  {q.title}
                </option>
              ))}
            </select>
          </label>
          <div className="form-row">
            <button
              className="button secondary"
              disabled={!selected || busy}
              onClick={() => start(Number(selected), "class", false)}
            >
              Study pack
            </button>
            {student && (
              <button
                className="button"
                disabled={!selected || busy}
                onClick={() => start(Number(selected), "class", true)}
              >
                Take challenge <ArrowRight size={15} />
              </button>
            )}
          </div>
        </section>
      </div>
      {detail && !playing && (
        <section className="panel mt">
          <div className="section-heading">
            <h2>{detail.title}</h2>
            <button className="text-link" onClick={() => setDetail(null)}>
              Close
            </button>
          </div>
          <p className="lesson-text">{detail.summary}</p>
          {detail.questions
            .filter((q) => q.kind === "short_answer")
            .map((q) => (
              <div className="question-editor" key={q.id}>
                <span className="eyebrow">A LITTLE SHORT-ANSWER PRACTICE</span>
                <h3 className="mt">{q.question}</h3>
                <label className="mt">
                  Try it in your own words
                  <textarea
                    rows={3}
                    maxLength={2000}
                    placeholder="This practice stays in this page and is not graded."
                  />
                </label>
                {practiceAnswers[q.id] ? (
                  <div className="feedback">
                    <strong>One way to explain it</strong>
                    <p>{practiceAnswers[q.id].answer}</p>
                    <p>{practiceAnswers[q.id].explanation}</p>
                    <blockquote className="source-quote">
                      {practiceAnswers[q.id].source_quote}
                    </blockquote>
                  </div>
                ) : (
                  <button
                    className="text-link"
                    disabled={busy}
                    onClick={async () => {
                      setBusy(true);
                      setError("");
                      try {
                        const answer = await api<{
                          answer: string;
                          explanation: string;
                          source_quote: string;
                        }>(`/quizzes/${detail.id}/practice/${q.id}`);
                        setPracticeAnswers((prev) => ({
                          ...prev,
                          [q.id]: answer,
                        }));
                      } catch (e) {
                        setError((e as Error).message);
                      } finally {
                        setBusy(false);
                      }
                    }}
                  >
                    Compare with a sample explanation →
                  </button>
                )}
              </div>
            ))}
          <h2 className="mt">A little flashcard practice</h2>
          <p className="subtle mt">Tap a card to turn it over.</p>
          <div className="cards-grid">
            {detail.flashcards.map((c, i) => (
              <button
                key={i}
                className="flashcard"
                aria-label={`Flashcard ${i + 1}: ${flipped[i] ? "answer" : "question"}. Tap to flip.`}
                onClick={() =>
                  setFlipped((prev) => ({ ...prev, [i]: !prev[i] }))
                }
              >
                {flipped[i] ? c.back : c.front}
              </button>
            ))}
          </div>
        </section>
      )}
      <section className="panel mt">
        <div className="section-heading">
          <h2>A little recognition for your curiosity</h2>
          <span className="subtle">Personal achievements</span>
        </div>
        {state?.badges.length ? (
          <div className="badge-list">
            {state.badges.map((b) => (
              <div className="achievement" key={b.name}>
                <span>{b.icon}</span>
                <div>
                  <strong>{b.name}</strong>
                  <p>{b.description}</p>
                </div>
              </div>
            ))}
          </div>
        ) : (
          <Empty
            title={
              student
                ? "Your curiosity is the starting point"
                : "A space for student progress"
            }
            description="Personal badges celebrate participation and improvement. No public individual rankings."
          />
        )}
      </section>
      {student && !!state?.history.length && (
        <section className="panel mt">
          <div className="section-heading">
            <h2>Your practice journey</h2>
            <span className="subtle">
              Only you and authorized school staff can access your results.
            </span>
          </div>
          <div className="table-scroll">
            <table>
              <thead>
                <tr>
                  <th>Challenge</th>
                  <th>Date</th>
                  <th>Practice feedback</th>
                </tr>
              </thead>
              <tbody>
                {state.history
                  .slice()
                  .reverse()
                  .map((h) => (
                    <tr key={h.id}>
                      <td>
                        {quizzes.find((q) => q.id === h.quiz_id)?.title ||
                          "Class challenge"}
                      </td>
                      <td>{h.day}</td>
                      <td>
                        {h.score} / {h.total}
                      </td>
                    </tr>
                  ))}
              </tbody>
            </table>
          </div>
        </section>
      )}
    </>
  );
}
