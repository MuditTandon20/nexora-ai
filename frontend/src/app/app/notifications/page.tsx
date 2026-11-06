"use client";
import { useEffect, useState } from "react";
import { Bell, Check } from "lucide-react";
import { api, post } from "@/lib/api";
import { Empty, ErrorMessage, PageHeading } from "@/components/workspace";
type Notification = {
  id: number | string;
  title: string;
  body: string;
  read: boolean;
  created_at: string;
};
export default function Notifications() {
  const [items, setItems] = useState<Notification[]>([]);
  const [error, setError] = useState("");
  const [busy, setBusy] = useState(false);
  const load = () => api<Notification[]>("/notifications").then(setItems);
  useEffect(() => {
    load().catch((e) => setError(e.message));
  }, []);
  return (
    <>
      <PageHeading
        eyebrow="AROUND YOUR SCHOOL"
        title="A little heads-up."
        description="Assignments, chapter notes, challenges, and news from your school community."
      />
      <ErrorMessage error={error} />
      {items.map((n) => (
        <article
          className={`panel notification-card ${n.read ? "read" : ""}`}
          key={n.id}
        >
          <span className={`icon-tile ${n.read ? "blue" : "green"}`}>
            <Bell size={20} />
          </span>
          <div>
            <h2>{n.title}</h2>
            <p>{n.body}</p>
            {!n.read && (
              <button
                className="text-link"
                disabled={busy}
                onClick={async () => {
                  setBusy(true);
                  try {
                    await post(`/notifications/${n.id}/read`);
                    await load();
                  } catch (e) {
                    setError((e as Error).message);
                  } finally {
                    setBusy(false);
                  }
                }}
              >
                <Check size={14} />
                Mark as read
              </button>
            )}
          </div>
        </article>
      ))}
      {!items.length && (
        <Empty
          title="A quiet moment"
          description="Updates from your school will appear here."
        />
      )}
    </>
  );
}
