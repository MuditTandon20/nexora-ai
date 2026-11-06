import { chromium, expect } from "@playwright/test";
import fs from "node:fs";
import { performance } from "node:perf_hooks";

const base = process.env.DEMO_BASE_URL || "http://localhost:3001";
if (!["localhost", "127.0.0.1"].includes(new URL(base).hostname))
  throw new Error("Local synthetic demo only");
const browser = await chromium.launch({ headless: true });
try {
  const page = await browser.newPage({
    viewport: { width: 1440, height: 1100 },
  });
  await page.emulateMedia({ reducedMotion: "reduce" });
  const errors = [];
  page.on("pageerror", (e) => errors.push(e.message));
  await page.goto(`${base}/login`);
  await page.getByLabel("School email").fill("teacher@nexora.demo");
  await page.getByLabel("Password", { exact: true }).fill("NexoraDemo!2026");
  await page.getByRole("button", { name: "Sign in to Nexora" }).click();
  await expect(
    page.getByRole("heading", { name: "Today’s classes" }),
  ).toBeVisible();
  const me = await (await page.request.get(`${base}/api/auth/me`)).json();
  const ai = await (await page.request.get(`${base}/api/ai/status`)).json();
  if (
    !me.school.endsWith("· Demo") ||
    me.user.email !== "teacher@nexora.demo" ||
    ai.configured
  )
    throw new Error("Expected synthetic teacher demo with AI disabled");
  const overview = await (
    await page.request.get(`${base}/api/dashboard`)
  ).json();
  const target = overview.class_tasks.find((c) => c.name === "Class 7 · A");
  const assignment = overview.homework.find((h) => h.pending_review > 0);
  if (!target || !assignment)
    throw new Error("Run app.demo into a fresh local database first");
  const roster = await (
    await page.request.get(`${base}/api/classes/${target.class_id}/roster`)
  ).json();
  const tasks = [
    "Open Class 7 attendance",
    "Open new assignment form",
    "Open a waiting submission",
  ];
  const results = [];
  for (const task of tasks) {
    for (let trial = 0; trial < 3; trial++) {
      for (const path of trial % 2
        ? ["dashboard shortcut", "existing manual navigation"]
        : ["existing manual navigation", "dashboard shortcut"]) {
        await page.goto(`${base}/app`);
        await expect(
          page.getByRole("heading", { name: "Today’s classes" }),
        ).toBeVisible();
        await expect(
          page.locator(`a[href="/app/assignments?review=${assignment.id}"]`),
        ).toBeVisible();
        let actions = 0;
        const act = async (fn) => {
          actions++;
          await fn();
        };
        const started = performance.now();
        if (task === tasks[0]) {
          if (path === "existing manual navigation") {
            await act(() =>
              page
                .getByRole("link", { name: "Attendance", exact: true })
                .click(),
            );
            await act(() =>
              page
                .getByRole("combobox", { name: "Class", exact: true })
                .selectOption(String(target.class_id)),
            );
          } else
            await act(() =>
              page
                .locator(`a[href="/app/attendance?classId=${target.class_id}"]`)
                .click(),
            );
          await expect(
            page.getByRole("combobox", { name: "Class", exact: true }),
          ).toHaveValue(String(target.class_id));
          await expect(
            page.getByRole("button", { name: new RegExp(roster[0].name) }),
          ).toBeVisible();
        } else if (task === tasks[1]) {
          if (path === "existing manual navigation") {
            await act(() =>
              page
                .getByRole("link", { name: "Assignments", exact: true })
                .click(),
            );
            await act(() =>
              page
                .getByRole("button", { name: "Create assignment", exact: true })
                .click(),
            );
          } else
            await act(() =>
              page
                .locator(".quick-actions")
                .getByRole("link", { name: /Create an assignment/ })
                .click(),
            );
          await expect(
            page
              .getByRole("dialog")
              .getByRole("heading", { name: "A new learning opportunity" }),
          ).toBeVisible();
        } else {
          if (path === "existing manual navigation") {
            await act(() =>
              page
                .getByRole("link", { name: "Assignments", exact: true })
                .click(),
            );
            const card = page
              .locator("article")
              .filter({
                has: page.getByRole("heading", {
                  name: assignment.title,
                  exact: true,
                }),
              });
            await act(() =>
              card.getByRole("button", { name: "Review submissions" }).click(),
            );
          } else
            await act(() =>
              page
                .locator(`a[href="/app/assignments?review=${assignment.id}"]`)
                .click(),
            );
          await expect(
            page
              .getByRole("dialog")
              .getByRole("heading", { name: assignment.title, exact: true }),
          ).toBeVisible();
          await expect(
            page.getByRole("dialog").locator(".review-card").first(),
          ).toBeVisible();
        }
        results.push({
          task,
          path,
          trial: trial + 1,
          logical_interactions: actions,
          elapsed_ms: Math.round(performance.now() - started),
        });
      }
    }
  }
  const median = (values) =>
    [...values].sort((a, b) => a - b)[Math.floor(values.length / 2)];
  const summary = tasks.map((task) => {
    const manual = results.filter(
      (r) => r.task === task && r.path === "existing manual navigation",
    );
    const shortcut = results.filter(
      (r) => r.task === task && r.path === "dashboard shortcut",
    );
    return {
      task,
      manual_interactions: manual[0].logical_interactions,
      shortcut_interactions: shortcut[0].logical_interactions,
      manual_median_ms: median(manual.map((r) => r.elapsed_ms)),
      shortcut_median_ms: median(shortcut.map((r) => r.elapsed_ms)),
    };
  });
  fs.mkdirSync("../docs/demo", { recursive: true });
  const report = {
    generated_at_utc: new Date().toISOString(),
    scope:
      "Automated warm-session local Chromium task-entry checks; not a human teacher time-saving study.",
    conditions: [
      "Three trials per path with alternating order.",
      "Login, return-to-overview setup, typing, saving and reading time excluded.",
      "Each Playwright click or selectOption counts as one logical interaction; native click counts can differ.",
      "No comparison against teacher paper workflows; no daily minutes-saved claim.",
      "Only original approved synthetic demo records used; no AI calls.",
    ],
    summary,
    trials: results,
    page_errors: errors,
  };
  fs.writeFileSync(
    "../docs/demo/workflow-measurements.json",
    JSON.stringify(report, null, 2) + "\n",
  );
  await page.goto(`${base}/app`);
  await expect(
    page.getByRole("heading", { name: "Today’s classes" }),
  ).toBeVisible();
  await expect(page.locator(".teacher-class-row")).toHaveCount(3);
  await page.screenshot({
    path: "../docs/demo/teacher-desktop.png",
    fullPage: true,
  });
  await page.setViewportSize({ width: 390, height: 844 });
  await page.screenshot({
    path: "../docs/demo/teacher-mobile.png",
    fullPage: true,
  });
  if (
    await page.evaluate(() => document.documentElement.scrollWidth > innerWidth)
  )
    throw new Error("Mobile horizontal overflow");
  if (errors.length) throw new Error(errors.join("; "));
  console.log(JSON.stringify({ summary, page_errors: errors }));
} finally {
  await browser.close();
}
