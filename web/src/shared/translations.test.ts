import { readFileSync, readdirSync } from "node:fs";
import { dirname, join } from "node:path";
import { fileURLToPath } from "node:url";
import ts from "typescript";
import { describe, expect, it } from "vitest";
import { catalogue as chinese } from "./locale-catalogue";
import { serviceMessages } from "./service-messages";
import { fictionalPrompt } from "../features/matter-proposals/prompt";

function sourceFiles(directory: string): string[] {
  return readdirSync(directory, { withFileTypes: true }).flatMap((entry) =>
    entry.isDirectory()
      ? sourceFiles(join(directory, entry.name))
      : /\.tsx?$/.test(entry.name) && !entry.name.includes(".test.")
        ? [join(directory, entry.name)]
        : [],
  );
}
function literalKeys(expression: ts.Expression): string[] {
  if (ts.isStringLiteral(expression)) return [expression.text];
  if (ts.isConditionalExpression(expression))
    return [
      ...literalKeys(expression.whenTrue),
      ...literalKeys(expression.whenFalse),
    ];
  return [];
}
describe("complete visible workflow language coverage", () => {
  it("translates every literal workflow key, including conditional states and safe backend messages", () => {
    const keys = new Set([...Object.values(serviceMessages), fictionalPrompt]);
    for (const path of sourceFiles(
      dirname(dirname(fileURLToPath(import.meta.url))),
    )) {
      const source = ts.createSourceFile(
        path,
        readFileSync(path, "utf8"),
        ts.ScriptTarget.Latest,
        true,
      );
      function visit(node: ts.Node) {
        if (
          ts.isCallExpression(node) &&
          ts.isIdentifier(node.expression) &&
          node.expression.text === "t" &&
          node.arguments[0]
        )
          literalKeys(node.arguments[0]).forEach((key) => keys.add(key));
        ts.forEachChild(node, visit);
      }
      visit(source);
    }
    expect([...keys].filter((key) => !Object.hasOwn(chinese, key))).toEqual([]);
  });
});
