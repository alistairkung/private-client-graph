import { describe, expect, it } from "vitest";
import { graphDrawing } from "./graph-layout";
import type { Graph, Relationship } from "../shared/contracts";
import {
  nodeFootprint,
  type Rectangle,
  type RelationshipRoute,
} from "./node-geometry";

const evergreen: Graph = {
  entities: [
    { id: "alice", name: "Alice Chen", type: "person" },
    { id: "bob", name: "Bob Chen", type: "person" },
    { id: "carol", name: "Carol Wong", type: "person" },
    { id: "david", name: "David Chen", type: "person" },
    { id: "trust", name: "Evergreen Family Trust", type: "trust" },
  ],
  relationships: [
    { source: "alice", target: "bob", type: "parent_of", evidence_ids: ["e1"] },
    {
      source: "alice",
      target: "trust",
      type: "settlor_of",
      evidence_ids: ["e2"],
    },
    {
      source: "alice",
      target: "david",
      type: "spouse_of",
      evidence_ids: ["e3"],
    },
    {
      source: "bob",
      target: "trust",
      type: "beneficiary_of",
      evidence_ids: ["e4"],
    },
    {
      source: "carol",
      target: "trust",
      type: "beneficiary_of",
      evidence_ids: ["e5"],
    },
    { source: "david", target: "bob", type: "parent_of", evidence_ids: ["e6"] },
  ],
  evidence: [],
};
type Drawing = ReturnType<typeof graphDrawing>;
const routes = (drawing: Drawing) =>
  drawing.edges.map((edge) => edge.data!.route as RelationshipRoute);
function box(drawing: Drawing, id: string) {
  const node = drawing.nodes.find((node) => node.id === id)!;
  const width = Number(node.style!.width),
    height = Number(node.style!.height);
  return nodeFootprint(
    { x: node.position.x + width / 2, y: node.position.y + height / 2 },
    height,
  );
}
const overlaps = (a: Rectangle, b: Rectangle) =>
  a.left < b.right && a.right > b.left && a.top < b.bottom && a.bottom > b.top;
function assertClearLabels(drawing: Drawing) {
  const labels = routes(drawing).map((route) => route.labelBounds);
  labels.forEach((label, index) => {
    drawing.nodes.forEach((node) =>
      expect(
        overlaps(label, box(drawing, node.id)),
        "label " + index + " overlaps " + node.id,
      ).toBe(false),
    );
    labels
      .slice(index + 1)
      .forEach((other) =>
        expect(overlaps(label, other), "overlapping labels").toBe(false),
      );
  });
}
function assertCompleteBounds(drawing: Drawing) {
  const bounds = {
    left: drawing.bounds.x,
    right: drawing.bounds.x + drawing.bounds.width,
    top: drawing.bounds.y,
    bottom: drawing.bounds.y + drawing.bounds.height,
  };
  const boxes = [
    ...drawing.nodes.map((node) => box(drawing, node.id)),
    ...routes(drawing).map((route) => route.labelBounds),
  ];
  boxes.forEach((item) => {
    expect(item.left).toBeGreaterThanOrEqual(bounds.left);
    expect(item.right).toBeLessThanOrEqual(bounds.right);
    expect(item.top).toBeGreaterThanOrEqual(bounds.top);
    expect(item.bottom).toBeLessThanOrEqual(bounds.bottom);
  });
  routes(drawing)
    .flatMap((route) => route.points)
    .forEach((point) => {
      expect(point.x).toBeGreaterThanOrEqual(bounds.left);
      expect(point.x).toBeLessThanOrEqual(bounds.right);
      expect(point.y).toBeGreaterThanOrEqual(bounds.top);
      expect(point.y).toBeLessThanOrEqual(bounds.bottom);
    });
}
function assertClearPaths(drawing: Drawing) {
  drawing.edges.forEach((edge) => {
    const route = edge.data!.route as RelationshipRoute;
    const obstacles = drawing.nodes
      .filter((node) => ![edge.source, edge.target].includes(node.id))
      .map((node) => box(drawing, node.id));
    drawing.nodes
      .filter(
        (node) =>
          node.data.type === "trust" &&
          [edge.source, edge.target].includes(node.id),
      )
      .forEach((node) => {
        const caption = box(drawing, node.id);
        caption.top = node.position.y + Number(node.style!.height);
        obstacles.push(caption);
      });
    route.points.slice(1).forEach((end, index) => {
      const start = route.points[index];
      for (let step = 0; step <= 100; step++) {
        const x = start.x + ((end.x - start.x) * step) / 100,
          y = start.y + ((end.y - start.y) * step) / 100;
        obstacles.forEach((obstacle) =>
          expect(
            x > obstacle.left &&
              x < obstacle.right &&
              y > obstacle.top &&
              y < obstacle.bottom,
            edge.id + " crosses a nonendpoint node",
          ).toBe(false),
        );
      }
    });
  });
}
describe("Working Atlas relationship structure", () => {
  it("keeps the Evergreen spouses aligned above the Trust and beneficiaries below it", () => {
    const drawing = graphDrawing(evergreen, (key) => key);
    const alice = box(drawing, "alice"),
      david = box(drawing, "david"),
      trust = box(drawing, "trust"),
      bob = box(drawing, "bob"),
      carol = box(drawing, "carol");
    expect(alice.top).toBe(david.top);
    expect(david.right).toBeLessThan(alice.left);
    expect(alice.bottom).toBeLessThan(trust.top);
    expect(alice.left).toBe(trust.left);
    expect(bob.top).toBeGreaterThan(trust.bottom);
    expect(carol.top).toBe(bob.top);
    expect(bob.right).toBeLessThan(carol.left);
    expect(
      drawing.nodes.find((node) => node.id === "trust")?.style,
    ).toMatchObject({ width: 170, height: 96 });
    expect(
      drawing.edges.map((edge) => [edge.id, edge.source, edge.target]),
    ).toEqual(
      evergreen.relationships.map((edge, index) => [
        String(index),
        edge.source,
        edge.target,
      ]),
    );
  });
  it("routes all six Evergreen claims without crossing nonendpoint nodes or overlapping labels", () => {
    const drawing = graphDrawing(evergreen, (key) => key);
    assertClearPaths(drawing);
    assertClearLabels(drawing);
    assertCompleteBounds(drawing);
    expect(drawing.edges.filter((edge) => edge.data?.parent)).toHaveLength(2);
    expect(
      drawing.edges
        .filter((edge) => edge.data?.trust)
        .every((edge) => !edge.data?.parent),
    ).toBe(true);
  });
  it("keeps unrelated family context near the role holder instead of moving it to the Trust level", () => {
    const drawing = graphDrawing(evergreen, (key) => key);
    expect(box(drawing, "david").top).toBe(box(drawing, "alice").top);
    expect(box(drawing, "david").top).not.toBe(box(drawing, "trust").top);
    expect(graphDrawing(evergreen, (key) => key)).toEqual(drawing);
  });
  it("separates reciprocal parent paths and labels without altering canonical direction", () => {
    const reciprocal: Graph = {
      ...evergreen,
      relationships: [
        ...evergreen.relationships,
        { source: "bob", target: "alice", type: "parent_of", evidence_ids: [] },
      ],
    };
    const drawing = graphDrawing(reciprocal, (key) => key);
    const first = routes(drawing)[0],
      second = routes(drawing).at(-1)!;
    expect(first.points).not.toEqual([...second.points].reverse());
    expect({ x: first.x, y: first.y }).not.toEqual({
      x: second.x,
      y: second.y,
    });
    expect(drawing.edges.at(-1)).toMatchObject({
      source: "bob",
      target: "alice",
    });
    assertClearPaths(drawing);
    assertClearLabels(drawing);
    assertCompleteBounds(drawing);
  });
  it("keeps reciprocal lanes distinct in a graph without a Trust", () => {
    const graph: Graph = {
      entities: evergreen.entities.filter((entity) =>
        ["alice", "bob"].includes(entity.id),
      ),
      relationships: [
        evergreen.relationships[0],
        { source: "bob", target: "alice", type: "parent_of", evidence_ids: [] },
      ],
      evidence: [],
    };
    const drawing = graphDrawing(graph, (key) => key);
    const [forward, reverse] = routes(drawing);
    expect(forward.points).not.toEqual([...reverse.points].reverse());
    expect({ x: forward.x, y: forward.y }).not.toEqual({
      x: reverse.x,
      y: reverse.y,
    });
    expect(drawing.nodes.map((node) => node.id)).toEqual(
      graph.entities.map((entity) => entity.id),
    );
    expect(
      drawing.edges.map((edge) => [edge.id, edge.source, edge.target]),
    ).toEqual(
      graph.relationships.map((edge, index) => [
        String(index),
        edge.source,
        edge.target,
      ]),
    );
    expect(Object.values(drawing.bounds).every(Number.isFinite)).toBe(true);
    assertClearLabels(drawing);
    assertCompleteBounds(drawing);
  });
  it("represents multiple Trust roles with one Person and distinct entry points/labels", () => {
    const roles: Relationship[] = [
      "settlor_of",
      "trustee_of",
      "beneficiary_of",
    ].map((type) => ({
      source: "alice",
      target: "trust",
      type: type as Relationship["type"],
      evidence_ids: [],
    }));
    const drawing = graphDrawing(
      {
        ...evergreen,
        entities: evergreen.entities.filter((entity) =>
          ["alice", "trust"].includes(entity.id),
        ),
        relationships: roles,
      },
      (key) => key,
    );
    expect(drawing.nodes.map((node) => node.id)).toEqual(["alice", "trust"]);
    expect(drawing.edges.map((edge) => edge.label)).toEqual([
      "Settlor",
      "Trustee",
      "Beneficiary",
    ]);
    expect(
      new Set(
        routes(drawing).map((route) => JSON.stringify(route.points.at(-1))),
      ).size,
    ).toBe(3);
    assertClearPaths(drawing);
    assertClearLabels(drawing);
    assertCompleteBounds(drawing);
  });
  it("uses the general layout for multiple Trusts and reserves every caption, route and label", () => {
    const graph: Graph = {
      entities: [
        evergreen.entities[0],
        evergreen.entities[4],
        { id: "second-trust", type: "trust", name: "Second Fictional Trust" },
      ],
      relationships: [
        evergreen.relationships[1],
        {
          source: "alice",
          target: "second-trust",
          type: "trustee_of",
          evidence_ids: [],
        },
      ],
      evidence: [],
    };
    const drawing = graphDrawing(graph, (key) => key);
    expect(drawing.nodes).toHaveLength(3);
    expect(drawing.edges).toHaveLength(2);
    assertClearLabels(drawing);
    assertCompleteBounds(drawing);
  });
  it("keeps route geometry and bounds unchanged by supported label translation", () => {
    const english = graphDrawing(evergreen, (key) => key);
    const chinese = graphDrawing(
      evergreen,
      (key) =>
        ({
          Settlor: "设立人",
          Beneficiary: "受益人",
          "Parent of": "父母关系",
          "Spouse of": "配偶关系",
        })[key] ?? key,
    );
    expect(routes(chinese)).toEqual(routes(english));
    expect(chinese.bounds).toEqual(english.bounds);
  });
});
