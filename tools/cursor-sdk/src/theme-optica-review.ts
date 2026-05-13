/**
 * OPTICA theme pass via Cursor SDK (`Agent.prompt`).
 *
 * From this directory:
 *   set CURSOR_API_KEY=your_key
 *   npm install
 *   npm run review
 *
 * Requires Node 20+. Uses local runtime: agent sees the real repo at theme root.
 */
import { Agent, CursorAgentError } from "@cursor/sdk";
import path from "node:path";
import { fileURLToPath } from "node:url";

const __dirname = path.dirname(fileURLToPath(import.meta.url));
/** Repo root (rebel-shopify), not tools/cursor-sdk */
const THEME_ROOT = path.resolve(__dirname, "..", "..", "..");

const PROMPT = `You are reviewing this Shopify OS 2.0 theme (Horizon base + OPTICA homepage + Atelier components).

Read these paths from the repo root (they exist):
- docs/OPTICA-THEME-REFERENCE.md
- .cursor/rules/shopify-theme.mdc

Then produce a concise review:

1. **Scoping** — Homepage CSS must live under \`body.template-index\`; PDP under \`body.template-product\`. Flag any risky global or wrong-scope patterns in assets/atelier-luxury.css and assets/optica-pdp.css.
2. **Sections** — Spot-check sections/optica-*.liquid and sections/atelier-*.liquid for schema safety, hardcoded copy that should be settings, and alignment with the reference doc.
3. **Layout** — templates/index.json and templates/product.json: section/block order sanity vs the reference (do not assume order is wrong without checking the file).
4. **Boundaries** — Note if anything suggests editing Horizon core (assets/base.css, sections/header.liquid) without strong justification.

Output Markdown: use severity labels (blocker / should-fix / nit). Include file paths; line numbers when you cite specific code. End with a short "merchant editor" checklist (what to verify in Theme Editor).`;

async function main(): Promise<void> {
  if (!process.env.CURSOR_API_KEY?.trim()) {
    console.error(
      "Missing CURSOR_API_KEY. Create a key under Cursor Dashboard (Cloud agents) or a team service account, then set the env var."
    );
    process.exit(1);
  }

  console.error("Theme root:", THEME_ROOT);
  console.error("Starting local agent run…\n");

  try {
    const result = await Agent.prompt(PROMPT, {
      apiKey: process.env.CURSOR_API_KEY.trim(),
      model: { id: "composer-2" },
      local: { cwd: THEME_ROOT },
    });

    if (result.status === "error") {
      console.error("Run finished with error status. Inspect the run in Cursor if needed.");
      process.exit(2);
    }

    process.stdout.write(String(result.result ?? "(no text result)\n"));
  } catch (err) {
    if (err instanceof CursorAgentError) {
      console.error("Startup/network error:", err.message, "| retryable=", err.isRetryable);
      process.exit(1);
    }
    throw err;
  }
}

await main();
