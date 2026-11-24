import assert from "node:assert/strict";
import { test } from "node:test";
import { conditionFigure, familyFigure } from "./figures.mjs";
import { readFile } from "node:fs/promises";

test("poster figures show unavailable delivery and retain graph coverage", () => {
  const family = familyFigure({
    F: { all_condition_micro_f1: 0, valid_graphs: 0, planned_conditions: 1 },
  });
  assert.match(family.svg, /0\/1/);
  assert.match(family.svg, /All-condition micro-F1/);

  const entities = [
    { id: "x", name: "A < B", type: "person" },
    { id: "y", name: "Trust", type: "trust" },
  ];
  const graph = {
    entities,
    relationships: [{ source: "x", target: "y", type: "trustee_of" }],
  };
  const result = conditionFigure({
    benchmark: {
      condition: "F0",
      expected: graph,
      graph: null,
      proof_targets: [],
    },
    result: null,
  });
  assert.match(result.svg, /A &lt; B/);
  assert.match(result.svg, /Predicted graph unavailable/);
  assert.match(result.svg, /trustee of/);
});

test("poster CLI requires a predicted graph and incomplete joint proof for condition output", async () => {
  const source = await readFile(new URL("./benchmark.mjs", import.meta.url), "utf8");
  assert.match(source, /selected\.benchmark\.graph/);
  assert.match(source, /target\.joint_only && target\.status !== "complete"/);
});
