"use client";
import { useEffect, useState } from "react";
import { Plus, GraduationCap, Megaphone, Users } from "lucide-react";
import { api, post, User } from "@/lib/api";
import {
  Empty,
  ErrorMessage,
  Modal,
  PageHeading,
  useWorkspace,
} from "@/components/workspace";

export default function AdminPage() {
  const { user, classes, refresh, notice } = useWorkspace();
  const [users, setUsers] = useState<User[]>([]);
  const [audit, setAudit] = useState<
    { id: number; action: string; actor_id: number; created_at: string }[]
  >([]);
  const [modal, setModal] = useState("");
  const [error, setError] = useState("");
  const [busy, setBusy] = useState(false);
  const [teacherIds, setTeacherIds] = useState<number[]>([]);
  const [studentIds, setStudentIds] = useState<number[]>([]);
  const load = async () => {
    const [u, a] = await Promise.all([
      api<User[]>("/users"),
      api<typeof audit>("/audit"),
    ]);
    setUsers(u);
    setAudit(a);
  };
  useEffect(() => {
    if (user.role === "admin") load().catch((e) => setError(e.message));
  }, [user.role]);
  if (user.role !== "admin")
    return (
      <Empty
        title="School administrator access"
        description="Your account does not have access to school administration."
      />
    );
  const action = async (e: React.FormEvent<HTMLFormElement>) => {
    e.preventDefault();
    const f = new FormData(e.currentTarget);
    setBusy(true);
    setError("");
    try {
      if (modal === "class")
        await post("/classes", {
          name: f.get("name"),
          grade: Number(f.get("grade")),
          teacher_ids: teacherIds,
          student_ids: studentIds,
        });
      if (modal === "user")
        await post("/users", {
          name: f.get("name"),
          email: f.get("email"),
          password: f.get("password"),
          role: f.get("role"),
        });
      if (modal === "announcement")
        await post("/announcements", {
          title: f.get("title"),
          body: f.get("body"),
        });
      await Promise.all([load(), refresh()]);
      setModal("");
      setStudentIds([]);
      setTeacherIds([]);
      notice("Saved to your school workspace.");
    } catch (e) {
      setError((e as Error).message);
    } finally {
      setBusy(false);
    }
  };
  return (
    <>
      <PageHeading
        eyebrow="BRING YOUR SCHOOL TOGETHER"
        title="A place for everyone."
        description="Create school-issued accounts, form classes, and keep everyone informed."
        action={
          <button
            className="button"
            onClick={() => {
              setError("");
              setModal("class");
            }}
          >
            <Plus size={17} />
            Create class
          </button>
        }
      />
      <div className="admin-actions">
        <button
          className="button secondary"
          onClick={() => {
            setError("");
            setModal("user");
          }}
        >
          <Users size={17} />
          Create account
        </button>
        <button
          className="button secondary"
          onClick={() => {
            setError("");
            setModal("announcement");
          }}
        >
          <Megaphone size={17} />
          Publish announcement
        </button>
      </div>
      <ErrorMessage error={!modal ? error : ""} />
      <div className="cards-grid mt">
        {classes.map((c) => (
          <article className="panel class-card" key={c.id}>
            <span className="icon-tile green">
              <GraduationCap size={24} />
            </span>
            <h2>{c.name}</h2>
            <p>
              Grade {c.grade} · {c.students} students
            </p>
          </article>
        ))}
      </div>
      <section className="panel mt">
        <div className="section-heading">
          <h2>Your school community</h2>
          <span className="subtle">{users.length} accounts</span>
        </div>
        <div className="table-scroll">
          <table>
            <thead>
              <tr>
                <th>Name</th>
                <th>School email</th>
                <th>Role</th>
              </tr>
            </thead>
            <tbody>
              {users.map((u) => (
                <tr key={u.id}>
                  <td>{u.name}</td>
                  <td>{u.email}</td>
                  <td>
                    <span className="badge green">{u.role}</span>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </section>
      <section className="panel mt">
        <div className="section-heading">
          <h2>Activity audit</h2>
          <span className="subtle">Latest sensitive actions</span>
        </div>
        {audit.slice(0, 15).map((a) => (
          <div key={a.id} className="audit-row">
            <strong>{a.action.replaceAll("_", " ")}</strong>
            <span>{users.find((u) => u.id === a.actor_id)?.name}</span>
            <small>
              {new Date(a.created_at + "Z").toLocaleString("en-IN", {
                timeZone: "Asia/Kolkata",
              })}
            </small>
          </div>
        ))}
      </section>
      <Modal
        open={!!modal}
        onOpenChange={(v) => {
          if (!v) setModal("");
        }}
        title={
          modal === "class"
            ? "Create a class"
            : modal === "user"
              ? "Create a school account"
              : "A note to your school"
        }
        description={
          modal === "class"
            ? "Choose a teacher and students from your school accounts."
            : modal === "user"
              ? "Issue student accounts through the school. Share passwords privately."
              : "This announcement will be visible to your school community."
        }
      >
        <form onSubmit={action}>
          {modal === "class" ? (
            <>
              <label>
                Class name
                <input
                  name="name"
                  minLength={2}
                  maxLength={80}
                  placeholder="Class 7 · A"
                  required
                />
              </label>
              <label>
                Grade
                <select name="grade">
                  {Array.from({ length: 10 }, (_, i) => (
                    <option key={i + 1}>{i + 1}</option>
                  ))}
                </select>
              </label>
              {(["teacher", "student"] as const).map((role) => (
                <fieldset key={role}>
                  <legend>
                    {role === "teacher" ? "Teachers" : "Students"}
                  </legend>
                  <div className="member-list">
                    {users
                      .filter((u) => u.role === role)
                      .map((u) => (
                        <label className="check-label" key={u.id}>
                          <input
                            type="checkbox"
                            checked={(role === "teacher"
                              ? teacherIds
                              : studentIds
                            ).includes(u.id)}
                            onChange={(e) => {
                              const setter =
                                role === "teacher"
                                  ? setTeacherIds
                                  : setStudentIds;
                              setter((prev) =>
                                e.target.checked
                                  ? [...prev, u.id]
                                  : prev.filter((x) => x !== u.id),
                              );
                            }}
                          />
                          {u.name}
                        </label>
                      ))}
                  </div>
                </fieldset>
              ))}
            </>
          ) : modal === "user" ? (
            <>
              <label>
                Full name
                <input name="name" minLength={2} maxLength={100} required />
              </label>
              <label>
                School email
                <input name="email" type="email" required />
              </label>
              <label>
                Role
                <select name="role">
                  <option value="student">Student</option>
                  <option value="teacher">Teacher</option>
                  <option value="admin">Administrator</option>
                </select>
              </label>
              <label>
                Temporary password
                <input
                  name="password"
                  type="password"
                  minLength={12}
                  maxLength={128}
                  autoComplete="new-password"
                  required
                />
                <small>
                  At least 12 characters. The user can change this in Account
                  settings.
                </small>
              </label>
            </>
          ) : (
            <>
              <label>
                Title
                <input name="title" minLength={3} maxLength={160} required />
              </label>
              <label>
                Announcement
                <textarea name="body" minLength={5} maxLength={3000} required />
              </label>
            </>
          )}
          <ErrorMessage error={error} />
          <button className="button full" disabled={busy}>
            {busy
              ? "Saving…"
              : modal === "class"
                ? "Create class"
                : modal === "user"
                  ? "Create account"
                  : "Publish announcement"}
          </button>
        </form>
      </Modal>
    </>
  );
}
