import { defineConfig } from "@playwright/test";
import base from "./playwright.config";

// Audit uses a separately seeded local API/database; never point it at a school pilot.
export default defineConfig({
  ...base,
  testDir: "./tests",
  outputDir: "../.audit/playwright-results",
  use: { ...base.use, baseURL: "http://localhost:3001" },
});
