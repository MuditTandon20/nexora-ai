"use client";
import { useEffect, useState } from "react";
import { Check, ClipboardList, Plus, Send } from "lucide-react";
import { api, post, dateLabel, indiaDate } from "@/lib/api";
import {
  ClassSubjectFields,
  Empty,
  ErrorMessage,
  Modal,
  PageHeading,
  useWorkspace,
} from "@/components/workspace";
type Homework = {
  id: number;
  class_id: number;
  subject_id: number;
  title: string;
  instructions: string;
  due_date: string;
  submission_count: number;
  student_count: number;
  my_submission: { answer: string; status: string; feedback: string } | null;
};
type Submission = {
  id: number;
  student_name: string;
  answer: string;
  status: string;
  feedback: string;
  submitted_at: string;
};
export default function AssignmentsPage() {
  const { user, classes, subjects, notice } = useWorkspace();
  const student = user.role === "student";
  const [items, setItems] = useState<Homework[]>([]);
  const [create, setCreate] = useState(false);
  const [selected, setSelected] = useState<Homework | null>(null);
  const [submissions, setSubmissions] = useState<Submission[]>([]);
  const [classId, setClassId] = useState("");
  const [subjectId, setSubjectId] = useState("");
  const [error, setError] = useState("");
  const [busy, setBusy] = useState(false);
  const load = () => api<Homework[]>("/homework").then(setItems);
  useEffect(() => {
    const query = new URLSearchParams(window.location.search);
    if (!student && query.get("create") === "1") setCreate(true);
    api<Homework[]>("/homework")
      .then(async (rows) => {
        setItems(rows);
        const target = rows.find((h) => h.id === Number(query.get("review")));
        if (target && !student) {
          setSubmissions(
            await api<Submission[]>(`/homework/${target.id}/submissions`),
          );
          setSelected(target);
        }
      })
      .catch((e) => setError(e.message));
  }, []);
  const openHomework = async (h: Homework) => {
    setError("");
    setSubmissions([]);
    if (!student) {
      try {
        setSubmissions(
          await api<Submission[]>(`/homework/${h.id}/submissions`),
        );
      } catch (e) {
        setError((e as Error).message);
        return;
      }
    }
    setSelected(h);
  };
  return (
    <>
      <PageHeading
        eyebrow="SMALL PRACTICE. REAL PROGRESS."
        title={student ? "Your next little step." : "Make room for practice."}
        description={
          student
            ? "Explore an assignment, share your thinking, and hear from your teacher."
            : "Create meaningful work and give feedback that helps students grow."
        }
        action={
          !student && (
            <button
              className="button"
              onClick={() => {
                setError("");
                setCreate(true);
              }}
            >
              <Plus size={17} />
              Create assignment
            </button>
          )
        }
      />
      <ErrorMessage error={!create && !selected ? error : ""} />
      <div className="cards-grid">
        {items.map((h) => (
          <article className="panel homework-card" key={h.id}>
            <div className="homework-card-top">
              <span className="icon-tile amber">
                <ClipboardList size={24} />
              </span>
              <span className="badge neutral">Due {dateLabel(h.due_date)}</span>
            </div>
            <small className="eyebrow">
              {subjects.find((s) => s.id === h.subject_id)?.name} ·{" "}
              {classes.find((c) => c.id === h.class_id)?.name}
            </small>
            <h2>{h.title}</h2>
            <p>{h.instructions}</p>
            {student ? (
              <div
                className={`badge ${h.my_submission?.status === "complete" ? "green" : "amber"}`}
              >
                {h.my_submission?.status.replaceAll("_", " ") ||
                  "Ready to begin"}
              </div>
            ) : (
              <div className="submission-progress">
                <div>
                  <span>Submissions</span>
                  <strong>
                    {h.submission_count} / {h.student_count}
                  </strong>
                </div>
                <progress
                  max={h.student_count || 1}
                  value={h.submission_count}
                />
              </div>
            )}
            <button
              className="button secondary full mt"
              onClick={() => openHomework(h)}
            >
              {student ? "Open assignment" : "Review submissions"} →
            </button>
          </article>
        ))}
      </div>
      {!items.length && (
        <Empty
          title="A clear learning list"
          description="Assignments will appear here when a teacher creates them."
        />
      )}
      <Modal
        open={create}
        onOpenChange={setCreate}
        title="A new learning opportunity"
        description="This assignment will notify every student in the selected class."
      >
        <form
          onSubmit={async (e) => {
            e.preventDefault();
            const f = new FormData(e.currentTarget);
            setBusy(true);
            setError("");
            try {
              await post("/homework", {
                class_id: Number(classId),
                subject_id: Number(subjectId),
                title: f.get("title"),
                instructions: f.get("instructions"),
                due_date: f.get("due_date"),
              });
              await load();
              setCreate(false);
              notice("Assignment shared with your class.");
            } catch (e) {
              setError((e as Error).message);
            } finally {
              setBusy(false);
            }
          }}
        >
          <ClassSubjectFields
            {...{ classId, setClassId, subjectId, setSubjectId }}
          />
          <label>
            Assignment title
            <input name="title" minLength={3} maxLength={160} required />
          </label>
          <label>
            What should students do?
            <textarea
              name="instructions"
              minLength={5}
              maxLength={10000}
              required
              rows={5}
            />
          </label>
          <label>
            Due date
            <input name="due_date" type="date" min={indiaDate()} required />
          </label>
          <ErrorMessage error={error} />
          <button className="button full" disabled={busy}>
            {busy ? "Sharing…" : "Create assignment"}
          </button>
        </form>
      </Modal>
      <Modal
        open={!!selected}
        onOpenChange={(v) => {
          if (!v) setSelected(null);
        }}
        title={selected?.title || "Assignment"}
        description={`Due ${selected ? dateLabel(selected.due_date) : ""}`}
      >
        <p className="lesson-text">{selected?.instructions}</p>
        <ErrorMessage error={error} />
        {student ? (
          <>
            {selected?.my_submission?.feedback && (
              <div className="feedback">
                <strong>Your teacher’s feedback</strong>
                <p>{selected.my_submission.feedback}</p>
              </div>
            )}
            <form
              key={selected?.id}
              onSubmit={async (e) => {
                e.preventDefault();
                setBusy(true);
                setError("");
                const f = new FormData(e.currentTarget);
                try {
                  await post(`/homework/${selected?.id}/submit`, {
                    answer: f.get("answer"),
                  });
                  await load();
                  setSelected(null);
                  notice("Your work is with your teacher. Nicely done.");
                } catch (e) {
                  setError((e as Error).message);
                } finally {
                  setBusy(false);
                }
              }}
            >
              <label>
                Your thinking
                <textarea
                  name="answer"
                  defaultValue={selected?.my_submission?.answer || ""}
                  minLength={1}
                  maxLength={20000}
                  required
                  rows={7}
                  disabled={selected?.my_submission?.status === "complete"}
                />
              </label>
              <button
                disabled={
                  busy || selected?.my_submission?.status === "complete"
                }
                className="button full"
              >
                <Send size={16} />
                {selected?.my_submission?.status === "complete"
                  ? "Marked complete"
                  : busy
                    ? "Submitting…"
                    : "Submit your work"}
              </button>
            </form>
          </>
        ) : (
          <div className="review-list">
            {!submissions.length && (
              <Empty
                title="Thinking in progress"
                description="Student submissions will appear here."
              />
            )}
            {submissions.map((s) => (
              <form
                key={s.id}
                className="review-card"
                onSubmit={async (e) => {
                  e.preventDefault();
                  const f = new FormData(e.currentTarget);
                  setBusy(true);
                  setError("");
                  try {
                    await post(`/submissions/${s.id}/review`, {
                      status: f.get("status"),
                      feedback: f.get("feedback"),
                    });
                    setSubmissions(
                      await api<Submission[]>(
                        `/homework/${selected?.id}/submissions`,
                      ),
                    );
                    await load();
                    notice("Feedback sent to the student.");
                  } catch (e) {
                    setError((e as Error).message);
                  } finally {
                    setBusy(false);
                  }
                }}
              >
                <div className="section-heading">
                  <strong>{s.student_name}</strong>
                  <span className="badge green">
                    {s.status.replaceAll("_", " ")}
                  </span>
                </div>
                <p className="lesson-text">{s.answer}</p>
                <label>
                  Your feedback
                  <textarea
                    name="feedback"
                    defaultValue={s.feedback}
                    maxLength={2000}
                  />
                </label>
                <div className="form-row">
                  <label>
                    Review status
                    <select
                      name="status"
                      defaultValue={
                        s.status === "needs_revision"
                          ? "needs_revision"
                          : "complete"
                      }
                    >
                      <option value="complete">Complete</option>
                      <option value="needs_revision">Needs revision</option>
                    </select>
                  </label>
                  <button className="button" disabled={busy}>
                    <Check size={16} />
                    Save review
                  </button>
                </div>
              </form>
            ))}
          </div>
        )}
      </Modal>
    </>
  );
}
