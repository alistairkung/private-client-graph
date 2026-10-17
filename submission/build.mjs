import fs from 'node:fs/promises';
import { validateResults } from './results.mjs';
import path from 'node:path';
import { fileURLToPath, pathToFileURL } from 'node:url';
import { createRequire } from 'node:module';
import { execFile } from 'node:child_process';
import { promisify } from 'node:util';

const root = path.dirname(fileURLToPath(import.meta.url));
const runtimeRoot = process.env.PCG_ARTIFACT_RUNTIME ?? '/Users/alistair/.cache/codex-runtimes/codex-primary-runtime/dependencies';
process.env.RUNTIME_NODE_MODULES ??= path.join(runtimeRoot, 'node/node_modules');
process.env.RUNTIME_NODE ??= path.join(runtimeRoot, 'node/bin/node');
const require = createRequire(path.join(runtimeRoot, 'node/node_modules/package.json'));
const { Presentation, PresentationFile } = await import(pathToFileURL(require.resolve('@oai/artifact-tool')).href);
const skill = process.env.PCG_PRESENTATIONS_SKILL ?? '/Users/alistair/.codex/plugins/cache/openai-primary-runtime/presentations/26.1013.11914/skills/presentations';
const { finalizePresentation, applyPresentationChartFont } = await import(pathToFileURL(path.join(skill, 'container_tools/artifact_tool_utils.mjs')).href);
const draft = process.argv.includes('--draft');
const stamp = new Date().toISOString().replace(/[:.]/g,'-');
const build = path.join(root,'.build',stamp);
const output = path.join(root,'output',stamp);
await fs.mkdir(build,{recursive:true});
await fs.mkdir(output,{recursive:true});
let results;
try { results=JSON.parse(await fs.readFile(path.join(root,'final-results.json'),'utf8')); }
catch(error) { if(error.code!=='ENOENT')throw error; }
if(!draft) validateResults(results);

const C={green:'#173E38',paper:'#F6F6F1',ink:'#243F39',muted:'#52665F',gold:'#EFDDA0',burgundy:'#773B46',white:'#FFFFFF'};
const FONT='Liberation Sans';
const p=Presentation.create({slideSize:{width:1280,height:720}});
p.theme.defaultFont = FONT;
function text(slide,value,x,y,w,h,size=28,color=C.ink,bold=false){
  const box=slide.shapes.add({geometry:'textbox',position:{left:x,top:y,width:w,height:h},fill:'none',line:{fill:'none',width:0}});
  box.text=value;
  box.text.style={typeface:FONT,fontSize:size,color,bold,verticalAlignment:'top',insets:0};
  return box;
}
function slide(title,notes=''){
 const s=p.slides.add();s.background.fill=C.paper;
 text(s,title,64,46,1152,66,44,C.green,true);
 if(draft)text(s,'Draft for review. Evaluation and deployment approval remain pending.',64,676,1080,26,16,C.burgundy);
 else text(s,'Private Client Graph   •   Synthetic research prototype',64,676,1080,26,16,C.muted);
 text(s,String(p.slides.items.length),1170,676,40,26,16,C.muted);
 s.speakerNotes.text=notes;
 return s;
}
async function image(s,filename,x,y,w,h,crop){
 const bytes=await fs.readFile(path.join(root,'assets',filename));
 return s.images.add({blob:bytes,contentType:'image/png',fit:'contain',crop,position:{left:x,top:y,width:w,height:h},alt:filename});
}
function node(s,label,x,y,w,h,fill=C.white){
 const n=s.shapes.add({geometry:'rect',position:{left:x,top:y,width:w,height:h},fill,line:{fill:C.muted,width:1}});
 n.text=label;n.text.style={typeface:FONT,fontSize:25,color:C.green,bold:true,alignment:'center',verticalAlignment:'middle',insets:14};
 return n;
}
function connect(s,a,b,from='right',to='left') { s.shapes.connect(a,b,{fromSide:from,toSide:to,kind:'straight',line:{fill:C.muted,width:2},head:{type:'none'},tail:{type:'triangle',width:'sm',length:'sm'}}); }
const pct=n=>n===null?'Unavailable':`${(n*100).toFixed(1)}%`;

// 1. A simple cover with the product's actual scope.
{
 const s=slide('', 'Project scope: docs/design/final-build-day.md. Synthetic material only. Deck figures must come from retained final Runs.');
 s.background.fill=C.green;
 text(s,'Private Client\nGraph',72,132,1050,220,82,C.white,true);
 text(s,'Reviewable family and trust relationships\nfrom private-client source documents',76,396,1050,100,34,C.white);
 text(s,'FTEC5660 hackathon\n17 October 2026',76,560,1000,70,23,C.white);
 if(draft)text(s,'Draft for review',950,605,265,40,24,C.white);
}
// 2. The problem is professional traceability, not generic graph visualization.
{
 const s=slide('The source-review problem','Sources: GLOSSARY.md; PRODUCT.md; cases/case_01/source.txt. The quoted sentence is a synthetic fixture. No efficiency or market-size claim.');
 text(s,'Family and trust facts span notes, letters and later updates.',64,145,580,105,34,C.green,true);
 text(s,'A graph makes connections visible. A solicitor still needs to inspect the words that support each relationship and distinguish a current appointment from an earlier one.',64,285,570,230,28);
 text(s,'“Alice Chen confirmed that Bob Chen is a beneficiary of the Evergreen Family Trust.”',720,180,470,210,36,C.green);
 text(s,'Case 01, synthetic attendance note',720,430,470,70,23,C.muted);
 text(s,'Project objective: produce inspectable proposed relationships for professional review.',64,565,1120,72,30,C.green,true);
}
// 3. Real screenshot of the fixed showcase, clearly distinguished from a measured Run.
{
 const s=slide('Evidence beside the relationship graph','Screenshot: local P6 deterministic browser run on 17 October 2026. Source: submission/assets/showcase-case-04.png. Curated ideal fixture, not a recorded model result or deployed build.');
 text(s,'Select a relationship, choose its Evidence and inspect the exact passage in the correct Source.',64,150,340,230,29,C.green,true);
 text(s,'Practitioners review a saved proposal before confirming the whole graph as current Matter state.',64,425,340,170,26);
 await image(s,'showcase-case-04.png',430,135,790,495,{left:0.28,top:0.58,right:0.08,bottom:0.055});
 text(s,'Local public showcase. Curated synthetic Case 04.',430,635,790,30,18,C.muted);
}
// 4. Explicitly requested editable architecture diagram.
{
 const s=slide('System architecture','Sources: docs/CODE_STYLE.md; ADR0008; ADR0009; approved final-build-day design. Fixed Extract/Resolve/Construct topology. Application uses approved no-resolution configuration.');
 const src=node(s,'Ordered Sources\nFinal PDF text',64,175,210,100);
 const llm=node(s,'Extract\nOne full-context call',332,175,240,100,C.gold);
 const resolver=node(s,'Resolve\nNo-resolution config',630,175,240,100);
 const graph=node(s,'Construct\nDeterministic validation',928,175,288,100);
 connect(s,src,llm);connect(s,llm,resolver);connect(s,resolver,graph);
 const proposal=node(s,'Matter Proposal\nSource-aware relational facts',750,360,466,105);
 connect(s,graph,proposal,'bottom','top');
 const matter=node(s,'Accepted Matter\nWhole-proposal confirmation',750,530,466,100);
 connect(s,proposal,matter,'bottom','top');
 text(s,'Model interprets semantics',64,355,540,50,29,C.green,true);
 text(s,'Code validates identity, types, exact quotes, support and deduplication. PostgreSQL preserves Source attribution and aggregate integrity.',64,420,575,170,27);
}
// 5. Explain source correctness and exact quote correctness separately.
{
 const s=slide('Source identity travels with Evidence','Sources: canonical_state.py; models/source.py; models/sourced_evidence.py; cases/case_04/source_evidence.json. Title is display text, not source identity.');
 text(s,'A quote carries an explicit Source ID. Repeated titles and repeated words do not identify the document.',64,145,1120,80,32,C.green,true);
 const a=node(s,'note_01\nInitial attendance note',64,285,340,98);
 const b=node(s,'note_02\nFollow-up attendance note',64,452,340,98);
 const relation=node(s,'Andrew Chan\nbeneficiary of\nHillcrest Family Trust',730,345,460,145,C.gold);
 connect(s,a,relation);connect(s,b,relation);
 text(s,'One canonical relationship can retain support from both Sources.',64,585,1120,60,29);
 text(s,'Exact quote occurrence checks mechanical provenance. It does not prove that the passage entails the relationship.',465,170,1,1,1);
 // Full source citation and the semantic caveat stay in the visible note below.
 text(s,'Exact-text validation checks occurrence. Professional review checks meaning.',465,525,720,75,24,C.muted);
}
// 6. Temporal interpretation stays inside semantic extraction.
{
 const s=slide('Explicit updates define the current trustee','Sources: cases/case_05/sources/note_01.txt and note_02.txt. Source-aware expected_state.json is an authored ideal. Dates refer to fictional events.');
 const first=node(s,'1 September\nDavid Ng is sole trustee',64,180,475,110);
 const later=node(s,'15 September\nRachel Lim is sole trustee',741,180,475,110,C.gold);
 connect(s,first,later);
 text(s,'Replacement effective 10 September',420,325,690,50,29,C.green,true);
 text(s,'The final current graph retains Rachel’s trustee edge and the five unchanged family and trust relationships.',64,425,720,150,31);
 text(s,'The source documents retain the historical statement. The application adds no event store or historical-date selector.',850,420,350,170,25,C.muted);
}
// 7. Actual research UI is optional while it is being captured, never fabricated.
{
 const s=slide('Research Workbench and evaluation','Sources: README.md Research Workbench; docs/design/final-build-day.md; research/final-day/validation. Deterministic tests substitute only the model boundary.');
 const workbench=await fs.access(path.join(root,'assets','workbench.png')).then(()=>true,()=>false);
 if(workbench){
  await image(s,'workbench.png',585,145,630,420);
  text(s,'Current Workbench interface. Screenshot context appears in the asset manifest.',585,580,630,65,19,C.muted);
 }
 text(s,'Five development cases exercise the chain. Ten separate synthetic cases form the proposed held-out benchmark.',64,145,workbench?460:1100,160,30,C.green,true);
 text(s,'A Run preserves inputs, configuration, extracted candidates, stage outcomes and deterministic evaluation artifacts.',64,350,workbench?460:1100,140,27);
 text(s,'Relationship P/R/F1 compare semantic edges. Approved-quote accuracy checks true-positive edges. Source attribution evaluates assessed Evidence items separately.',64,520,workbench?460:1100,120,24);
}
// 8. Results are populated exclusively from actual retained final Runs.
{
 const s=slide(results?'Held-out extraction results':'Held-out benchmark status',results?`Run IDs: ${results.run_ids.join(', ')}\nFrozen commit: ${results.frozen_commit}\nModel: ${results.model}\nArtifacts: ${results.artifacts.join(', ')}`:'No held-out Run has been supplied. This draft makes no final extraction-quality claim. Authored ideal fixtures do not measure model performance.');
 if(results){
  const a=results.aggregate;
  text(s,`Precision ${pct(a.precision)}     Recall ${pct(a.recall)}     F1 ${pct(a.f1)}`,64,140,1150,55,33,C.green,true);
  const scored=results.cases.filter(c=>Number.isFinite(c.f1));
  const chart=s.charts.add('bar',{position:{left:64,top:235,width:780,height:320},categories:scored.map(c=>c.id.replace('heldout_','')),series:[{name:'Relationship F1',values:scored.map(c=>c.f1),fill:C.green}],hasLegend:false,barOptions:{direction:'column',grouping:'clustered'},dataLabels:{showValue:true,position:'outEnd',numberFormatCode:'0%'},yAxis:{minimumScale:0,maximumScale:1,numberFormatCode:'0%',majorGridlines:{fill:'#D5D9D2',width:1}},xAxis:{textStyle:{typeface:FONT,fontSize:22}},chartFill:'none',plotAreaFill:'none'});
  applyPresentationChartFont(chart,{fontFamily:FONT});
  text(s,`${results.scored_cases}/${results.planned_cases} cases scored\n${results.attempts} provider attempts\nCost ${results.cost_usd===null?'unavailable':`US$${results.cost_usd.toFixed(4)}`}`,900,250,300,175,27);
  text(s,`Approved-quote accuracy ${pct(a.quote_provenance_accuracy)} per true-positive edge\nSource attribution ${pct(a.source_attribution_accuracy)} per assessed Evidence item`,64,585,1140,65,23,C.muted);
 }else{
  text(s,'10 synthetic cases\n39 current relationships',64,155,1120,150,52,C.green,true);
  text(s,'Independent fixture review covers exact Source attribution and supported current relationships. Benchmark approval and the frozen-chain evaluation remain pending.',64,370,1100,145,31);
  text(s,'No held-out precision, recall, F1 or provider cost is claimed in this draft.',64,565,1100,70,27,C.burgundy);
 }
}
// 9. Disclose limits and preserve real failure examples once known.
{
 const s=slide('Findings and limitations','Sources: AGENTS.md; synthetic authoring workflow; independent case-review summaries; retained Run failures when supplied. Current authentication does not authorize real confidential client data.');
 const failures=results?.failures??[];
 text(s,failures.length?'Observed failure cases':'Limits of the current evidence',64,145,1120,50,32,C.green,true);
 if(failures.length){
  failures.slice(0,2).forEach((f,i)=>text(s,`${f.case_id} (${f.stage})\n${f.description}`,64,235+i*145,1120,125,27));
 }else{
  text(s,'The held-out examples are small, explicit and synthetic. They test specific difficulties and offer limited evidence of robustness on practice documents.',64,235,1120,120,29);
  text(s,'Exact occurrence and approved-quote scoring cannot establish legal correctness. Curated examples demonstrate review behaviour, not extraction accuracy.',64,395,1120,120,29);
 }
 text(s,'Synthetic material only. Text-layer PDFs only. Whole-proposal confirmation. Real client use needs a separate data-handling and tenancy design.',64,575,1120,72,25,C.muted);
}
// 10. The link and deployment status are factual, not a promise of deployment.
{
 const url=results?.demo_url??'https://private-client-graph-production.up.railway.app';
 const verified=results?.deployment_verified===true;
 const s=slide('Conclusion and demonstration',`Public deployment URL: ${url}\nMulti-source public deployment verified: ${verified}. Local screenshot assets demonstrate the reviewed P6 build. Current deployed service predates that build unless verification is supplied.`);
 text(s,'A bounded extraction system with inspectable Evidence and explicit professional confirmation',64,145,1110,145,39,C.green,true);
 text(s,'The next evidence should come from broader documents and practitioner feedback. Real-client ingestion requires a separately approved security and data design.',64,365,1110,115,30);
 text(s,url,64,535,1150,45,27,C.green,true);
 text(s,verified?'Open the public page, choose Case 01, 04 or 05, then select a relationship and follow its Evidence.': 'The public service currently has the earlier Case 01 demo. The reviewed multi-source build remains a local preview pending deployment approval.',64,590,1135,65,24,C.muted);
}

for (const [index,s] of p.slides.items.entries()) {
 const png=await p.export({slide:s,format:'png',scale:1});
 await fs.writeFile(path.join(build,`slide-${String(index+1).padStart(2,'0')}.png`),new Uint8Array(await png.arrayBuffer()));
}
await fs.writeFile(path.join(build,'montage.webp'),new Uint8Array(await (await p.export({format:'webp',montage:true})).arrayBuffer()));
const candidate=path.join(build,'candidate.pptx');
await (await PresentationFile.exportPptx(p)).save(candidate);
const final=path.join(output,draft?'private-client-graph-draft.pptx':'private-client-graph.pptx');
await finalizePresentation({workspaceDir:root,candidatePath:candidate,finalPath:final,pythonExecutable:path.join(runtimeRoot,'python/bin/python3'),integrityValidatorPath:path.join(skill,'container_tools/inspect_presentation_package_integrity.py'),layoutValidatorPath:path.join(skill,'container_tools/inspect_presentation_layout_geometry.py'),layoutArgs:['--expected-slide-size-emu','12192000,6858000','--validate-bullet-geometry','--validate-heading-fit'],explicitTotalSlideCount:10,requiredNativeTableOwnerSlides:[],requiredNativeChartOwnerSlides:results?[8]:[],materializeLiteralChartWorkbooks:true,fontPolicy:{basis:'design',families:[FONT]},verifyArtifactToolImport:true,receiptPath:path.join(build,'validation.json')});
try {
  await fs.writeFile(path.join(output,draft?'private-client-graph-draft.pdf':'private-client-graph.pdf'),new Uint8Array(await (await p.export({format:'pdf'})).arrayBuffer()));
} catch (error) {
  // The bundled Artifact Tool PDF exporter can lack its standard-font module.
  // Convert the validated editable PPTX with the bundled office renderer instead.
  console.warn(`Artifact PDF export unavailable: ${error.message}`);
  await promisify(execFile)(path.join(runtimeRoot,'bin/override/soffice'),[
    `-env:UserInstallation=${pathToFileURL(path.join(build,'office-profile')).href}`,
    '--headless','--convert-to','pdf','--outdir',output,final
  ]);
}
await fs.writeFile(path.join(root,'latest-build.json'),JSON.stringify({draft,output,previews:build,pptx:final,pdf:path.join(output,draft?'private-client-graph-draft.pdf':'private-client-graph.pdf')},null,2)+'\n');
console.log(JSON.stringify({draft,output,previews:build,pptx:final}));
