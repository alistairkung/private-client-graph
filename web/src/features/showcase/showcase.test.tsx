import { render, screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { expect, test, vi } from "vitest";
import { App } from "../../app/App";
const summaries=[{id:"case-01",title:"Case 01",description:"One source"},{id:"case-04",title:"Case 04",description:"Two sources"}];
const detail=(id:string)=>({...summaries.find(item=>item.id===id),notice:"Curated ideal fixture",state:{sources:[{id:"a",title:"First note",text:`${id} source`}],entities:[],relationships:[],evidence:[]}});
const response=(body:unknown)=>new Response(JSON.stringify(body));

test("fixed cases load without execution and selection fetches only read-only examples",async()=>{
 const fetcher=vi.spyOn(globalThis,"fetch").mockImplementation(async url=>response(url==="/api/showcase/cases"?summaries:detail(String(url).split("/").at(-1)!)));
 render(<App/>);
 await screen.findByText("case-01 source");
 expect(screen.getByText(/Curated ideal fixtures/)).toBeVisible();
 expect(screen.queryByRole("button",{name:/live analysis/i})).not.toBeInTheDocument();
 expect(screen.queryByLabelText(/PDF/)).not.toBeInTheDocument();
 await userEvent.setup().selectOptions(screen.getByLabelText("Choose a synthetic case"),"case-04");
 await screen.findByText("case-04 source");
 expect(fetcher.mock.calls.every(([,options])=>!options?.method||options.method==="GET")).toBe(true);
});

test("failed case loading offers an explicit retry",async()=>{
 let fail=true;
 vi.spyOn(globalThis,"fetch").mockImplementation(async url=>{
  if(url==="/api/showcase/cases")return response(summaries);
  if(fail)throw new Error("offline");
  return response(detail("case-01"));
 });
 render(<App/>);
 await screen.findByRole("alert");
 fail=false;
 await userEvent.setup().click(screen.getByRole("button",{name:"Reload case"}));
 await waitFor(()=>expect(screen.getByText("case-01 source")).toBeVisible());
});
