"use client";
import { useEffect, useState } from "react";
import Link from "next/link";
import {
  ArrowRight,
  ArrowUpRight,
  Bell,
  BookOpen,
  CalendarCheck,
  Check,
  ClipboardList,
  Clock3,
  Leaf,
  Plus,
  Sparkles,
  Swords,
} from "lucide-react";
import { api, dateLabel } from "@/lib/api";
import { Empty, ErrorMessage, useWorkspace } from "@/components/workspace";

type Dashboard = {
  date: string;
  classes: number;
  attendance_present: number;
  attendance_total: number;
  attendance_status: string | null;
  pending_review: number;
  materials: number;
  homework: { id: number; title: string; due_date: string; class_id: number }[];
  announcements: { id: number; title: string; body: string }[];
};
export default function Overview() {
  const { user, classes } = useWorkspace();
  const [data, setData] = useState<Dashboard | null>(null);
  const [error, setError] = useState("");
  useEffect(() => {
    api<Dashboard>("/dashboard")
      .then(setData)
      .catch((e) => setError(e.message));
  }, []);
  const student = user.role === "student";
  const admin = user.role === "admin";
  return (
    <>
      <div className="welcome-row">
        <div>
          <div className="eyebrow">
            <span className="greeting-dot" /> A FRESH DAY, FULL OF POSSIBILITY
          </div>
          <h1>
            {student
              ? "Ready for a little discovery"
              : "A good day to make a difference"}
            ,<br />
            <span>{user.name.split(" ")[0]}.</span>{" "}
            <span className="greeting-leaf">✳</span>
          </h1>
          <p>
            {student
              ? "Small steps, new ideas. Your learning adventure starts here."
              : "Your classroom, in a clear view. Let’s make today a little lighter."}
          </p>
        </div>
        <div className="date-card">
          <span>
            {data
              ? new Date(data.date + "T12:00:00").toLocaleDateString("en-IN", {
                  weekday: "long",
                })
              : "Today"}
          </span>
          <strong>{data ? dateLabel(data.date) : "…"}</strong>
          <small>ONE DAY. MANY POSSIBILITIES.</small>
        </div>
      </div>
      <ErrorMessage error={error} />
      <div className="stats-grid">
        {[
          {
            title: student ? "Today’s attendance" : "Your classes",
            value: student
              ? data?.attendance_status || "Not marked"
              : (data?.classes ?? "—"),
            detail: student
              ? "Only your own attendance is shown"
              : "A space for every curious mind",
            icon: CalendarCheck,
            color: "green",
          },
          {
            title: student ? "Study materials" : "Attendance today",
            value: student
              ? (data?.materials ?? "—")
              : data?.attendance_total
                ? `${Math.round((data.attendance_present / data.attendance_total) * 100)}%`
                : "Not marked",
            detail: student
              ? "Ready when you are"
              : data?.attendance_total
                ? `${data.attendance_present} of ${data.attendance_total} students present`
                : "Ready for your first roll call",
            icon: BookOpen,
            color: "blue",
          },
          {
            title: student ? "Assignments" : "Waiting for review",
            value: student
              ? (data?.homework.length ?? "—")
              : (data?.pending_review ?? "—"),
            detail: student
              ? "A little practice goes a long way"
              : "Submissions ready for your feedback",
            icon: ClipboardList,
            color: "amber",
          },
        ].map((s) => (
          <article className="stat-card" key={s.title}>
            <div>
              <span>{s.title}</span>
              <span className={`icon-tile ${s.color}`}>
                <s.icon size={19} />
              </span>
            </div>
            <strong>{s.value}</strong>
            <p>{s.detail}</p>
          </article>
        ))}
      </div>
      <div className="dashboard-grid">
        <div className="dashboard-primary">
          <section className="panel">
            <div className="section-heading">
              <div>
                <span className="eyebrow">LET’S GET INTO IT</span>
                <h2>
                  {student
                    ? "Your learning toolkit"
                    : "A little less clicking."}
                </h2>
              </div>
              <span className="subtle">Your everyday essentials</span>
            </div>
            <div className="quick-actions">
              {(student
                ? [
                    {
                      title: "Your assignments",
                      text: "A little practice, a lot of progress",
                      href: "/app/assignments",
                      icon: ClipboardList,
                      color: "green",
                    },
                    {
                      title: "Ask Study Buddy",
                      text: "Make a tricky idea click",
                      href: "/app/buddy",
                      icon: Sparkles,
                      color: "lilac",
                    },
                    {
                      title: "Explore notes",
                      text: "Pick up where you left off",
                      href: "/app/notes",
                      icon: BookOpen,
                      color: "blue",
                    },
                  ]
                : [
                    {
                      title: admin ? "Create a class" : "Mark attendance",
                      text: admin
                        ? "Bring your classroom together"
                        : "A quick roll call, then on we go",
                      href: admin ? "/app/admin" : "/app/attendance",
                      icon: admin ? Plus : CalendarCheck,
                      color: "green",
                    },
                    {
                      title: "Create an assignment",
                      text: "Give curious minds a little nudge",
                      href: "/app/assignments",
                      icon: ClipboardList,
                      color: "amber",
                    },
                    {
                      title: "Make a learning pack",
                      text: "From chapter notes to aha! moments",
                      href: "/app/studio",
                      icon: Sparkles,
                      color: "lilac",
                    },
                  ]
              ).map((a) => (
                <Link href={a.href} key={a.href} className="quick-action">
                  <span className={`icon-tile ${a.color}`}>
                    <a.icon size={22} />
                  </span>
                  <strong>{a.title}</strong>
                  <p>{a.text}</p>
                  <ArrowUpRight size={17} />
                </Link>
              ))}
            </div>
          </section>
          <section className="panel">
            <div className="section-heading">
              <div>
                <span className="eyebrow">A LITTLE FOCUS</span>
                <h2>
                  {student
                    ? "On your learning list"
                    : "Assignments at a glance"}
                </h2>
              </div>
              <Link href="/app/assignments" className="text-link">
                View all <ArrowRight size={15} />
              </Link>
            </div>
            {data?.homework.length ? (
              <div className="assignment-list">
                {data.homework.map((h, i) => (
                  <Link
                    href="/app/assignments"
                    className="assignment-row"
                    key={h.id}
                  >
                    <span
                      className={`assignment-symbol ${i % 2 ? "lilac" : "blue"}`}
                    >
                      <BookOpen size={20} />
                    </span>
                    <div>
                      <strong>{h.title}</strong>
                      <small>
                        {classes.find((c) => c.id === h.class_id)?.name ||
                          "Your class"}
                      </small>
                    </div>
                    <span className="due-label">
                      <Clock3 size={13} />
                      Due {dateLabel(h.due_date)}
                    </span>
                    <ChevronArrow />
                  </Link>
                ))}
              </div>
            ) : (
              <Empty
                title={
                  data ? "A little breathing room" : "Loading assignments…"
                }
                description="Assignments from your classes will appear here."
              />
            )}
          </section>
          <section className="studio-banner">
            <div className="studio-banner-icon">
              <Sparkles size={28} />
            </div>
            <div>
              <span className="eyebrow">
                THOUGHTFUL TECH. REAL POSSIBILITIES.
              </span>
              <h2>
                {student
                  ? "Big questions are welcome here."
                  : "A teaching assistant for your teaching style."}
              </h2>
              <p>
                {student
                  ? "Explore your chapter, one question at a time."
                  : "Turn your approved chapter notes into quizzes, flashcards and summaries."}
              </p>
              <Link
                href={student ? "/app/buddy" : "/app/studio"}
                className="text-link"
              >
                {student ? "Meet Study Buddy" : "Open AI learning studio"}{" "}
                <ArrowRight size={16} />
              </Link>
            </div>
            <span className="banner-decoration">✳</span>
          </section>
        </div>
        <div className="dashboard-secondary">
          <section className="arena-card">
            <span className="arena-label">
              <Swords size={16} /> NEXORA ARENA
            </span>
            <div className="arena-art">
              <span>?</span>
              <span>✦</span>
              <span>+</span>
            </div>
            <h2>
              A small challenge.
              <br />A bright little spark.
            </h2>
            <p>
              Five questions. A fresh perspective.
              <br />
              Discover something new today.
            </p>
            <Link href="/app/arena" className="button arena-button">
              {student ? "Take today’s challenge" : "Explore class challenges"}
              <ArrowUpRight size={16} />
            </Link>
            <small>
              <Leaf size={13} /> Curiosity counts. Every single time.
            </small>
          </section>
          <section className="panel notice-panel">
            <div className="section-heading">
              <h2>Around your school</h2>
              <Bell size={18} />
            </div>
            {data?.announcements.map((a) => (
              <article className="notice-item" key={a.id}>
                <span className="notice-dot" />
                <div>
                  <strong>{a.title}</strong>
                  <p>{a.body}</p>
                </div>
              </article>
            ))}
            {!data?.announcements.length && (
              <p className="subtle">A quiet moment. No announcements yet.</p>
            )}
            <Link className="text-link" href="/app/notifications">
              All notifications <ArrowRight size={14} />
            </Link>
          </section>
          <div className="thought-card">
            <span>“</span>
            <p>
              The beautiful thing about learning is that it grows when you share
              it.
            </p>
            <small>A LITTLE THOUGHT FOR TODAY</small>
          </div>
        </div>
      </div>
    </>
  );
}
function ChevronArrow() {
  return <ArrowUpRight size={16} className="row-arrow" />;
}
