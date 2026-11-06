"use client";
import { useEffect, useState } from "react";
import { TrendingUp } from "lucide-react";
import { api, dateLabel } from "@/lib/api";
import {
  Empty,
  ErrorMessage,
  PageHeading,
  useWorkspace,
} from "@/components/workspace";
type Data = {
  attendance: { day: string; total: number; present: number }[];
  assignments: {
    title: string;
    students: number;
    submitted: number;
    complete: number;
  }[];
  topics: { topic: string; correct: number; total: number }[];
  practice_attempts: number;
};
export default function Analytics() {
  const { user } = useWorkspace();
  const [data, setData] = useState<Data | null>(null);
  const [error, setError] = useState("");
  useEffect(() => {
    if (user.role !== "student")
      api<Data>("/analytics")
        .then(setData)
        .catch((e) => setError(e.message));
  }, [user.role]);
  if (user.role === "student")
    return (
      <Empty
        title="A space for your teachers"
        description="Your own practice feedback is available in Nexora Arena."
      />
    );
  const total = data?.attendance.reduce((n, a) => n + a.total, 0) || 0;
  const present = data?.attendance.reduce((n, a) => n + a.present, 0) || 0;
  return (
    <>
      <PageHeading
        eyebrow="A CLEARER PICTURE"
        title="Notice the little things."
        description="Simple classroom insights to help you decide where a little extra support could help."
      />
      <ErrorMessage error={error} />
      <div className="stats-grid analytics-stats">
        {[
          {
            title: "Attendance across marked days",
            value: total ? `${Math.round((present / total) * 100)}%` : "—",
            detail: "Based on the latest 14 marked days",
          },
          {
            title: "Assignments shared",
            value: data?.assignments.length ?? "—",
            detail: "Across your assigned classes",
          },
          {
            title: "Practice challenges completed",
            value: data?.practice_attempts ?? "—",
            detail: "Practice feedback, reviewed by people",
          },
        ].map((s) => (
          <div className="stat-card" key={s.title}>
            <div>
              <span>{s.title}</span>
              <span className="icon-tile green">
                <TrendingUp size={18} />
              </span>
            </div>
            <strong>{s.value}</strong>
            <p>{s.detail}</p>
          </div>
        ))}
      </div>
      <div className="analytics-grid">
        <section className="panel">
          <div className="section-heading">
            <h2>Attendance, day by day</h2>
            <span className="badge green">Present %</span>
          </div>
          {data?.attendance.length ? (
            <div
              className="analytics-chart"
              role="img"
              aria-label={data.attendance
                .map(
                  (a) =>
                    `${a.day}: ${Math.round((a.present / a.total) * 100)}% present`,
                )
                .join(", ")}
            >
              {data.attendance.slice(-10).map((a) => (
                <div className="chart-column" key={a.day}>
                  <strong>{Math.round((a.present / a.total) * 100)}%</strong>
                  <div
                    className="chart-bar"
                    style={{ height: `${(a.present / a.total) * 80}%` }}
                  />
                  <small>{dateLabel(a.day)}</small>
                </div>
              ))}
            </div>
          ) : (
            <Empty
              title="A fresh start"
              description="Mark attendance to start seeing trends."
            />
          )}
        </section>
        <section className="panel">
          <div className="section-heading">
            <h2>Concepts to revisit</h2>
            <span className="subtle">Lowest practice accuracy first</span>
          </div>
          {data?.topics.length ? (
            data.topics.map((t) => (
              <div className="topic-row" key={t.topic}>
                <div>
                  <strong>{t.topic}</strong>
                  <span>
                    {t.correct} / {t.total} correct
                  </span>
                </div>
                <progress max={t.total} value={t.correct} />
              </div>
            ))
          ) : (
            <Empty
              title="Let curiosity lead"
              description="Topic insights appear after students complete Arena challenges."
            />
          )}
        </section>
        <section className="panel" style={{ gridColumn: "1 / -1" }}>
          <div className="section-heading">
            <h2>Assignment completion</h2>
            <span className="subtle">Submission and teacher review</span>
          </div>
          <div className="table-scroll">
            <table>
              <thead>
                <tr>
                  <th>Assignment</th>
                  <th>Submitted</th>
                  <th>Teacher marked complete</th>
                  <th>Class size</th>
                </tr>
              </thead>
              <tbody>
                {data?.assignments.map((a, i) => (
                  <tr key={i}>
                    <td>{a.title}</td>
                    <td>{a.submitted}</td>
                    <td>{a.complete}</td>
                    <td>{a.students}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </section>
      </div>
    </>
  );
}
