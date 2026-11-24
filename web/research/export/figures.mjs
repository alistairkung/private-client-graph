import dagre from "@dagrejs/dagre";

const ink = "#132837";
const muted = "#475966";
const colors = {
  expected: "#356c9b",
  missing: "#ab382c",
  extra: "#ab382c",
  matched: "#29725c",
};
const symmetric = new Set(["spouse_of", "sibling_of"]);
const escape = (value) =>
  String(value).replace(
    /[&<>"']/g,
    (c) =>
      ({
        "&": "&amp;",
        "<": "&lt;",
        ">": "&gt;",
        '"': "&quot;",
        "'": "&apos;",
      })[c],
  );

function figure(width, height, label, contents) {
  return {
    width,
    height,
    svg: `<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 ${width} ${height}" width="${width}" height="${height}" role="img">
<title>${escape(label)}</title>
<rect width="100%" height="100%" fill="#fff"/>
<g font-family="Arial, sans-serif" fill="${ink}">${contents}</g>
</svg>\n`,
  };
}

function text(x, y, value, size = 16, options = "") {
  return `<text x="${x}" y="${y}" font-size="${size}" ${options}>${escape(value)}</text>`;
}

export function familyFigure(families) {
  const rows = Object.entries(families);
  const height = rows.length * 26 + 146;
  const lines = rows.map(([family, metrics], index) => {
    const y = 112 + index * 26;
    const f1 = metrics.all_condition_micro_f1;
    return [
      text(36, y, family),
      `<rect x="140" y="${y - 13}" width="520" height="14" rx="2" fill="#eef2f4"/>`,
      `<rect x="140" y="${y - 13}" width="${f1 * 520}" height="14" rx="2" fill="#29725c"/>`,
      text(686, y, f1.toFixed(3)),
      text(818, y, `${metrics.valid_graphs}/${metrics.planned_conditions}`),
    ].join("");
  });
  return figure(
    944,
    height,
    "Benchmark v3 family performance",
    [
      text(36, 46, "Benchmark v3 family performance", 28, 'font-weight="bold"'),
      text(36, 80, "Family", 14),
      text(140, 80, "All-condition micro-F1", 14),
      text(818, 80, "Built / planned", 14),
      ...lines,
      text(
        36,
        height - 22,
        "Evaluation Protocol v1 · Unavailable graphs contribute expected-edge false negatives.",
        14,
        `fill="${muted}"`,
      ),
    ].join(""),
  );
}

export function conditionFigure(observation) {
  const {
    condition,
    expected,
    graph,
    proof_targets: proofs,
  } = observation.benchmark;
  const predicted = observation.result?.state;
  const outcomes = new Map();
  for (const edge of graph?.true_positive_edges ?? [])
    outcomes.set(JSON.stringify(edge), "matched");
  for (const edge of graph?.false_positive_edges ?? [])
    outcomes.set(JSON.stringify(edge), "extra");
  for (const edge of graph?.false_negative_edges ?? [])
    outcomes.set(JSON.stringify(edge), "missing");
  const expectedPanel = graphPanel(expected, outcomes);
  const predictedPanel = predicted ? graphPanel(predicted, outcomes) : null;
  const width = Math.max(
    1024,
    expectedPanel.width + (predictedPanel?.width ?? 480) + 104,
  );
  const leftWidth =
    expectedPanel.width +
    (width - expectedPanel.width - (predictedPanel?.width ?? 480)) / 2;
  const height =
    Math.max(expectedPanel.height, predictedPanel?.height ?? 0, 210) + 168;
  const joint = proofs.filter((proof) => proof.joint_only);
  const detail = joint.find((proof) => proof.status === "incomplete");
  const proofLabels = detail
    ? detail.alternatives.map(({ members }, index) => {
        const attached = members.filter((member) => member.attached).length;
        return `Alternative ${index + 1}: ${attached}/${members.length} exact members attached`;
      })
    : [];
  const proofHeight = proofLabels.length ? 46 + proofLabels.length * 22 : 0;
  return figure(
    width,
    height + proofHeight,
    `Benchmark v3 condition ${condition}`,
    [
      text(
        36,
        44,
        `Benchmark v3 · Condition ${condition}`,
        26,
        'font-weight="bold"',
      ),
      text(36, 75, "Expected graph", 18, 'font-weight="bold"'),
      text(leftWidth + 20, 75, "Predicted graph", 18, 'font-weight="bold"'),
      `<g transform="translate(36,90)">${expectedPanel.svg}</g>`,
      predictedPanel
        ? `<g transform="translate(${leftWidth + 20},90)">${predictedPanel.svg}</g>`
        : text(
            leftWidth + 20,
            124,
            "Predicted graph unavailable",
            16,
            `fill="${muted}"`,
          ),
      text(
        36,
        height - 50,
        "Green · matched  |  Red · missing or extra  |  Blue · expected",
        14,
      ),
      text(36, height - 24, "Evaluation Protocol v1", 14, `fill="${muted}"`),
      detail
        ? text(
            36,
            height + 12,
            `Incomplete joint proof · ${detail.edge.join(" · ")}`,
            16,
            'font-weight="bold"',
          )
        : "",
      ...proofLabels.map((label, index) =>
        text(36, height + 38 + index * 22, label, 14),
      ),
    ].join(""),
  );
}

function graphPanel(state, outcomes) {
  if (!state.entities.length)
    return { width: 250, height: 50, svg: text(0, 25, "Valid empty graph") };
  const graph = new dagre.graphlib.Graph({ multigraph: true });
  graph.setGraph({
    rankdir: "TB",
    marginx: 4,
    marginy: 8,
    nodesep: 38,
    ranksep: 70,
  });
  graph.setDefaultEdgeLabel(() => ({}));
  const names = new Map(state.entities.map((item) => [item.id, item.name]));
  for (const item of state.entities) {
    graph.setNode(item.id, {
      width: Math.max(90, item.name.length * 8 + 22),
      height: 38,
    });
  }
  state.relationships.forEach((item, index) => {
    const label = item.type.replaceAll("_", " ");
    const edge = [names.get(item.source), item.type, names.get(item.target)];
    const outcome =
      outcomes.get(JSON.stringify(edge)) ??
      (symmetric.has(item.type)
        ? outcomes.get(JSON.stringify([edge[2], edge[1], edge[0]]))
        : undefined);
    graph.setEdge(
      item.source,
      item.target,
      {
        width: label.length * 8,
        height: 20,
        label,
        directed: !symmetric.has(item.type),
        color:
          colors[outcome === "provenance_failure" ? "matched" : outcome] ??
          colors.expected,
      },
      String(index),
    );
  });
  dagre.layout(graph);
  const edges = graph.edges().map((key) => edgeMarkup(graph.edge(key)));
  const nodes = state.entities.map((item) => {
    const { x, y, width, height } = graph.node(item.id);
    const fill = item.type === "trust" ? "#edf6f3" : "#f1f5f8";
    return [
      `<rect x="${x - width / 2}" y="${y - height / 2}" width="${width}" height="${height}" rx="6" fill="${fill}" stroke="#567480"/>`,
      text(x, y + 5, item.name, 14, 'text-anchor="middle"'),
    ].join("");
  });
  return {
    width: graph.graph().width,
    height: graph.graph().height,
    svg: [...edges, ...nodes].join(""),
  };
}

function edgeMarkup({ points, x, y, width, label, directed, color }) {
  const path = points
    .map((point, index) => `${index ? "L" : "M"}${point.x},${point.y}`)
    .join(" ");
  const last = points.at(-1);
  const prior = points.at(-2);
  const angle =
    (Math.atan2(last.y - prior.y, last.x - prior.x) * 180) / Math.PI;
  return [
    `<path d="${path}" fill="none" stroke="${color}" stroke-width="2"/>`,
    directed
      ? `<path d="M0,0 -9,-4 -9,4 Z" transform="translate(${last.x},${last.y}) rotate(${angle})" fill="${color}"/>`
      : "",
    `<rect x="${x - width / 2 - 2}" y="${y - 9}" width="${width + 4}" height="19" fill="white"/>`,
    text(x, y + 4, label, 13, `fill="${color}" text-anchor="middle"`),
  ].join("");
}
