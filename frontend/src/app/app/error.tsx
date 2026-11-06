"use client";
export default function WorkspaceError({ reset }: { reset: () => void }) {
  return (
    <div className="panel empty" role="alert">
      <h2>This page needs a fresh start.</h2>
      <p>
        Your saved school records are still on the server. Try loading the page
        again.
      </p>
      <button className="button" onClick={reset}>
        Try again
      </button>
    </div>
  );
}
