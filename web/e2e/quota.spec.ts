import { expect, test } from "@playwright/test";
test("configured public live execution remains closed and all fixed examples work",async({page})=>{
 const writes:string[]=[];
 page.on("request",request=>{if(request.method()!=="GET")writes.push(request.url());});
 await page.goto("/");
 await expect(page.getByRole("button",{name:/live analysis/i})).toHaveCount(0);
 for(const id of ["case-04","case-05","case-01"]){
  await page.getByLabel("Choose a synthetic case").selectOption(id);
  await expect(page.getByLabel("Relationship graph")).toBeVisible();
  await expect(page.getByRole("navigation",{name:"Sources"}).getByRole("button")).toHaveCount(id==="case-01"?1:2);
 }
 expect(writes).toEqual([]);
 const rejected=await page.request.post("/api/showcase/case-01/analysis",{data:{mode:"live"}});
 expect(rejected.status()).toBe(403);
});
