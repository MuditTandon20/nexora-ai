# Student privacy and pilot readiness

Nexora is a pilot MVP. School authorization, consent and compliance review remain the responsibility of the operator and school before real children use it. This document defines operational work, not legal advice or a claim of regulatory compliance.

## Data handling

- Collect only school, name, school-issued email/account, role, class membership and necessary learning activity. No dates of birth, home addresses, advertising IDs or payment data are required.
- Passwords are Argon2 hashes. Session cookies are HttpOnly, SameSite=Lax and Secure in production. Store session-token hashes only.
- Backend policy isolates schools/classes. Students see their own private submissions/attendance/attempts. Teachers access assigned classes. Admins have school-wide access.
- Model requests contain source excerpts, grade, language and the current question. Profile metadata and conversation history are not added. Do not upload identifying student data into approved chapter notes or include it in questions. Provider request retention must be reviewed separately.
- Nexora stores AI metadata/errors but not tutor conversation text. Browser chat exists only in page memory; changing chapter or leaving/reloading clears it. No training pipeline or advertising integration exists in this codebase.
- Private PDF objects have random server-generated names; students cannot choose storage paths. Authorized downloads are attachments. S3 access is server-side.

## Retention procedure to agree before a pilot

The school must approve a retention schedule rather than silently inheriting a universal period. Suggested operational starting points for review: expire sessions after 12 hours; delete expired session rows daily; keep content/attendance/submissions only for the school's authorized academic retention period; keep diagnostic AI metadata 30 days; keep audit data only for a documented operational need. These are proposed defaults, not an automatically running deletion job.

Operator procedure:

1. Verify the requester with the school administrator. Never accept a browser-supplied school/student ID as authorization.
2. Record the approved access/correction/deletion request in a restricted school log with an owner and deadline.
3. Export only the verified school's/user's records from the database. Have a second authorized operator review the filter, then share through a school-approved private channel.
4. For deletion, revoke that user's sessions and deactivate access first. Use a reviewed transaction to delete dependent submissions, attendance, attempts, notifications, enrollments, AI metadata and account records according to the agreed retention/audit policy. Referential constraints deliberately prevent casual destructive cascades. A generalized self-service deletion feature is not built.
5. Delete obsolete private storage objects when their material records are removed; check for upload/database failures that left orphan objects.
6. Apply the policy to exports, logs, provider systems and backups. Document backup expiry so deleted records aren't silently restored. Confirm completion to the verified school contact.

No scheduler is installed for retention. Automate the approved procedure and test it with synthetic data before enrolling real users. Do not claim deletion is complete until storage and backup handling are verified.

## Pilot release gate

- Written school authorization, guardian/child notices where applicable, and defined support/deletion contacts.
- Private staging review of role permissions and cross-school access on actual PostgreSQL.
- Disable/remove synthetic demo accounts from the production database. Bootstrap fresh school accounts privately.
- HTTPS, exact-origin/CSRF checks, secure cookies and credential rotation verified in the deployed topology.
- Private S3 permissions/encryption/backup behavior tested, upload malware handling and isolated PDF parsing implemented.
- Restore test completed and documented. Retention jobs and deletion/export procedures validated.
- Approved model/data-processing agreement, age-appropriate safety evaluation in English/Hindi, prompt-injection checks and provider-side spend limits.
- Human teacher review of factual correctness, source alignment, grade level and explanations. Citation validation alone cannot establish these qualities.
- Keyboard/screen-reader and low-cost Android testing, accessibility contrast review, slower-network performance measurements.
- Monitoring/incident ownership and a shared rate limiter before multiple API instances.

Future work includes parent access, handwritten notebook assistance, prerequisite mapping, adaptive learning, voice and advanced analytics. These are intentionally outside the MVP.
