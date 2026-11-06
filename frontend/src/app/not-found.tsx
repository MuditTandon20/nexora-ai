import Link from "next/link";
export default function NotFound() {
  return (
    <main className="loading-page">
      <h1>A little off the path.</h1>
      <p>This page could not be found.</p>
      <Link href="/app" className="button">
        Back to your workspace
      </Link>
    </main>
  );
}
