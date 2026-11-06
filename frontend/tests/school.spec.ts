import { test, expect, Page } from "@playwright/test";

test("offline fallback caches no school data", async ({ page, context }) => {
  await page.goto("/login");
  await page.evaluate(() => navigator.serviceWorker.ready);
  await page.reload();
  const cached = await page.evaluate(async () => {
    const names = await caches.keys();
    return (
      await Promise.all(
        names.map(async (n) =>
          (await (await caches.open(n)).keys()).map(
            (r) => new URL(r.url).pathname,
          ),
        ),
      )
    ).flat();
  });
  expect(
    cached.every((p) => p === "/offline.html" || p === "/icon.svg"),
  ).toBeTruthy();
  await context.setOffline(true);
  await page.goto("/app/help");
  await expect(
    page.getByRole("heading", { name: "A little pause." }),
  ).toBeVisible();
  await context.setOffline(false);
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

test("admin creates class → teacher marks attendance → student sees own status", async ({
  browser,
}) => {
  const errors: string[] = [];
  const admin = await browser.newContext();
  const teacher = await browser.newContext();
  const student = await browser.newContext();
  const ap = await admin.newPage();
  const tp = await teacher.newPage();
  const sp = await student.newPage();
  for (const p of [ap, tp, sp])
    p.on("pageerror", (e) => errors.push(e.message));
  await login(ap, "admin");
  await ap.getByRole("link", { name: "School & people" }).click();
  await ap.getByRole("button", { name: "Create class", exact: true }).click();
  const dialog = ap.getByRole("dialog");
  const className = `Pilot ${Date.now()}`;
  await dialog.getByLabel("Class name").fill(className);
  await dialog
    .getByRole("combobox", { name: "Grade", exact: true })
    .selectOption("6");
  await dialog.getByLabel("Meera Iyer").check();
  await dialog.getByLabel("Aarav Mehta").check();
  await dialog.getByLabel("Diya Kapoor").check();
  await dialog
    .getByRole("button", { name: "Create class", exact: true })
    .click();
  await expect(ap.getByRole("heading", { name: className })).toBeVisible();
  await login(tp, "teacher");
  await tp.getByRole("link", { name: "Attendance", exact: true }).click();
  await tp
    .getByRole("combobox", { name: "Class", exact: true })
    .selectOption({ label: className });
  await tp.getByRole("button", { name: /Diya Kapoor/ }).click();
  await tp.getByRole("button", { name: "Review & save" }).click();
  await expect(
    tp.getByRole("dialog").getByText("Absent: Diya Kapoor"),
  ).toBeVisible();
  await tp.getByRole("button", { name: "Confirm & save attendance" }).click();
  await expect(tp.getByText("Saved attendance", { exact: true })).toBeVisible();
  await login(sp, "student");
  await sp.getByRole("link", { name: "Attendance", exact: true }).click();
  await sp
    .getByRole("combobox", { name: "Class", exact: true })
    .selectOption({ label: className });
  await expect(
    sp.getByRole("heading", { name: "present", exact: true }),
  ).toBeVisible();
  await expect(sp.getByText("Diya Kapoor")).toHaveCount(0);
  expect(errors).toEqual([]);
  await admin.close();
  await teacher.close();
  await student.close();
});

test("teacher publishes notes and homework → student submits → teacher reviews", async ({
  browser,
}) => {
  const teacher = await browser.newContext();
  const student = await browser.newContext();
  const tp = await teacher.newPage();
  const sp = await student.newPage();
  const suffix = Date.now();
  const title = `Light and leaves ${suffix}`;
  const assignment = `A little plant practice ${suffix}`;
  await login(tp, "teacher");
  await tp.getByRole("link", { name: "Study materials", exact: true }).click();
  await tp.getByRole("button", { name: "Add study material" }).click();
  let dialog = tp.getByRole("dialog");
  await dialog
    .getByRole("combobox", { name: "Class", exact: true })
    .selectOption({ label: "Class 6 · A" });
  await dialog
    .getByRole("combobox", { name: "Subject", exact: true })
    .selectOption({ label: "Science" });
  await dialog.getByLabel("Lesson title").fill(title);
  await dialog
    .getByLabel("Chapter content")
    .fill(
      "Plants make food through photosynthesis. Chlorophyll captures sunlight. Roots absorb water from the soil. Oxygen is released during photosynthesis.",
    );
  await dialog.getByRole("button", { name: "Save draft material" }).click();
  const card = tp
    .locator("article")
    .filter({ has: tp.getByRole("heading", { name: title, exact: true }) });
  await card.getByRole("button", { name: "Approve", exact: true }).click();
  await expect(card.getByText("Approved", { exact: true })).toBeVisible();
  await tp.getByRole("link", { name: "Assignments", exact: true }).click();
  await tp
    .getByRole("button", { name: "Create assignment", exact: true })
    .click();
  dialog = tp.getByRole("dialog");
  await dialog
    .getByRole("combobox", { name: "Class", exact: true })
    .selectOption({ label: "Class 6 · A" });
  await dialog
    .getByRole("combobox", { name: "Subject", exact: true })
    .selectOption({ label: "Science" });
  await dialog.getByLabel("Assignment title").fill(assignment);
  await dialog
    .getByLabel("What should students do?")
    .fill("Explain how plants make food using sunlight.");
  await dialog.getByLabel("Due date").fill("2026-12-20");
  await dialog
    .getByRole("button", { name: "Create assignment", exact: true })
    .click();
  await expect(
    tp.getByRole("heading", { name: assignment, exact: true }),
  ).toBeVisible();
  await login(sp, "student");
  await sp.getByRole("link", { name: "Study materials", exact: true }).click();
  await expect(
    sp.getByRole("heading", { name: title, exact: true }),
  ).toBeVisible();
  await sp.getByRole("link", { name: "Assignments", exact: true }).click();
  const studentCard = sp.locator("article").filter({
    has: sp.getByRole("heading", { name: assignment, exact: true }),
  });
  await studentCard.getByRole("button", { name: "Open assignment" }).click();
  await sp
    .getByLabel("Your thinking")
    .fill("Plants use sunlight, water and carbon dioxide to make glucose.");
  await sp.getByRole("button", { name: "Submit your work" }).click();
  await expect(
    studentCard.getByText("submitted", { exact: true }),
  ).toBeVisible();
  await tp.reload();
  const teacherCard = tp.locator("article").filter({
    has: tp.getByRole("heading", { name: assignment, exact: true }),
  });
  await teacherCard.getByRole("button", { name: "Review submissions" }).click();
  await tp.getByLabel("Your feedback").fill("Clear explanation. Nicely done.");
  await tp.getByRole("button", { name: "Save review" }).click();
  await expect(
    tp.getByRole("dialog").getByText("complete", { exact: true }),
  ).toBeVisible();
  await sp.reload();
  await studentCard.getByRole("button", { name: "Open assignment" }).click();
  await expect(
    sp.getByText("Clear explanation. Nicely done.", { exact: true }),
  ).toBeVisible();
  await teacher.close();
  await student.close();
});

test("mobile workspace and student challenge", async ({ page }) => {
  await page.setViewportSize({ width: 390, height: 844 });
  await login(page, "student");
  await page.getByRole("button", { name: "Open navigation" }).click();
  await page.getByRole("link", { name: "Nexora Arena", exact: true }).click();
  await expect(
    page.getByRole("heading", { name: /Small challenges/ }),
  ).toBeVisible();
  expect(
    await page.evaluate(
      () => document.documentElement.scrollWidth <= innerWidth,
    ),
  ).toBeTruthy();
  await page
    .getByLabel("Choose class challenge")
    .selectOption({ label: "The green world challenge" });
  await page.getByRole("button", { name: "Study pack", exact: true }).click();
  await expect(
    page.getByRole("heading", { name: "A little flashcard practice" }),
  ).toBeVisible();
  await page.getByRole("button", { name: /Flashcard 1/ }).click();
  await expect(
    page.getByRole("button", { name: /Flashcard 1: answer/ }),
  ).toBeVisible();
  await page
    .getByLabel("Try it in your own words")
    .fill("Trees help provide food and oxygen.");
  await page
    .getByRole("button", { name: "Compare with a sample explanation" })
    .click();
  await expect(
    page.getByText("One way to explain it", { exact: true }),
  ).toBeVisible();
});
