"use client";
import { createContext, useContext, useEffect, useState } from "react";
import { usePathname, useRouter } from "next/navigation";
import Link from "next/link";
import {
  Bell,
  BookOpen,
  CalendarCheck,
  ChevronDown,
  ChevronRight,
  CircleHelp,
  GraduationCap,
  LayoutDashboard,
  Leaf,
  LogOut,
  Menu,
  Settings,
  ShieldCheck,
  Sparkles,
  Swords,
  TrendingUp,
  X,
  ClipboardList,
} from "lucide-react";
import * as Dialog from "@radix-ui/react-dialog";
import { api, post, setCsrf, User, ClassInfo, Subject } from "@/lib/api";

type Context = {
  user: User;
  classes: ClassInfo[];
  subjects: Subject[];
  refresh: () => Promise<void>;
  notice: (message: string) => void;
};
const WorkspaceContext = createContext<Context | null>(null);
export function useWorkspace() {
  const value = useContext(WorkspaceContext);
  if (!value) throw new Error("Workspace unavailable");
  return value;
}
export function Modal({
  open,
  onOpenChange,
  title,
  description,
  children,
}: {
  open: boolean;
  onOpenChange: (v: boolean) => void;
  title: string;
  description: string;
  children: React.ReactNode;
}) {
  return (
    <Dialog.Root open={open} onOpenChange={onOpenChange}>
      <Dialog.Portal>
        <Dialog.Overlay className="modal-overlay" />
        <Dialog.Content className="modal">
          <Dialog.Title>{title}</Dialog.Title>
          <Dialog.Description>{description}</Dialog.Description>
          <Dialog.Close className="icon-button modal-close" aria-label="Close">
            <X size={20} />
          </Dialog.Close>
          {children}
        </Dialog.Content>
      </Dialog.Portal>
    </Dialog.Root>
  );
}
export function PageHeading({
  eyebrow,
  title,
  description,
  action,
}: {
  eyebrow: string;
  title: string;
  description: string;
  action?: React.ReactNode;
}) {
  return (
    <div className="page-heading">
      <div>
        <span className="eyebrow">{eyebrow}</span>
        <h1>{title}</h1>
        <p>{description}</p>
      </div>
      {action}
    </div>
  );
}
export function Empty({
  title,
  description,
}: {
  title: string;
  description: string;
}) {
  return (
    <div className="empty">
      <BookOpen size={30} />
      <h3>{title}</h3>
      <p>{description}</p>
    </div>
  );
}
export function ErrorMessage({ error }: { error: string }) {
  return error ? (
    <div className="alert" role="alert">
      {error}
    </div>
  ) : null;
}
export function ClassSubjectFields({
  classId,
  setClassId,
  subjectId,
  setSubjectId,
}: {
  classId: string;
  setClassId: (v: string) => void;
  subjectId: string;
  setSubjectId: (v: string) => void;
}) {
  const { classes, subjects } = useWorkspace();
  return (
    <div className="form-row">
      <label>
        Class
        <select
          required
          value={classId}
          onChange={(e) => setClassId(e.target.value)}
        >
          <option value="">Select class</option>
          {classes.map((c) => (
            <option key={c.id} value={c.id}>
              {c.name}
            </option>
          ))}
        </select>
      </label>
      <label>
        Subject
        <select
          required
          value={subjectId}
          onChange={(e) => setSubjectId(e.target.value)}
        >
          <option value="">Select subject</option>
          {subjects.map((s) => (
            <option key={s.id} value={s.id}>
              {s.name}
            </option>
          ))}
        </select>
      </label>
    </div>
  );
}

export default function Workspace({ children }: { children: React.ReactNode }) {
  const router = useRouter();
  const path = usePathname();
  const [user, setUser] = useState<User | null>(null);
  const [school, setSchool] = useState("");
  const [classes, setClasses] = useState<ClassInfo[]>([]);
  const [subjects, setSubjects] = useState<Subject[]>([]);
  const [toast, setToast] = useState("");
  const [menu, setMenu] = useState(false);
  const [error, setError] = useState("");
  const [settings, showSettings] = useState(false);
  const [passwordError, setPasswordError] = useState("");
  const [busy, setBusy] = useState(false);
  const refresh = async () => {
    const [c, s] = await Promise.all([
      api<ClassInfo[]>("/classes"),
      api<Subject[]>("/subjects"),
    ]);
    setClasses(c);
    setSubjects(s);
  };
  useEffect(() => {
    api<{ user: User; school: string; csrf_token: string }>("/auth/me")
      .then(async (data) => {
        setCsrf(data.csrf_token);
        setUser(data.user);
        setSchool(data.school);
        await refresh();
      })
      .catch((e) => {
        if (e.message === "Please sign in") router.replace("/login");
        else setError(e.message);
      });
  }, [router]);
  useEffect(() => {
    if (!toast) return;
    const timer = setTimeout(() => setToast(""), 5000);
    return () => clearTimeout(timer);
  }, [toast]);
  if (!user)
    return (
      <main className="loading-page">
        <span className="brand-icon">N</span>
        <p>{error || "Opening your school workspace…"}</p>
        {error && (
          <Link href="/login" className="button">
            Back to sign in
          </Link>
        )}
      </main>
    );
  const student = user.role === "student";
  const nav = [
    { label: "Overview", href: "/app", icon: LayoutDashboard },
    ...(user.role === "admin"
      ? [{ label: "School & people", href: "/app/admin", icon: GraduationCap }]
      : []),
    { label: "Attendance", href: "/app/attendance", icon: CalendarCheck },
    { label: "Study materials", href: "/app/notes", icon: BookOpen },
    { label: "Assignments", href: "/app/assignments", icon: ClipboardList },
    ...(!student
      ? [{ label: "AI learning studio", href: "/app/studio", icon: Sparkles }]
      : [{ label: "Study Buddy", href: "/app/buddy", icon: Sparkles }]),
    { label: "Nexora Arena", href: "/app/arena", icon: Swords },
    ...(!student
      ? [{ label: "Class insights", href: "/app/analytics", icon: TrendingUp }]
      : []),
  ];
  return (
    <WorkspaceContext.Provider
      value={{ user, classes, subjects, refresh, notice: setToast }}
    >
      <div className={`workspace ${menu ? "menu-open" : ""}`}>
        <a href="#main" className="skip-link">
          Skip to content
        </a>
        <aside className="sidebar">
          <Link href="/app" className="brand">
            <span className="brand-icon">
              N<span>✦</span>
            </span>
            nexora<span className="ai-tag">AI</span>
          </Link>
          <div className="school-switch">
            <span className="school-mark">
              <GraduationCap size={21} />
            </span>
            <div>
              <strong>{school.split(" · ")[0]}</strong>
              <small>
                {user.role === "admin"
                  ? "School workspace"
                  : student
                    ? "Student workspace"
                    : "Teacher workspace"}
              </small>
            </div>
            <ChevronDown size={14} />
          </div>
          <span className="nav-caption">YOUR WORKSPACE</span>
          <nav>
            {nav.map((item) => (
              <Link
                onClick={() => setMenu(false)}
                href={item.href}
                key={item.href}
                className={`nav-item ${path === item.href ? "active" : ""}`}
              >
                <item.icon size={19} />
                {item.label}
                {item.href === "/app/studio" && (
                  <span className="new-tag">AI</span>
                )}
                {item.href === "/app/arena" && <span className="arena-dot" />}
              </Link>
            ))}
          </nav>
          <div className="sidebar-bottom">
            <div className="sidebar-note">
              <Leaf size={20} />
              <strong>
                A little less busy.
                <br />A little more possibility.
              </strong>
              <p>Make room for what matters.</p>
            </div>
            <button className="nav-item" onClick={() => showSettings(true)}>
              <Settings size={18} />
              Account settings
            </button>
            <Link href="/app/help" className="nav-item">
              <CircleHelp size={18} />
              Help & privacy
            </Link>
            <button className="user-profile" onClick={() => showSettings(true)}>
              <span className="avatar">
                {user.name
                  .split(" ")
                  .map((n) => n[0])
                  .slice(0, 2)
                  .join("")}
              </span>
              <span>
                <strong>{user.name}</strong>
                <small>
                  {user.role === "admin"
                    ? "School administrator"
                    : user.role === "teacher"
                      ? "Teacher"
                      : "Student"}
                </small>
              </span>
              <ChevronRight size={16} />
            </button>
          </div>
        </aside>
        {menu && (
          <button
            className="menu-backdrop"
            onClick={() => setMenu(false)}
            aria-label="Close navigation"
          />
        )}
        <div className="workspace-main">
          <header className="topbar">
            <div>
              <button
                className="icon-button mobile-menu"
                aria-label="Open navigation"
                onClick={() => setMenu(!menu)}
              >
                <Menu size={22} />
              </button>
              <span className="breadcrumb">
                Workspace <ChevronRight size={13} />{" "}
                <strong>
                  {nav.find((n) => n.href === path)?.label || "Nexora"}
                </strong>
              </span>
            </div>
            <div className="topbar-actions">
              <span className="school-session">
                <span /> SCHOOL WORKSPACE
              </span>
              <Link
                className="icon-button"
                href="/app/notifications"
                aria-label="Notifications"
              >
                <Bell size={19} />
              </Link>
              <span className="avatar small">{user.name[0]}</span>
            </div>
          </header>
          <main id="main" className="main-content">
            {children}
          </main>
          <footer className="app-footer">
            <span>Made for the moments that matter.</span>
            <span>
              Nexora AI <span className="footer-star">✦</span>
            </span>
          </footer>
        </div>
        {toast && (
          <div className="toast" role="status">
            <ShieldCheck size={18} />
            {toast}
          </div>
        )}
        <Modal
          open={settings}
          onOpenChange={showSettings}
          title="Your account"
          description={`${user.email} · ${user.role}`}
        >
          <form
            onSubmit={async (e) => {
              e.preventDefault();
              setBusy(true);
              setPasswordError("");
              const f = new FormData(e.currentTarget);
              try {
                await post("/auth/password", {
                  current_password: f.get("current"),
                  new_password: f.get("new"),
                });
                router.replace("/login");
              } catch (e) {
                setPasswordError((e as Error).message);
              } finally {
                setBusy(false);
              }
            }}
          >
            <label>
              Current password
              <input
                name="current"
                type="password"
                autoComplete="current-password"
                required
              />
            </label>
            <label>
              New password
              <input
                name="new"
                type="password"
                minLength={12}
                maxLength={128}
                autoComplete="new-password"
                required
              />
              <small>
                At least 12 characters. All sessions will be signed out.
              </small>
            </label>
            <ErrorMessage error={passwordError} />
            <button disabled={busy} className="button">
              Change password
            </button>
          </form>
          <button
            disabled={busy}
            className="button secondary full mt"
            onClick={async () => {
              setBusy(true);
              try {
                await post("/auth/logout");
                router.replace("/login");
              } catch (e) {
                setPasswordError((e as Error).message);
                setBusy(false);
              }
            }}
          >
            <LogOut size={16} />
            Sign out
          </button>
        </Modal>
      </div>
    </WorkspaceContext.Provider>
  );
}
