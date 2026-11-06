import { test, expect, Page } from "@playwright/test";

test("blank class names are rejected and normalized class creation remains usable", async ({
  page,
}) => {
  await login(page, "admin");
  await page.getByRole("link", { name: "School & people" }).click();
  await page.getByRole("button", { name: "Create class", exact: true }).click();
  const dialog = page.getByRole("dialog");
  await dialog.getByLabel("Class name").fill("    ");
  await dialog
    .getByRole("button", { name: "Create class", exact: true })
    .click();
  await expect(dialog.getByRole("alert")).toBeVisible();
  const name = `Stabilization ${Date.now()}`;
  await dialog.getByLabel("Class name").fill(`  ${name}  `);
  await dialog
    .getByRole("button", { name: "Create class", exact: true })
    .click();
  await expect(page.getByRole("heading", { name, exact: true })).toBeVisible();
});

async function login(page: Page, role: string) {
  await page.goto("/login");
  await page.getByLabel("School email").fill(`${role}@nexora.demo`);
  await page.getByLabel("Password", { exact: true }).fill("NexoraDemo!2026");
  await page.getByRole("button", { name: "Sign in to Nexora" }).click();
  await expect(
    page.getByRole("heading", { name: /a good day|ready for a little/i }),
  ).toBeVisible();
}

test("AI-disabled teacher can use school pages without inference requests", async ({
  page,
}) => {
  const errors: string[] = [];
  const inferenceRequests: string[] = [];
  page.on("pageerror", (error) => errors.push(error.message));
  page.on("request", (request) => {
    if (/\/api\/ai\/(generate|tutor)$/.test(request.url()))
      inferenceRequests.push(request.url());
  });
  await login(page, "teacher");
  const status = await page.request.get("/api/ai/status");
  expect((await status.json()).configured).toBe(false);
  for (const path of [
    "attendance",
    "notes",
    "assignments",
    "analytics",
    "notifications",
    "studio",
  ]) {
    await page.goto(`/app/${path}`);
    await expect(page.locator("main h1")).toBeVisible();
    await expect(page.getByText("Please sign in", { exact: true })).toHaveCount(
      0,
    );
  }
  await expect(page.getByText(/AI is not connected/)).toBeVisible();
  await expect(
    page.getByRole("button", { name: "Generate learning pack" }),
  ).toBeDisabled();
  expect(errors).toEqual([]);
  expect(inferenceRequests).toEqual([]);
});

test("AI-disabled student can save a complete five-question challenge", async ({
  page,
}) => {
  const errors: string[] = [];
  page.on("pageerror", (error) => errors.push(error.message));
  await login(page, "student");
  await page.getByRole("link", { name: "Nexora Arena", exact: true }).click();
  await page
    .getByLabel("Choose class challenge")
    .selectOption({ label: "The green world challenge" });
  await page.getByRole("button", { name: "Take challenge" }).click();
  const answers = [
    "Photosynthesis",
    "Chlorophyll",
    "Oxygen",
    "Roots",
    "Glucose",
  ];
  for (let index = 0; index < answers.length; index++) {
    await page
      .locator(".answer-options")
      .getByRole("button", { name: new RegExp(`${answers[index]}$`) })
      .click();
    await page.getByRole("button", { name: "Check my answer" }).click();
    await expect(
      page.getByRole("status").filter({ has: page.getByRole("heading") }),
    ).toBeVisible();
    await page
      .getByRole("button", {
        name:
          index === answers.length - 1 ? "Complete challenge" : "Next question",
      })
      .click();
  }
  await expect(
    page.getByRole("heading", { name: "A little wiser than before." }),
  ).toBeVisible();
  await page
    .getByRole("button", { name: "Back to your learning space" })
    .click();
  await expect(
    page.getByRole("heading", { name: "Your practice journey" }),
  ).toBeVisible();
  await expect(
    page.getByRole("cell", { name: "5 / 5", exact: true }),
  ).toBeVisible();
  expect(errors).toEqual([]);
});

test("AI-disabled Study Buddy is explicit and makes no tutor calls", async ({
  page,
}) => {
  const calls: string[] = [];
  page.on("request", (request) => {
    if (request.url().endsWith("/api/ai/tutor")) calls.push(request.url());
  });
  await login(page, "student");
  await page.getByRole("link", { name: "Study Buddy", exact: true }).click();
  await expect(
    page.getByText(/has not connected an AI provider/),
  ).toBeVisible();
  await expect(
    page.getByRole("button", { name: "Ask Study Buddy" }),
  ).toBeDisabled();
  expect(calls).toEqual([]);
});
