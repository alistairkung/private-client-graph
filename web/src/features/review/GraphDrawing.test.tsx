import { readFileSync } from "node:fs";
import { dirname, join } from "node:path";
import { fileURLToPath } from "node:url";
import {
  PERSON_HEIGHT,
  TRUST_HEIGHT,
  TRUST_LABEL_HEIGHT,
} from "./node-geometry";
import { type ReactNode } from "react";
import { afterEach, describe, expect, it, vi } from "vitest";
import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import type { Edge, EdgeProps, Node, NodeProps } from "@xyflow/react";
import { GraphDrawing } from "./GraphDrawing";
import { graphDrawing } from "./graph-layout";
import type { CanonicalState } from "../../shared/contracts";
import { LocaleProvider, useLocale } from "../../shared/locale";

const diagramStyles = readFileSync(
  join(dirname(fileURLToPath(import.meta.url)), "review.css"),
  "utf8",
);

const camera = vi.hoisted(() => ({
  fitBounds: vi.fn(),
  zoomIn: vi.fn(),
  zoomOut: vi.fn(),
}));
vi.mock("@xyflow/react", async (importOriginal) => {
  const actual = await importOriginal<typeof import("@xyflow/react")>();
  const react = await import("react");
  return {
    ...actual,
    ReactFlowProvider: ({ children }: { children: ReactNode }) => children,
    EdgeLabelRenderer: ({ children }: { children: ReactNode }) => children,
    BaseEdge: () => react.createElement("span"),
    Handle: () => react.createElement("span"),
    useReactFlow: () => ({ ...camera, viewportInitialized: true }),
    useStore: (
      selector: (state: { width: number; height: number }) => unknown,
    ) => selector({ width: 800, height: 560 }),
    ReactFlow: ({
      edges,
      edgeTypes,
      nodes,
      nodeTypes,
      children,
    }: {
      edges: Edge[];
      nodes: Node[];
      nodeTypes: Record<string, (props: NodeProps) => ReactNode>;
      edgeTypes: Record<string, (props: EdgeProps) => ReactNode>;
      children: ReactNode;
    }) =>
      react.createElement(
        "div",
        null,
        ...nodes.map((node) =>
          react.createElement(
            "div",
            { key: "node-" + node.id, "aria-label": node.ariaLabel },
            react.createElement(nodeTypes[node.type!], {
              id: node.id,
              data: node.data,
              type: node.type!,
              dragging: false,
              zIndex: 0,
              selectable: true,
              deletable: false,
              selected: Boolean(node.selected),
              draggable: false,
              isConnectable: false,
              positionAbsoluteX: node.position.x,
              positionAbsoluteY: node.position.y,
            }),
          ),
        ),
        ...edges.map((edge) =>
          react.createElement(edgeTypes[edge.type!], {
            ...edge,
            markerStart: undefined,
            markerEnd: undefined,
            key: edge.id,
            sourceX: 0,
            sourceY: 0,
            targetX: 0,
            targetY: 0,
            sourcePosition: actual.Position.Bottom,
            targetPosition: actual.Position.Top,
            selectable: true,
            deletable: false,
          }),
        ),
        children,
      ),
  };
});
const graph: CanonicalState = {
  sources: [],
  evidence: [],
  entities: [
    { id: "alice", type: "person", name: "Alice Chen" },
    { id: "trust", type: "trust", name: "Evergreen Family Trust" },
  ],
  relationships: [
    {
      source: "alice",
      target: "trust",
      type: "settlor_of",
      evidence_ids: ["first"],
    },
    {
      source: "alice",
      target: "trust",
      type: "trustee_of",
      evidence_ids: ["second"],
    },
  ],
};
afterEach(() => {
  vi.clearAllMocks();
  try {
    localStorage.clear();
  } catch {
    /* Optional preference storage. */
  }
});
describe("keyboard graph actions and camera continuity", () => {
  it("keeps full long canonical names in accessible labels and native title while diagram previews stay bounded", () => {
    const personName =
      "Completely Fictional Person With A Very Long Canonical Name "
        .repeat(3)
        .trim();
    const trustName =
      "Completely Fictional Family Trust With A Very Long Canonical Name "
        .repeat(3)
        .trim();
    const longGraph = {
      ...graph,
      entities: [
        { ...graph.entities[0], name: personName },
        { ...graph.entities[1], name: trustName },
      ],
    };
    render(
      <>
        <style>{diagramStyles}</style>
        <GraphDrawing
          state={longGraph}
          selected={null}
          selectedEntity={null}
          onSelect={vi.fn()}
          onEntity={vi.fn()}
        />
      </>,
    );
    const personPreview = screen
      .getByTitle(personName)
      .querySelector("strong")!;
    const trustPreview = screen.getByTitle(trustName).querySelector("strong")!;
    const personStyle = getComputedStyle(personPreview);
    const trustStyle = getComputedStyle(trustPreview);
    expect(personStyle.overflow).toBe("hidden");
    expect(personStyle.getPropertyValue("-webkit-line-clamp")).toBe("2");
    expect(parseFloat(personStyle.maxHeight) + 16).toBeLessThanOrEqual(
      PERSON_HEIGHT,
    );
    expect(trustStyle.overflow).toBe("hidden");
    expect(trustStyle.getPropertyValue("-webkit-line-clamp")).toBe("2");
    expect(
      parseFloat(trustStyle.top) + parseFloat(trustStyle.maxHeight),
    ).toBeLessThanOrEqual(TRUST_HEIGHT + TRUST_LABEL_HEIGHT);
    expect(
      screen.getByTitle(personName).querySelector("strong")?.textContent,
    ).toBe(personName);
    expect(
      screen.getByTitle(trustName).querySelector("strong")?.textContent,
    ).toBe(trustName);
    expect(screen.getByLabelText(personName)).toBeInTheDocument();
    expect(screen.getByLabelText(trustName)).toBeInTheDocument();
    expect(
      screen.getByRole("button", {
        name: personName + " — settlor of — " + trustName,
      }),
    ).toBeInTheDocument();
  });
  it("offers each connector as a keyboard button with complete canonical names and stable selection index", async () => {
    const onSelect = vi.fn();
    const { rerender } = render(
      <GraphDrawing
        state={graph}
        selected={null}
        selectedEntity={null}
        onSelect={onSelect}
        onEntity={vi.fn()}
      />,
    );
    const first = screen.getByRole("button", {
      name: "Alice Chen — settlor of — Evergreen Family Trust",
    });
    expect(first).toHaveTextContent("Settlor");
    expect(first).toHaveAttribute("aria-pressed", "false");
    first.focus();
    await userEvent.keyboard("{Enter}");
    expect(onSelect).toHaveBeenCalledWith(0);
    const second = screen.getByRole("button", {
      name: "Alice Chen — trustee of — Evergreen Family Trust",
    });
    second.focus();
    await userEvent.keyboard(" ");
    expect(onSelect).toHaveBeenLastCalledWith(1);
    rerender(
      <GraphDrawing
        state={graph}
        selected={1}
        selectedEntity={null}
        onSelect={onSelect}
        onEntity={vi.fn()}
      />,
    );
    expect(
      screen.getByRole("button", {
        name: "Alice Chen — trustee of — Evergreen Family Trust",
      }),
    ).toHaveAttribute("aria-pressed", "true");
    expect(camera.fitBounds).toHaveBeenCalledTimes(1);
  });
  it("fits the complete drawing bounds including routes, labels and Trust captions", async () => {
    render(
      <GraphDrawing
        state={graph}
        selected={null}
        selectedEntity={null}
        onSelect={vi.fn()}
        onEntity={vi.fn()}
      />,
    );
    expect(camera.fitBounds).toHaveBeenCalledWith(
      graphDrawing(graph, (key) => key).bounds,
      { padding: 0.05 },
    );
    await userEvent.click(screen.getByRole("button", { name: "Fit graph" }));
    expect(camera.fitBounds).toHaveBeenCalledTimes(2);
    expect(screen.getByLabelText("Graph legend")).toHaveTextContent(
      "Trust role",
    );
    expect(screen.getByLabelText("Graph legend")).toHaveTextContent(
      "Parent to child",
    );
    expect(screen.getByLabelText("Graph legend")).toHaveTextContent(
      "Spouse or sibling",
    );
  });
  it("changes visible connector language without resetting the camera", async () => {
    function Switch() {
      const { setLocale } = useLocale();
      return (
        <button onClick={() => setLocale("zh-CN")}>Switch language</button>
      );
    }
    render(
      <LocaleProvider>
        <Switch />
        <GraphDrawing
          state={graph}
          selected={null}
          selectedEntity={null}
          onSelect={vi.fn()}
          onEntity={vi.fn()}
        />
      </LocaleProvider>,
    );
    await userEvent.click(
      screen.getByRole("button", { name: "Switch language" }),
    );
    expect(
      screen.getByRole("button", {
        name: "Alice Chen — 为其设立人 — Evergreen Family Trust",
      }),
    ).toHaveTextContent("设立人");
    expect(camera.fitBounds).toHaveBeenCalledTimes(1);
  });
});
