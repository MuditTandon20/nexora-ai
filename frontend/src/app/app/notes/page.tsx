"use client";
import { useEffect, useState } from "react";
import { BookOpen, Download, Plus, ShieldCheck } from "lucide-react";
import { api, post } from "@/lib/api";
import {
  ClassSubjectFields,
  Empty,
  ErrorMessage,
  Modal,
  PageHeading,
  useWorkspace,
} from "@/components/workspace";
export type Material = {
  id: number;
  title: string;
  class_id: number;
  subject_id: number;
  content: string;
  approved: boolean;
  has_file: boolean;
  created_at: string;
};
export default function NotesPage() {
  const { user, classes, subjects, notice } = useWorkspace();
  const [materials, setMaterials] = useState<Material[]>([]);
  const [open, setOpen] = useState(false);
  const [view, setView] = useState<Material | null>(null);
  const [classId, setClassId] = useState("");
  const [subjectId, setSubjectId] = useState("");
  const [mode, setMode] = useState("text");
  const [error, setError] = useState("");
  const [busy, setBusy] = useState(false);
  const [filter, setFilter] = useState("");
  const load = () => api<Material[]>("/materials").then(setMaterials);
  useEffect(() => {
    load().catch((e) => setError(e.message));
    if (
      user.role !== "student" &&
      new URLSearchParams(window.location.search).get("create") === "1"
    )
      setOpen(true);
  }, []);
  return (
    <>
      <PageHeading
        eyebrow="A SHELF OF POSSIBILITIES"
        title="Good ideas live here."
        description={
          user.role === "student"
            ? "Your teacher-approved chapter notes, ready to explore."
            : "Upload a PDF or write a lesson. Review it before sharing with students."
        }
        action={
          user.role !== "student" && (
            <button
              className="button"
              onClick={() => {
                setError("");
                setOpen(true);
              }}
            >
              <Plus size={17} />
              Add study material
            </button>
          )
        }
      />
      <ErrorMessage error={!open ? error : ""} />
      <div className="filter-tabs">
        <button
          className={!filter ? "selected" : ""}
          onClick={() => setFilter("")}
        >
          All materials <span>{materials.length}</span>
        </button>
        {subjects.map((s) => (
          <button
            key={s.id}
            className={filter === String(s.id) ? "selected" : ""}
            onClick={() => setFilter(String(s.id))}
          >
            {s.name}
          </button>
        ))}
      </div>
      <div className="cards-grid">
        {materials
          .filter((m) => !filter || m.subject_id === Number(filter))
          .map((m, i) => (
            <article className="panel material-card" key={m.id}>
              <div className={`material-cover cover-${i % 3}`}>
                <BookOpen size={38} />
                <span>{subjects.find((s) => s.id === m.subject_id)?.name}</span>
                <small>CHAPTER NOTES</small>
                <span className="cover-flower">✳</span>
              </div>
              <div className="material-body">
                <div className="material-meta">
                  <span>{classes.find((c) => c.id === m.class_id)?.name}</span>
                  <span className={`badge ${m.approved ? "green" : "amber"}`}>
                    {m.approved ? "Approved" : "Draft"}
                  </span>
                </div>
                <h2>{m.title}</h2>
                <p>{m.content.slice(0, 125)}…</p>
                <div className="material-actions">
                  <button className="text-link" onClick={() => setView(m)}>
                    Read lesson →
                  </button>
                  {m.has_file && (
                    <a
                      className="icon-button"
                      href={`/api/materials/${m.id}/download`}
                      aria-label={`Download ${m.title}`}
                    >
                      <Download size={18} />
                    </a>
                  )}
                  {!m.approved && user.role !== "student" && (
                    <button
                      disabled={busy}
                      className="button secondary compact"
                      onClick={async () => {
                        setBusy(true);
                        try {
                          await post(`/materials/${m.id}/approve`);
                          await load();
                          notice("Lesson approved and shared with the class.");
                        } catch (e) {
                          setError((e as Error).message);
                        } finally {
                          setBusy(false);
                        }
                      }}
                    >
                      <ShieldCheck size={15} />
                      Approve
                    </button>
                  )}
                </div>
              </div>
            </article>
          ))}
      </div>
      {!materials.length && (
        <Empty
          title="Your bookshelf is ready"
          description="Approved study materials will appear here."
        />
      )}
      <Modal
        open={open}
        onOpenChange={setOpen}
        title="Add a little knowledge"
        description="PDFs are private, text-readable, at most 10 MB and 100 pages. Uploads start as drafts."
      >
        <form
          onSubmit={async (e) => {
            e.preventDefault();
            setBusy(true);
            setError("");
            const f = new FormData(e.currentTarget);
            try {
              if (mode === "pdf") {
                f.set("class_id", classId);
                f.set("subject_id", subjectId);
                await api("/materials/upload", { method: "POST", body: f });
              } else
                await post("/materials", {
                  class_id: Number(classId),
                  subject_id: Number(subjectId),
                  title: f.get("title"),
                  content: f.get("content"),
                  approved: false,
                });
              await load();
              setOpen(false);
              notice(
                "Material saved as a draft. Read it, then approve it for your class.",
              );
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
            Lesson title
            <input name="title" minLength={3} maxLength={160} required />
          </label>
          <div className="segmented">
            <button
              type="button"
              className={mode === "text" ? "selected" : ""}
              onClick={() => setMode("text")}
            >
              Write lesson
            </button>
            <button
              type="button"
              className={mode === "pdf" ? "selected" : ""}
              onClick={() => setMode("pdf")}
            >
              Upload PDF
            </button>
          </div>
          {mode === "text" ? (
            <label>
              Chapter content
              <textarea
                name="content"
                minLength={30}
                maxLength={60000}
                rows={8}
                required
                placeholder="Use trusted, age-appropriate chapter content."
              />
            </label>
          ) : (
            <label className="upload-zone">
              <BookOpen size={28} />
              <span>Choose a readable PDF</span>
              <input
                name="file"
                type="file"
                accept="application/pdf,.pdf"
                required
              />
            </label>
          )}
          <ErrorMessage error={error} />
          <button disabled={busy} className="button full">
            {busy ? "Saving lesson…" : "Save draft material"}
          </button>
        </form>
      </Modal>
      <Modal
        open={!!view}
        onOpenChange={(v) => {
          if (!v) setView(null);
        }}
        title={view?.title || "Lesson"}
        description="Approved learning content is the source for your learning tools."
      >
        <div className="lesson-text">{view?.content}</div>
      </Modal>
    </>
  );
}
