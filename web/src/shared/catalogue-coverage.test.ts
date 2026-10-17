import { readFileSync, readdirSync } from "node:fs";
import { resolve } from "node:path";
import ts from "typescript";
import { expect, it } from "vitest";
import { catalogue } from "./locale-catalogue";
import { translate } from "./locale";

function sourceFiles(directory: string): string[] {
  return readdirSync(directory, {withFileTypes:true}).flatMap(entry => {
    const path = resolve(directory, entry.name);
    if (entry.isDirectory()) return entry.name === "research" ? [] : sourceFiles(path);
    return /\.tsx?$/.test(entry.name) && !/\.test\./.test(entry.name) ? [path] : [];
  });
}

it("covers application translation keys, safe dynamic error messages and case instructions", () => {
  const keys = new Set<string>();
  for (const path of sourceFiles(resolve(import.meta.dirname, ".."))) {
    const file = ts.createSourceFile(path, readFileSync(path,"utf8"), ts.ScriptTarget.Latest, true);
    function visit(node: ts.Node) {
      if (ts.isCallExpression(node) && ts.isIdentifier(node.expression) && node.expression.text === "t") {
        const key = node.arguments[0];
        if (key && ts.isStringLiteralLike(key)) keys.add(key.text);
      }
      if (path.endsWith("error-presentation.ts")) {
        if (ts.isReturnStatement(node) && node.expression && ts.isStringLiteralLike(node.expression)) keys.add(node.expression.text);
        if (ts.isVariableDeclaration(node) && node.name.getText(file) === "messages" && node.initializer && ts.isObjectLiteralExpression(node.initializer)) {
          for (const message of node.initializer.properties) {
            if (ts.isPropertyAssignment(message) && ts.isStringLiteralLike(message.initializer)) keys.add(message.initializer.text);
          }
        }
        if (ts.isBinaryExpression(node) && node.operatorToken.kind === ts.SyntaxKind.QuestionQuestionToken && ts.isStringLiteralLike(node.right)) keys.add(node.right.text);
      }
      ts.forEachChild(node,visit);
    }
    visit(file);
  }
  const summaries = readFileSync(resolve(import.meta.dirname,"../../../private_client_graph/application/showcase_cases.py"),"utf8");
  for (const match of summaries.matchAll(/description="([^"]+)"/g)) keys.add(match[1]);
  expect([...keys].filter(key => !catalogue[key]), "Missing Simplified Chinese interface text").toEqual([]);
});

it("retains interpolation values in every English and Chinese catalogue entry", () => {
  const placeholders = (text:string) => [...text.matchAll(/\{(\w+)\}/g)].map(match=>match[1]).sort();
  for (const [english,chinese] of Object.entries(catalogue)) {
    expect(placeholders(chinese),english).toEqual(placeholders(english));
  }
  expect(translate("zh-CN","Evidence from Source {number}:",{number:2})).toBe("证据来自来源 2：");
});
