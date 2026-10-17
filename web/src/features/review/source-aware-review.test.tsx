import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { expect, test, vi } from "vitest";
import type { CanonicalState } from "../../shared/canonical-state";
import { evidenceSource } from "./source-aware-review";
import { SourceAwareReviewWorkspace } from "./SourceAwareReviewWorkspace";
vi.mock("./GraphView", () => ({
 GraphView: ({onSelect}:{onSelect:(index:number)=>void}) => <button onClick={()=>onSelect(0)}>Select relationship</button>
}));
const state:CanonicalState={
 sources:[{id:"a",title:"Same title",text:"First source. Alex is trustee."},{id:"b",title:"Same title",text:"Second source. Alex is trustee."}],
 entities:[{id:"p",type:"person",name:"Alex"},{id:"t",type:"trust",name:"Cedar"}],
 relationships:[{source:"p",type:"trustee_of",target:"t",evidence_ids:["q1","q2"]}],
 evidence:[{id:"q1",source_id:"a",document:"Same title",supporting_text:"Alex is trustee."},{id:"q2",source_id:"b",document:"Same title",supporting_text:"Alex is trustee."}]
};
test("Source identity controls identical quote attribution, never title or first quote match",()=>{
 expect(evidenceSource(state,state.evidence[1]).source.id).toBe("b");
 expect(()=>evidenceSource(state,{...state.evidence[1],source_id:"missing"})).toThrow(/Source/);
 expect(()=>evidenceSource({...state,sources:[state.sources[0],{...state.sources[1],text:"No quote"}]},state.evidence[1])).toThrow();
});
test("choosing Evidence activates its Source, source browsing never misattributes its highlight",async()=>{
 render(<SourceAwareReviewWorkspace state={state}/>);
 const user=userEvent.setup();
 await user.click(screen.getByRole("button",{name:"Select relationship"}));
 await user.click(screen.getByRole("button",{name:/Evidence 2/}));
 expect(screen.getByLabelText("Source document")).toHaveTextContent("Second source");
 expect(document.querySelector("mark")).toHaveTextContent("Alex is trustee.");
 expect(screen.getByRole("button",{name:"Source 2 Same title"})).toHaveAttribute("aria-pressed","true");
 await user.click(screen.getByRole("button",{name:"Source 1 Same title"}));
 expect(screen.getByLabelText("Source document")).toHaveTextContent("First source");
 expect(document.querySelector("mark")).toBeNull();
 await user.click(screen.getByRole("link",{name:"View in source"}));
 expect(screen.getByLabelText("Source document")).toHaveTextContent("Second source");
 expect(document.querySelector("mark")).toHaveFocus();
});
