export type User = {
  id: number;
  name: string;
  email: string;
  role: "admin" | "teacher" | "student";
  school_id: number;
};
export type ClassInfo = {
  id: number;
  name: string;
  grade: number;
  students: number;
};
export type Subject = { id: number; name: string };
let csrfToken = "";
export function setCsrf(value: string) {
  csrfToken = value;
}
export async function api<T>(
  path: string,
  options: RequestInit = {},
): Promise<T> {
  const headers = new Headers(options.headers);
  if (!(options.body instanceof FormData))
    headers.set("Content-Type", "application/json");
  if (csrfToken) headers.set("X-CSRF-Token", csrfToken);
  const response = await fetch(`/api${path}`, {
    ...options,
    headers,
    credentials: "same-origin",
    cache: "no-store",
  });
  if (!response.ok) {
    const data = await response
      .json()
      .catch(() => ({ detail: "The server could not complete this request" }));
    throw new Error(
      typeof data.detail === "string"
        ? data.detail
        : data.detail?.map((e: { msg: string }) => e.msg).join("; ") ||
            "Request failed",
    );
  }
  return response.json();
}
export function post<T>(path: string, data: unknown = {}): Promise<T> {
  return api<T>(path, { method: "POST", body: JSON.stringify(data) });
}
export function indiaDate() {
  return new Intl.DateTimeFormat("en-CA", { timeZone: "Asia/Kolkata" }).format(
    new Date(),
  );
}
export function dateLabel(value: string) {
  return new Date(value + "T12:00:00").toLocaleDateString("en-IN", {
    day: "numeric",
    month: "short",
  });
}
