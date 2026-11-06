import { PageHeading } from "@/components/workspace";
export default function Help() {
  return (
    <>
      <PageHeading
        eyebrow="A THOUGHTFUL SCHOOL SPACE"
        title="A little guidance."
        description="How your school workspace works, and how it treats your information."
      />
      <article className="panel help-copy">
        <h2>Start with your school</h2>
        <p>
          Your school administrator creates accounts and classes. Teachers
          manage attendance, publish learning materials, and review assignments.
          Students see only the classes they belong to and their own private
          work.
        </p>
        <h2>Your daily workflow</h2>
        <ul>
          <li>
            Administrators: open School & people to create accounts and classes,
            then choose a teacher and students.
          </li>
          <li>
            Teachers: select a class and date in Attendance, tap absences, then
            review and confirm. Changes to saved attendance require a reason.
          </li>
          <li>
            Teachers: add a chapter in Study materials, review it, and approve
            it for students. Create an assignment and review submissions when
            they arrive.
          </li>
          <li>
            Students: open Assignments to submit written work. Open Arena to
            practise with approved quizzes and flashcards.
          </li>
        </ul>
        <h2>AI, with teachers in control</h2>
        <p>
          AI learning tools use an approved chapter. They may make mistakes.
          Teachers check and approve generated learning packs; students should
          check Study Buddy’s quoted evidence and ask their teacher if something
          seems wrong. Quiz results are practice feedback, never final academic
          grades.
        </p>
        <h2>Your privacy</h2>
        <p>
          This workspace has no advertisements or public individual student
          rankings. Study Buddy messages remain in the current browser page’s
          memory; the backend records request counts, model version, latency,
          and errors without storing conversation text. Your question and
          selected chapter excerpts are sent to the model provider configured by
          your school. Please do not include personal details in your questions.
        </p>
        <h2>Access, corrections and deletion</h2>
        <p>
          Contact your school administrator for an account, an attendance
          correction, or a request to access or delete information. Your school
          is responsible for obtaining authorization, choosing an approved model
          provider, and setting retention periods before using this platform
          with real students.
        </p>
        <h2>Local demonstration</h2>
        <p>
          Seeded demo records use synthetic names and learning data. Do not put
          real student information in the demo. Your school’s pilot should begin
          only after access, privacy, backups, and reliability have been
          checked.
        </p>
      </article>
    </>
  );
}
