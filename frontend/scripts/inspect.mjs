import { chromium } from "@playwright/test";
import fs from "node:fs";
const browser = await chromium.launch({ headless: true });
const page = await browser.newPage({ viewport: { width: 1440, height: 1050 } });
await page.emulateMedia({ reducedMotion: "reduce" });
const errors = [];
page.on("pageerror", (e) => errors.push(e.message));
await page.goto("http://localhost:3000/login");
await page.getByLabel("School email").fill("teacher@nexora.demo");
await page.getByLabel("Password", { exact: true }).fill("NexoraDemo!2026");
await page.getByRole("button", { name: "Sign in to Nexora" }).click();
await page.waitForURL("**/app");
await page.getByRole("heading", { name: /A good day/ }).waitFor();
fs.mkdirSync("../docs/screenshots", { recursive: true });
await page.screenshot({
  path: "../docs/screenshots/teacher-desktop.png",
  fullPage: true,
});
await page.setViewportSize({ width: 390, height: 844 });
console.log(
  JSON.stringify(
    await page.evaluate(() => ({
      classes: document.querySelector(".workspace").className,
      transform: getComputedStyle(document.querySelector(".sidebar")).transform,
      right: document.querySelector(".sidebar").getBoundingClientRect().right,
      width: innerWidth,
    })),
  ),
);
await page.screenshot({
  path: "../docs/screenshots/teacher-mobile.png",
  fullPage: true,
});
console.log(
  JSON.stringify({
    pageErrors: errors,
    viewportOverflow: await page.evaluate(
      () => document.documentElement.scrollWidth > innerWidth,
    ),
  }),
);
await page.setViewportSize({ width: 1440, height: 1050 });
await page.goto("http://localhost:3000/app/notes");
await page.getByRole("button", { name: "Add study material" }).click();
console.log(
  JSON.stringify(
    await page
      .getByRole("dialog")
      .locator("select")
      .evaluateAll((es) =>
        es.map((e) => ({
          html: e.outerHTML,
          labels: [...e.labels].map((l) => l.textContent),
        })),
      ),
  ),
);
for (const size of [192, 512]) {
  await page.setViewportSize({ width: size, height: size });
  const svg = fs
    .readFileSync("public/icon.svg", "utf8")
    .replace("<svg ", `<svg width="${size}" height="${size}" `);
  await page.setContent(`<body style="margin:0">${svg}</body>`);
  await page.screenshot({
    path: `public/icon-${size}.png`,
    omitBackground: true,
  });
}
await browser.close();
