/**
 * make_poster.js
 * ──────────────
 * Generates MASBIO_Poster_2026.pptx — a fully editable 1-page A0-style
 * conference poster for the MASBIO Data Publishing Agent project.
 *
 * Run: node make_poster.js
 * Output: MASBIO_Poster_2026.pptx (saved next to this script)
 *
 * Install deps first:
 *   npm install pptxgenjs
 */

const pptxgen = require("pptxgenjs");
const path    = require("path");

// ── Poster dimensions (A0 landscape in inches: 46.8 × 33.1) ─────────────────
// Scaled to 1/3 for comfortable editing — scale up when printing
const W = 15.6;   // width  (inches)
const H = 11.0;   // height (inches)

// ── Colour palette (Ocean / Marine) ─────────────────────────────────────────
const TEAL      = "028090";   // dominant — headers, accents
const TEAL_DARK = "01606E";   // darker teal for title bar
const TEAL_LITE = "E0F4F7";   // very light teal — card backgrounds
const MINT      = "02C39A";   // accent — highlight boxes
const WHITE     = "FFFFFF";
const OFFWHITE  = "F7FAFB";
const DARK      = "1A2E35";   // body text
const MID       = "4A6572";   // muted text

// ── Typography ───────────────────────────────────────────────────────────────
const FONT      = "Calibri";

// ── Helper: fresh shadow ─────────────────────────────────────────────────────
const mkShadow = () => ({ type: "outer", color: "000000", blur: 8, offset: 3, angle: 135, opacity: 0.12 });

// ── Helper: section card ─────────────────────────────────────────────────────
function card(slide, x, y, w, h, title, bodyLines, accentColor = TEAL) {
  // Card background
  slide.addShape("rect", {
    x, y, w, h,
    fill: { color: WHITE },
    line: { color: "E0E8EA", width: 0.5 },
    shadow: mkShadow(),
  });
  // Left accent strip
  slide.addShape("rect", {
    x, y, w: 0.07, h,
    fill: { color: accentColor },
    line: { color: accentColor, width: 0 },
  });
  // Title bar
  slide.addShape("rect", {
    x, y, w, h: 0.38,
    fill: { color: accentColor },
    line: { color: accentColor, width: 0 },
  });
  slide.addText(title.toUpperCase(), {
    x: x + 0.12, y: y + 0.04, w: w - 0.2, h: 0.3,
    fontFace: FONT, fontSize: 10, bold: true, color: WHITE,
    margin: 0,
  });
  // Body
  if (bodyLines && bodyLines.length) {
    slide.addText(bodyLines, {
      x: x + 0.15, y: y + 0.44, w: w - 0.25, h: h - 0.52,
      fontFace: FONT, fontSize: 9, color: DARK,
      valign: "top", margin: 0,
    });
  }
}

// ── Helper: flow box (for diagram) ──────────────────────────────────────────
function flowBox(slide, x, y, w, h, label, sublabel, fill, textColor = WHITE) {
  slide.addShape("rect", {
    x, y, w, h,
    fill: { color: fill },
    line: { color: fill, width: 0 },
    shadow: mkShadow(),
  });
  const items = sublabel
    ? [
        { text: label,    options: { bold: true, breakLine: true, fontSize: 9  } },
        { text: sublabel, options: { bold: false, fontSize: 7.5 } },
      ]
    : [{ text: label, options: { bold: true, fontSize: 9 } }];
  slide.addText(items, {
    x, y, w, h,
    fontFace: FONT, color: textColor,
    align: "center", valign: "middle", margin: 0,
  });
}

// ── Helper: arrow ─────────────────────────────────────────────────────────────
function arrowDown(slide, x, y, len = 0.22) {
  slide.addShape("line", {
    x, y, w: 0, h: len,
    line: { color: MID, width: 1.5, endArrowType: "arrow" },
  });
}
function arrowRight(slide, x, y, len = 0.22) {
  slide.addShape("line", {
    x, y, w: len, h: 0,
    line: { color: MID, width: 1.5, endArrowType: "arrow" },
  });
}

// ════════════════════════════════════════════════════════════════════════════
// BUILD POSTER
// ════════════════════════════════════════════════════════════════════════════

async function buildPoster() {
  const pres = new pptxgen();
  pres.defineLayout({ name: "POSTER", width: W, height: H });
  pres.layout = "POSTER";

  const slide = pres.addSlide();
  slide.background = { color: OFFWHITE };

  // ── HEADER BAR ──────────────────────────────────────────────────────────
  slide.addShape("rect", {
    x: 0, y: 0, w: W, h: 1.05,
    fill: { color: TEAL_DARK },
    line: { color: TEAL_DARK, width: 0 },
  });
  // Mint accent strip at bottom of header
  slide.addShape("rect", {
    x: 0, y: 1.05, w: W, h: 0.055,
    fill: { color: MINT },
    line: { color: MINT, width: 0 },
  });

  // Poster title
  slide.addText("AI-Powered Research Data Publishing Agent for Harvard Dataverse", {
    x: 0.3, y: 0.07, w: 11.5, h: 0.52,
    fontFace: FONT, fontSize: 24, bold: true, color: WHITE, margin: 0,
  });
  // Subtitle / project
  slide.addText("MASBIO — Marine and Saltwater Biomass Innovation Project  ·  Horizon Europe / ERC", {
    x: 0.3, y: 0.6, w: 11.0, h: 0.3,
    fontFace: FONT, fontSize: 11, color: "B2E4EC", italic: true, margin: 0,
  });
  // Author + affiliation
  slide.addText("Syeda Nyma Ferdous  ·  North Carolina State University  ·  snferdou@ncsu.edu", {
    x: 0.3, y: 0.78, w: 10.0, h: 0.24,
    fontFace: FONT, fontSize: 9.5, color: "D0EEF3", margin: 0,
  });
  // Year badge
  slide.addShape("rect", {
    x: 14.8, y: 0.08, w: 0.72, h: 0.34,
    fill: { color: MINT },
    line: { color: MINT, width: 0 },
  });
  slide.addText("2026", {
    x: 14.8, y: 0.08, w: 0.72, h: 0.34,
    fontFace: FONT, fontSize: 10, bold: true, color: WHITE,
    align: "center", valign: "middle", margin: 0,
  });

  // ── COLUMN SETUP ─────────────────────────────────────────────────────────
  const TOP    = 1.18;
  const BOT    = H - 0.45;
  const CH     = BOT - TOP;   // content height
  const GAP    = 0.14;
  const C1W    = 3.3;
  const C2W    = 6.1;
  const C3W    = 3.55;
  const C1X    = 0.18;
  const C2X    = C1X + C1W + GAP;
  const C3X    = C2X + C2W + GAP;

  // ══════════════════════════════════════════════════════════════════════════
  // COLUMN 1 — Introduction + Technology Stack
  // ══════════════════════════════════════════════════════════════════════════

  // Background & Motivation
  card(slide, C1X, TOP, C1W, 2.45, "Background & Motivation", [
    { text: "Research data management is a critical challenge in modern science. Manually publishing datasets to repositories like Harvard Dataverse requires filling complex metadata forms and navigating APIs — a time-consuming barrier for researchers.", options: { breakLine: true, paraSpaceAfter: 6 } },
    { text: "The MASBIO project generates four primary data streams:", options: { breakLine: true, bold: true, paraSpaceAfter: 3 } },
    { text: "Biomass production statistics (FAOSTAT, CSV)", options: { bullet: true, breakLine: true, indentLevel: 0 } },
    { text: "Field sensor data — pH, DO, salinity, temperature", options: { bullet: true, breakLine: true } },
    { text: "Policy & governance documents (PDF)", options: { bullet: true, breakLine: true } },
    { text: "RAG pipeline outputs — embeddings, Q&A logs", options: { bullet: true } },
  ]);

  // Objectives
  card(slide, C1X, TOP + 2.55, C1W, 1.85, "Objectives", [
    { text: "Automate metadata generation using AI (Groq + RAG)", options: { bullet: true, breakLine: true } },
    { text: "Publish datasets to Harvard Dataverse via API", options: { bullet: true, breakLine: true } },
    { text: "Provide a browser-based UI for non-technical users", options: { bullet: true, breakLine: true } },
    { text: "Ensure FAIR data principles and CC0 licensing", options: { bullet: true, breakLine: true } },
    { text: "Eliminate manual metadata entry entirely", options: { bullet: true } },
  ]);

  // Technology Stack
  card(slide, C1X, TOP + 4.5, C1W, 2.2, "Technology Stack", [
    { text: "LangChain ReAct", options: { bold: true, breakLine: false } },
    { text: " — Agent framework\n", options: { breakLine: true } },
    { text: "Groq (Llama 3)", options: { bold: true, breakLine: false } },
    { text: " — Free LLM API\n", options: { breakLine: true } },
    { text: "sentence-transformers", options: { bold: true, breakLine: false } },
    { text: " — Local RAG embeddings\n", options: { breakLine: true } },
    { text: "FastAPI", options: { bold: true, breakLine: false } },
    { text: " — REST API + web UI\n", options: { breakLine: true } },
    { text: "Playwright", options: { bold: true, breakLine: false } },
    { text: " — Browser automation\n", options: { breakLine: true } },
    { text: "Harvard Dataverse Native API", options: { bold: true, breakLine: false } },
    { text: " — Repository", options: {} },
  ]);

  // ══════════════════════════════════════════════════════════════════════════
  // COLUMN 2 — Architecture Diagram
  // ══════════════════════════════════════════════════════════════════════════

  card(slide, C2X, TOP, C2W, CH, "System Architecture — Data Publishing Agent", null);

  // Diagram area starts after header bar of card
  const DX = C2X + 0.15;
  const DY = TOP + 0.5;
  const DW = C2W - 0.3;

  // ── Row 1: User ──────────────────────────────────────────────────────────
  const bw = 1.55, bh = 0.52;
  const row1y = DY + 0.1;
  const userX = DX + (DW - bw) / 2;
  flowBox(slide, userX, row1y, bw, bh, "Researcher", "Uploads CSV via Browser UI", TEAL_DARK);
  arrowDown(slide, userX + bw / 2, row1y + bh, 0.22);

  // ── Row 2: FastAPI ────────────────────────────────────────────────────────
  const row2y = row1y + bh + 0.22;
  flowBox(slide, userX, row2y, bw, bh, "FastAPI REST Service", "POST /api/v1/pipeline/publish", "1C7293");
  arrowDown(slide, userX + bw / 2, row2y + bh, 0.22);

  // ── Row 3: RAG + Groq (side by side) ─────────────────────────────────────
  const row3y = row2y + bh + 0.22;
  const halfW = (DW - 0.2) / 2;
  const ragX  = DX + 0.05;
  const groqX = DX + 0.05 + halfW + 0.1;

  flowBox(slide, ragX, row3y, halfW, 1.05,
    "RAG Feature Extraction",
    "Column names · Time period\nGeo coverage · Data source\n(sentence-transformers — local)",
    "21295C");

  flowBox(slide, groqX, row3y, halfW, 1.05,
    "Groq LLM — Llama 3",
    "Description · Keywords\nSubject classification\n(Free API · No cost)",
    MINT, DARK);

  // Merge arrow
  const mergeX = DX + DW / 2;
  arrowDown(slide, mergeX, row3y + 1.05, 0.22);

  // ── Merge box: Combined Metadata ─────────────────────────────────────────
  const row4y = row3y + 1.05 + 0.22;
  const mergeW = 2.6;
  flowBox(slide, DX + (DW - mergeW) / 2, row4y, mergeW, 0.48,
    "Merged Metadata",
    "Title (filename) + Groq fields + RAG-detected fields",
    "4A6572");
  arrowDown(slide, mergeX, row4y + 0.48, 0.22);

  // ── Row 5: LangChain Agent ────────────────────────────────────────────────
  const row5y = row4y + 0.48 + 0.22;
  const agentW = DW - 0.1;
  flowBox(slide, DX + 0.05, row5y, agentW, 0.42,
    "LangChain ReAct Agent  —  claude-sonnet-4-6 / Llama 3",
    "Reasons step-by-step · Selects tools · Handles failures",
    TEAL_DARK);

  // ── Row 6: 5 Tools ────────────────────────────────────────────────────────
  const row6y = row5y + 0.42 + 0.18;
  const tools = [
    ["Search", "Check duplicates"],
    ["Create", "POST metadata → DOI"],
    ["Upload", "CSV to draft"],
    ["Verify", "Check state"],
    ["Publish", "Wait lock → Go live"],
  ];
  const toolColors = ["028090", "02A896", TEAL, "01606E", MINT];
  const toolW = (agentW - 0.04 * 4) / 5;
  tools.forEach((t, i) => {
    const tx = DX + 0.05 + i * (toolW + 0.04);
    // Arrow from agent box
    slide.addShape("line", {
      x: tx + toolW / 2,
      y: row5y + 0.42,
      w: 0, h: 0.18,
      line: { color: MID, width: 1, endArrowType: "arrow" },
    });
    flowBox(slide, tx, row6y, toolW, 0.72, t[0], t[1], toolColors[i]);
  });

  // ── Row 7: Dataverse ─────────────────────────────────────────────────────
  const row7y = row6y + 0.72 + 0.22;
  arrowDown(slide, mergeX, row6y + 0.72, 0.22);
  const dvW = 2.8;
  flowBox(slide, DX + (DW - dvW) / 2, row7y, dvW, 0.52,
    "Harvard Dataverse",
    "Permanent DOI · Publicly accessible · CC0 1.0",
    "8B0000");

  // ── Row 8: Output ─────────────────────────────────────────────────────────
  const row8y = row7y + 0.52 + 0.18;
  arrowDown(slide, mergeX, row7y + 0.52, 0.18);
  const outW = 2.4;
  flowBox(slide, DX + (DW - outW) / 2, row8y, outW, 0.4,
    "Published Dataset + DOI returned to Browser",
    null, "02C39A", DARK);

  // ══════════════════════════════════════════════════════════════════════════
  // COLUMN 3 — Results + Future Work
  // ══════════════════════════════════════════════════════════════════════════

  // Key Features
  card(slide, C3X, TOP, C3W, 2.35, "Key Features", [
    { text: "Zero-cost metadata", options: { bold: true, breakLine: false } },
    { text: " — RAG pipeline runs fully locally with no API fees\n", options: { breakLine: true } },
    { text: "Hybrid AI", options: { bold: true, breakLine: false } },
    { text: " — Groq LLM for semantics + RAG for structure\n", options: { breakLine: true } },
    { text: "Smart title", options: { bold: true, breakLine: false } },
    { text: " — Always derived from the original filename\n", options: { breakLine: true } },
    { text: "Ingest-aware publishing", options: { bold: true, breakLine: false } },
    { text: " — Polls lock status before publish\n", options: { breakLine: true } },
    { text: "Browser UI", options: { bold: true, breakLine: false } },
    { text: " — No code required for non-technical users\n", options: { breakLine: true } },
    { text: "Dry-run mode", options: { bold: true, breakLine: false } },
    { text: " — Test without publishing", options: {} },
  ]);

  // FAIR Data Compliance
  card(slide, C3X, TOP + 2.45, C3W, 1.65, "FAIR Data Compliance", [
    { text: "F", options: { bold: true, color: TEAL, breakLine: false } },
    { text: "indable — Persistent DOI via Harvard Dataverse\n", options: { breakLine: true } },
    { text: "A", options: { bold: true, color: TEAL, breakLine: false } },
    { text: "ccessible — Public API + browser interface\n", options: { breakLine: true } },
    { text: "I", options: { bold: true, color: TEAL, breakLine: false } },
    { text: "nteroperable — Dataverse citation metadata schema\n", options: { breakLine: true } },
    { text: "R", options: { bold: true, color: TEAL, breakLine: false } },
    { text: "eusable — CC0 1.0 license, FAOSTAT provenance", options: {} },
  ]);

  // Results
  card(slide, C3X, TOP + 4.2, C3W, 1.95, "Results & Validation", [
    { text: "Successfully published FAOSTAT forestry biomass datasets to Harvard Dataverse in draft mode with auto-generated metadata.", options: { breakLine: true, paraSpaceAfter: 5 } },
    { text: "Metadata accuracy tested against 20 domain knowledge base entries covering biomass, marine, agricultural and environmental datasets.", options: { breakLine: true, paraSpaceAfter: 5 } },
    { text: "End-to-end pipeline completes in under 60 seconds including ingest lock wait.", options: {} },
  ]);

  // Future Work
  card(slide, C3X, TOP + 6.25, C3W, 1.45, "Future Work", [
    { text: "Migrate agent core from LangChain to LangGraph for better control", options: { bullet: true, breakLine: true } },
    { text: "Expand knowledge base to 100+ domain entries", options: { bullet: true, breakLine: true } },
    { text: "Add multi-file batch publishing support", options: { bullet: true, breakLine: true } },
    { text: "Deploy as shared team service via Railway", options: { bullet: true } },
  ]);

  // ── FOOTER ───────────────────────────────────────────────────────────────
  slide.addShape("rect", {
    x: 0, y: H - 0.4, w: W, h: 0.4,
    fill: { color: TEAL_DARK },
    line: { color: TEAL_DARK, width: 0 },
  });
  slide.addText(
    "MASBIO — Marine and Saltwater Biomass Innovation Project  ·  Horizon Europe  ·  Contact: snferdou@ncsu.edu  ·  dataverse.harvard.edu",
    {
      x: 0.3, y: H - 0.38, w: W - 0.6, h: 0.35,
      fontFace: FONT, fontSize: 8.5, color: "B2E4EC",
      valign: "middle", margin: 0,
    }
  );

  // ── SAVE ─────────────────────────────────────────────────────────────────
  const outPath = path.join(__dirname, "MASBIO_Poster_2026.pptx");
  await pres.writeFile({ fileName: outPath });
  console.log("✅  Saved → " + outPath);
}

buildPoster().catch(err => { console.error("Error:", err); process.exit(1); });
