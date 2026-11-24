/** Local poster export from the Workbench's verified read surface. */
import { mkdir, writeFile } from "node:fs/promises";
import { join } from "node:path";
import { parseArgs } from "node:util";
import { chromium } from "@playwright/test";
import { conditionFigure, familyFigure } from "./figures.mjs";

const { values } = parseArgs({
  options: {
    origin: { type: "string", default: "http://127.0.0.1:8080" },
    experiment: { type: "string" },
    run: { type: "string" },
    condition: { type: "string" },
    output: { type: "string" },
  },
});

try {
  await exportBenchmark(values);
} catch (error) {
  console.error(`Benchmark export failed: ${error.message}`);
  process.exitCode = 1;
}

async function exportBenchmark({ origin, experiment, run, condition, output }) {
  if (!experiment || !run || !output) {
    throw new Error(
      "Supply --experiment ID --run ID --output NEW_DIRECTORY and optionally --condition ID",
    );
  }
  const url = new URL(origin);
  if (
    url.protocol !== "http:" ||
    !["127.0.0.1", "localhost", "[::1]"].includes(url.hostname) ||
    url.username ||
    url.password ||
    url.pathname !== "/" ||
    url.search ||
    url.hash
  ) {
    throw new Error("The origin must be a local HTTP Workbench");
  }
  if (!/^[a-f0-9]{32}$/.test(experiment) || !/^[a-f0-9]{32}$/.test(run)) {
    throw new Error(
      "Experiment and Run identifiers must each have 32 lowercase hexadecimal characters",
    );
  }
  const health = await readJson(url, "/health");
  if (health.read_only !== true)
    throw new Error("The Workbench must be running in read-only mode");
  const detail = await readJson(
    url,
    `/api/research/v2/experiments/${experiment}/runs/${run}`,
  );
  if (!detail.benchmark)
    throw new Error("The Run has no verified Benchmark v3 result");
  const selected = condition
    ? detail.observations.find(
        (item) => item.benchmark?.condition === condition,
      )
    : null;
  if (condition && !selected)
    throw new Error("The selected Condition is outside the verified Run");

  const figures = new Map([
    ["family-performance", familyFigure(detail.benchmark.families)],
  ]);
  if (selected) figures.set("condition-comparison", conditionFigure(selected));
  const pdf = await renderPdf(figures);

  await mkdir(output, { mode: 0o700 });
  const write = (name, data) =>
    writeFile(join(output, name), data, { flag: "wx", mode: 0o600 });
  await write("metrics.csv", metricsCsv(detail));
  await write(
    "provenance.json",
    JSON.stringify(
      {
        run: detail.id,
        artifact_digest: detail.artifact_digest,
        protocol: detail.benchmark.scope.protocol_version,
        benchmark_digest: detail.benchmark.scope.benchmark_sha256,
        observation_origin: detail.benchmark.scope.observation_origin,
        selected_condition: selected?.benchmark.condition ?? null,
      },
      null,
      2,
    ) + "\n",
  );
  for (const [name, value] of figures) {
    await write(`${name}.svg`, value.svg);
    await write(`${name}.pdf`, pdf.get(name));
  }
  console.log("Verified poster export saved locally.");
}

async function readJson(origin, path) {
  const response = await fetch(new URL(path, origin), {
    redirect: "error",
    signal: AbortSignal.timeout(30_000),
  });
  if (!response.ok)
    throw new Error(
      `Workbench returned HTTP ${response.status}; no export was written`,
    );
  return response.json();
}

async function renderPdf(figures) {
  const browser = await chromium.launch();
  try {
    const page = await browser.newPage();
    const pdf = new Map();
    for (const [name, value] of figures) {
      await page.setContent(`<!doctype html><style>
        @page { size: ${value.width}px ${value.height}px; margin: 0 }
        body { margin: 0 } svg { display: block }
      </style>${value.svg}`);
      pdf.set(
        name,
        await page.pdf({ preferCSSPageSize: true, printBackground: true }),
      );
    }
    return pdf;
  } finally {
    await browser.close();
  }
}

function metricsCsv(detail) {
  const {
    cohort,
    families,
    family_macro_f1,
    valid_graph_only_family_macro_f1,
    valid_graph_only_macro_family_count,
    scope,
  } = detail.benchmark;
  const rows = [
    [
      "cohort",
      "",
      "",
      "",
      cohort,
      family_macro_f1,
      valid_graph_only_family_macro_f1,
      valid_graph_only_macro_family_count,
    ],
    ...Object.entries(families).map(([family, data]) => [
      "family",
      family,
      "",
      "",
      data,
    ]),
    ...detail.observations.map(({ benchmark: condition }) => [
      "condition",
      condition.family,
      condition.condition,
      condition.outcome,
      observationMetrics(condition),
    ]),
  ];
  const keys = [
    "planned_conditions",
    "valid_graphs",
    "exact_graphs",
    "all_condition_micro_f1",
    "valid_graph_only_micro_f1",
    "expected_edges_without_graph",
    "planned_proofs",
    "complete_proofs",
    "planned_joint_proofs",
    "complete_joint_proofs",
    "incomplete_proofs",
    "missed_proofs",
    "proofs_without_graph",
    "quote_passed",
    "quote_assessed",
    "attribution_passed",
    "attribution_assessed",
  ];
  const header = [
    "level",
    "family",
    "condition",
    "outcome",
    ...keys,
    "tp",
    "fp",
    "fn",
    "valid_graph_tp",
    "valid_graph_fp",
    "valid_graph_fn",
    "family_macro_f1",
    "valid_graph_only_family_macro_f1",
    "valid_graph_only_macro_family_count",
    "protocol",
    "run_id",
    "run_digest",
  ];
  return (
    [
      header,
      ...rows.map(
        ([
          level,
          family,
          condition,
          outcome,
          m,
          macro,
          validMacro,
          macroCount,
        ]) => [
          level,
          family,
          condition,
          outcome,
          ...keys.map((key) => m[key]),
          m.all_conditions.tp,
          m.all_conditions.fp,
          m.all_conditions.fn,
          m.valid_graph_only?.tp,
          m.valid_graph_only?.fp,
          m.valid_graph_only?.fn,
          macro,
          validMacro,
          macroCount,
          scope.protocol_version,
          detail.id,
          detail.artifact_digest,
        ],
      ),
    ]
      .map((row) => row.map(csvValue).join(","))
      .join("\n") + "\n"
  );
}

function observationMetrics(condition) {
  const { graph, expected_edges: expected, metrics } = condition;
  return {
    ...metrics,
    planned_conditions: 1,
    valid_graphs: Number(Boolean(graph)),
    exact_graphs: Number(Boolean(graph && !graph.fp && !graph.fn)),
    all_condition_micro_f1: graph?.f1 ?? 0,
    valid_graph_only_micro_f1: graph?.f1,
    expected_edges_without_graph: graph ? 0 : expected,
    proofs_without_graph: graph ? 0 : metrics.planned_proofs,
    all_conditions: {
      tp: graph?.tp ?? 0,
      fp: graph?.fp ?? 0,
      fn: graph?.fn ?? expected,
    },
    valid_graph_only: graph,
  };
}

function csvValue(value) {
  if (value === undefined || value === null) return "";
  const source = String(value);
  return /[",\n\r]/.test(source) ? `"${source.replaceAll('"', '""')}"` : source;
}
