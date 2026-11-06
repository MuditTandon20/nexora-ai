import { test, expect } from "@playwright/test";

test("teacher dashboard opens attendance, creation and pending review in context", async ({
  browser,
}) => {
  const context = await browser.newContext();
  const page = await context.newPage();
  const errors: string[] = [];
  page.on("pageerror", (e) => errors.push(e.message));
  await page.goto("/login");
  await page.getByLabel("School email").fill("teacher@nexora.demo");
  await page.getByLabel("Password", { exact: true }).fill("NexoraDemo!2026");
  await page.getByRole("button", { name: "Sign in to Nexora" }).click();
  await expect(
    page.getByRole("heading", { name: "Today’s classes" }),
  ).toBeVisible();
  const me = await (await page.request.get("/api/auth/me")).json();
  const classes = await (await page.request.get("/api/classes")).json();
  const subjects = await (await page.request.get("/api/subjects")).json();
  const selectedClass = classes.find(
    (c: { name: string }) => c.name === "Class 6 · A",
  );
  const title = `Dashboard review ${Date.now()}`;
  const response = await page.request.post("/api/homework", {
    headers: { "x-csrf-token": me.csrf_token },
    data: {
      class_id: selectedClass.id,
      subject_id: subjects[0].id,
      title,
      instructions: "Explain a synthetic classroom example.",
      due_date: new Date(Date.now() + 7 * 86400000).toISOString().slice(0, 10),
    },
  });
  expect(response.status()).toBe(201);
  const assignment = await response.json();
  const learner = await browser.newContext();
  const auth = await (
    await learner.request.post("/api/auth/login", {
      data: { email: "student@nexora.demo", password: "NexoraDemo!2026" },
    })
  ).json();
  expect(
    (
      await learner.request.post(`/api/homework/${assignment.id}/submit`, {
        headers: { "x-csrf-token": auth.csrf_token },
        data: { answer: "Synthetic student work ready for review." },
      })
    ).status(),
  ).toBe(200);
  await learner.close();
  await page.goto("/app");
  await page
    .locator(`a[href="/app/attendance?classId=${selectedClass.id}"]`)
    .click();
  await expect(
    page.getByRole("combobox", { name: "Class", exact: true }),
  ).toHaveValue(String(selectedClass.id));
  await page.goto("/app");
  await page
    .locator(`a[href="/app/assignments?review=${assignment.id}"]`)
    .click();
  await expect(
    page.getByRole("dialog").getByRole("heading", { name: title, exact: true }),
  ).toBeVisible();
  await expect(
    page
      .getByRole("dialog")
      .getByText("Synthetic student work ready for review."),
  ).toBeVisible();
  await page
    .getByRole("dialog")
    .getByRole("button", { name: "Close", exact: true })
    .click();
  await page.goto("/app");
  await page
    .locator(".quick-actions")
    .getByRole("link", { name: /Create an assignment/ })
    .click();
  await expect(
    page
      .getByRole("dialog")
      .getByRole("heading", { name: "A new learning opportunity" }),
  ).toBeVisible();
  await page
    .getByRole("dialog")
    .getByRole("button", { name: "Close", exact: true })
    .click();
  await page.goto("/app");
  await page
    .locator(".quick-actions")
    .getByRole("link", { name: /Share study material/ })
    .click();
  await expect(
    page
      .getByRole("dialog")
      .getByRole("heading", { name: "Add a little knowledge" }),
  ).toBeVisible();
  expect(errors).toEqual([]);
  await context.close();
});
