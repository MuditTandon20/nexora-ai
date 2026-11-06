"use client";
import { useEffect, useRef, useState } from "react";
import { CalendarCheck, Check, Download, Save, X } from "lucide-react";
import { api, post, indiaDate } from "@/lib/api";
import {
  Empty,
  ErrorMessage,
  Modal,
  PageHeading,
  useWorkspace,
} from "@/components/workspace";
type AttendanceData = {
  saved: boolean;
  version: string | null;
  records: { student_id: number; status: string }[];
};
export default function AttendancePage() {
  const { user, classes, notice } = useWorkspace();
  const [classId, setClassId] = useState("");
  const [day, setDay] = useState(indiaDate());
  const [roster, setRoster] = useState<{ id: number; name: string }[]>([]);
  const [absent, setAbsent] = useState<number[]>([]);
  const [data, setData] = useState<AttendanceData | null>(null);
  const [history, setHistory] = useState<
    { class_id: number; day: string; student_id: number; status: string }[]
  >([]);
  const [reason, setReason] = useState("");
  const [confirm, setConfirm] = useState(false);
  const [error, setError] = useState("");
  const [busy, setBusy] = useState(false);
  const [loading, setLoading] = useState(false);
  const requestSequence = useRef(0);
  const student = user.role === "student";
  useEffect(() => {
    if (classes.length && !classId) setClassId(String(classes[0].id));
  }, [classes, classId]);
  const load = async () => {
    if (!classId) return;
    const sequence = ++requestSequence.current;
    setLoading(true);
    setData(null);
    setError("");
    try {
      const [a, r, h] = await Promise.all([
        api<AttendanceData>(`/classes/${classId}/attendance?day=${day}`),
        student
          ? Promise.resolve([])
          : api<{ id: number; name: string }[]>(`/classes/${classId}/roster`),
        api<typeof history>("/attendance/history"),
      ]);
      if (sequence !== requestSequence.current) return;
      setData(a);
      setRoster(r);
      setAbsent(
        a.records.filter((x) => x.status === "absent").map((x) => x.student_id),
      );
      setHistory(h);
    } catch (e) {
      if (sequence === requestSequence.current) setError((e as Error).message);
    } finally {
      if (sequence === requestSequence.current) setLoading(false);
    }
  };
  useEffect(() => {
    void load();
    return () => {
      requestSequence.current++;
    };
  }, [classId, day, student]);
  const exportCSV = () => {
    const rows = history.filter((h) => h.class_id === Number(classId));
    const csv =
      "Date,Student ID,Status\n" +
      rows.map((h) => `${h.day},${h.student_id},${h.status}`).join("\n");
    const url = URL.createObjectURL(new Blob([csv], { type: "text/csv" }));
    const a = document.createElement("a");
    a.href = url;
    a.download = "attendance.csv";
    a.click();
    URL.revokeObjectURL(url);
  };
  return (
    <>
      <PageHeading
        eyebrow="A QUICK ROLL CALL"
        title={student ? "Your attendance" : "Everyone accounted for."}
        description={
          student
            ? "Your own attendance, with a clear view of each day."
            : "Everyone starts present. Tap a student to mark an absence."
        }
        action={
          <button
            className="button secondary"
            onClick={exportCSV}
            disabled={!history.length}
          >
            <Download size={16} />
            Export history
          </button>
        }
      />
      <ErrorMessage error={error} />
      <section className="panel">
        <div className="filter-bar">
          <label>
            Class
            <select
              value={classId}
              onChange={(e) => setClassId(e.target.value)}
            >
              {classes.map((c) => (
                <option value={c.id} key={c.id}>
                  {c.name}
                </option>
              ))}
            </select>
          </label>
          <label>
            Date
            <input
              type="date"
              value={day}
              max={indiaDate()}
              onChange={(e) => setDay(e.target.value)}
              required
            />
          </label>
          {data && (
            <span className={`badge ${data.saved ? "green" : "amber"}`}>
              {data.saved ? "Saved attendance" : "Not marked yet"}
            </span>
          )}
        </div>
        {loading ? (
          <Empty
            title="Loading attendance…"
            description="Getting the selected classroom."
          />
        ) : student ? (
          <div className="student-attendance">
            <CalendarCheck size={36} />
            <h2>{data?.records[0]?.status || "Not marked yet"}</h2>
            <p>{day} · Your teacher manages this attendance record.</p>
          </div>
        ) : roster.length ? (
          <>
            <div className="roster-summary">
              <strong>
                {roster.length - absent.length} present{" "}
                <span>/ {roster.length} students</span>
              </strong>
              <span>{absent.length} absent</span>
            </div>
            <div className="roster-grid">
              {roster.map((s, i) => (
                <button
                  key={s.id}
                  aria-pressed={!absent.includes(s.id)}
                  className={`roster-student ${absent.includes(s.id) ? "is-absent" : ""}`}
                  onClick={() =>
                    setAbsent((prev) =>
                      prev.includes(s.id)
                        ? prev.filter((id) => id !== s.id)
                        : [...prev, s.id],
                    )
                  }
                >
                  <span className="roll-number">
                    {String(i + 1).padStart(2, "0")}
                  </span>
                  <span className="avatar">
                    {s.name
                      .split(" ")
                      .map((n) => n[0])
                      .join("")}
                  </span>
                  <strong>{s.name}</strong>
                  <span className="attendance-indicator">
                    {absent.includes(s.id) ? (
                      <X size={16} />
                    ) : (
                      <Check size={16} />
                    )}
                  </span>
                  <small>{absent.includes(s.id) ? "Absent" : "Present"}</small>
                </button>
              ))}
            </div>
            {data?.saved && (
              <label className="mt">
                Reason for correction
                <textarea
                  value={reason}
                  onChange={(e) => setReason(e.target.value)}
                  minLength={5}
                  placeholder="Explain why this attendance is changing"
                />
              </label>
            )}
            <div className="panel-footer">
              <p>
                <CalendarCheck size={15} />{" "}
                {data?.saved
                  ? "Corrections are recorded in the audit log."
                  : "Review your roll call before saving."}
              </p>
              <button
                className="button"
                disabled={
                  busy || !data || (data.saved && reason.trim().length < 5)
                }
                onClick={() => setConfirm(true)}
              >
                <Save size={16} />
                {data?.saved ? "Review correction" : "Review & save"}
              </button>
            </div>
          </>
        ) : (
          <Empty
            title="No students in this class yet"
            description="A school administrator can create a class with student accounts."
          />
        )}
      </section>
      <section className="panel mt">
        <div className="section-heading">
          <h2>Attendance history</h2>
          <span className="subtle">Selected class · latest 1,000 records</span>
        </div>
        <div className="table-scroll">
          <table>
            <thead>
              <tr>
                <th>Date</th>
                {!student && <th>Student</th>}
                <th>Status</th>
              </tr>
            </thead>
            <tbody>
              {history
                .filter((h) => h.class_id === Number(classId))
                .slice(0, 60)
                .map((h, i) => (
                  <tr key={i}>
                    <td>{h.day}</td>
                    {!student && (
                      <td>
                        {roster.find((s) => s.id === h.student_id)?.name ||
                          `Student ${h.student_id}`}
                      </td>
                    )}
                    <td>
                      <span
                        className={`badge ${h.status === "present" ? "green" : "amber"}`}
                      >
                        {h.status}
                      </span>
                    </td>
                  </tr>
                ))}
            </tbody>
          </table>
        </div>
      </section>
      <Modal
        open={confirm}
        onOpenChange={setConfirm}
        title="Ready to save this roll call?"
        description={`${day} · ${classes.find((c) => c.id === Number(classId))?.name}`}
      >
        <div className="confirmation-counts">
          <strong>
            {roster.length - absent.length}
            <small>Present</small>
          </strong>
          <strong>
            {absent.length}
            <small>Absent</small>
          </strong>
        </div>
        <p>
          {absent.length
            ? `Absent: ${roster
                .filter((s) => absent.includes(s.id))
                .map((s) => s.name)
                .join(", ")}`
            : "All students are marked present."}
        </p>
        <button
          className="button full mt"
          disabled={busy}
          onClick={async () => {
            setBusy(true);
            try {
              await post(`/classes/${classId}/attendance`, {
                day,
                absent_ids: absent,
                confirmed: true,
                expected_version: data?.version,
                correction_reason: reason,
              });
              setConfirm(false);
              setReason("");
              notice("Attendance saved. A little more time for teaching.");
              await load();
            } catch (e) {
              setConfirm(false);
              setError((e as Error).message);
            } finally {
              setBusy(false);
            }
          }}
        >
          {busy ? "Saving…" : "Confirm & save attendance"}
        </button>
      </Modal>
    </>
  );
}
