"""A self-contained research report rendered exclusively from saved observations."""
import html
import json
from typing import Any

from .artifacts import Bundle
from .chart import f1_chart
from .summary import summarize

STYLE = """
:root{color-scheme:light;--ink:#173e38;--muted:#52665f;--rule:#d5d9d2;--accent:#773b46;--paper:#f6f6f1}
*{box-sizing:border-box}body{margin:0;background:var(--paper);color:var(--ink);font:16px/1.55 Arial,sans-serif}
main{max-width:1180px;margin:auto;padding:48px 32px 80px}header{max-width:78ch;margin-bottom:42px}
h1,h2{font-family:Georgia,serif;font-weight:400;line-height:1.16}h1{font-size:clamp(32px,5vw,54px);margin:0 0 18px}
h2{font-size:30px;margin:0 0 12px}h3{font-size:18px;margin-top:28px}p{max-width:76ch}a{color:var(--accent);text-underline-offset:4px}
nav{display:flex;gap:24px;flex-wrap:wrap}nav a{padding:10px 0}section{margin:48px 0}.notice{padding:16px 20px;background:#efdda0;border-radius:5px}
.caption{color:var(--muted)}.plot{background:white;padding:18px;border:1px solid var(--rule);border-radius:5px}
svg{width:100%;height:auto;display:block}svg text{font:14px Arial,sans-serif;fill:var(--muted)}.grid{stroke:#e1e5df;stroke-width:1}
.baseline{stroke:var(--ink);stroke-width:2;stroke-dasharray:7 5;fill:white}.resolver{stroke:var(--accent);stroke-width:2;fill:var(--accent)}
.point{stroke-dasharray:none}.range{stroke:var(--accent);stroke-width:1.5;fill:none}.legend{display:flex;gap:28px;flex-wrap:wrap;font-size:14px}.legend span:first-child{color:var(--ink)}.legend span:last-child{color:var(--accent)}
.table-scroll{overflow-x:auto}table{width:100%;border-collapse:collapse;font-size:14px;margin:16px 0;font-variant-numeric:tabular-nums}
th,td{text-align:right;padding:12px 10px;border-bottom:1px solid var(--rule);white-space:nowrap}th:first-child,td:first-child{text-align:left}th{font-weight:600}caption{text-align:left;color:var(--muted);padding:8px 0}
.details{margin-top:18px}details{border-top:1px solid var(--rule);padding:12px 0}summary{cursor:pointer;min-height:32px;overflow-wrap:anywhere}
pre{white-space:pre-wrap;overflow-wrap:anywhere;padding:18px;background:white;font-size:12px;color:var(--ink)}:focus-visible{outline:3px solid var(--accent);outline-offset:4px}::selection{background:#efdda0;color:var(--ink)}
@media(max-width:650px){main{padding:26px 16px}.plot{padding:4px}section{margin:32px 0}h2{font-size:26px}}
@media print{body{background:white}main{padding:0}.table-scroll{overflow:visible}details{break-inside:avoid}nav{display:none}}
"""


def render_report(bundle: Bundle) -> str:
    report = summarize(bundle)
    mode = ('Deterministic demonstration — substitute responses, not provider performance.'
            if report['kind'] == 'demonstration' else
            'Task A development diagnostics — not the evaluation pilot.' if report['kind'] == 'task_a_diagnostic'
            else 'Development pilot — descriptive evidence, not a reliability estimate.')
    operations = report['operations']
    sections = [_cohort_section(report, cohort) for cohort in report['cohorts']]
    provenance = {k: v for k, v in report['provenance'].items() if k != 'code'}
    return f'''<!doctype html><html lang="en"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1"><title>Alias resolution experiment · Private Client Graph</title>
<style>{STYLE}</style></head><body><main>
<header><h1>Does alias resolution earn its place?</h1>
<p>Private Client Graph compares the unchanged extraction with a full-Source generative resolver. Every comparison shares its extraction, graph construction and evaluation.</p>
<p class="notice">{html.escape(mode)}</p>
<p class="caption">Model: {html.escape(report['model'])}<br>Experiment: {html.escape(report['experiment_id'])}</p>
<nav aria-label="Report sections">{''.join(f'<a href="#{c}">{c.capitalize()} inputs</a>' for c in report['cohorts'])}<a href="#operations">Cost and execution</a><a href="#method">Method and provenance</a></nav></header>
{''.join(sections)}
<section id="operations"><h2>Cost and execution</h2>
<p>{operations['attempted']} attempted calls of {report['planned_provider_attempts']} planned; cap {report['call_cap']}. {operations['paid_attempts']} paid attempts. {operations['provider_failed_attempts']} provider failures; {operations['uncertain_attempts']} uncertain attempts.</p>
<p>Estimated experiment spend: {_number(operations['estimated_spend'], 6)} {html.escape((report['configuration'].get('pricing') or {}).get('currency', ''))}. {operations['unpriced_attempts']} attempts lack sufficient pricing or usage. Known partial cost: {_number(operations['known_cost_sum'], 6)}. Unknown is not zero.</p>
{_usage_table(operations['tokens'])}
<p>Provider latency per attempt: mean {_number(operations['provider_latency']['mean'])} s; sample SD {_number(operations['provider_latency']['standard_deviation'])} s. Returned models: {html.escape(', '.join(operations['returned_models']) or 'Unavailable')}.</p>
{_details('Attempt statuses, raw observations and usage', operations['attempts'])}
{_details('Execution checkpoints and stop reasons', report['sessions'])}</section>
<section id="method"><h2>Method and provenance</h2>
<p>Each resolver repetition uses the same saved extraction. Resolver mean and range describe all scored repetitions; failed scores remain missing. Sample index is not elapsed time. Three repetitions do not establish reliability.</p>
<p>Cohort summaries give each input equal weight. Between-input variation of resolver means is separate from within-input variation. Identity diagnostics compare annotated endpoint pairs, not counts of people. Unannotated inputs have no identity score. Provenance accuracy applies only to matched relationships.</p>
<p>Authored challenges measure targeted behavior, not real-world error prevalence. Existing name-based evaluation cannot distinguish different people with identical names. No statistical significance or unseen-test generalisation is claimed.</p>
<p>Incremental cost is resolver-only. Single-pipeline estimates add one extraction to one resolver attempt; reused extractions are not charged again as experiment spend. Authored extraction cost is unavailable. Historical elapsed time includes local processing and has no recorded price.</p>
<p>Pipeline latency sums extraction provider time, resolver provider and edit time, graph construction and evaluation. It excludes artifact I/O and research identity diagnostics. Historical elapsed time cannot be split into stages, so its comparable pipeline estimates remain unavailable.</p>
{_details('Configuration and pricing metadata', report['configuration'])}
{_details('Code revision, dependencies and prompt snapshots', provenance)}
{_details('Fixture versions, hashes and annotation provenance', [s.model_dump(mode='json') for s in bundle.plan.inputs])}
</section></main></body></html>'''


def _number(value: Any, places: int = 3) -> str:
    return 'Unavailable' if value is None else f'{value:.{places}f}'


def _details(title: str, value: Any) -> str:
    return f'<details><summary>{html.escape(title)}</summary><pre>{html.escape(json.dumps(value, indent=2, ensure_ascii=False))}</pre></details>'


def _cohort_section(report: dict[str, Any], cohort: str) -> str:
    samples = [s for s in report['samples'] if s['cohort'] == cohort]
    stats = report['cohorts'][cohort]
    rows = []
    for index, sample in enumerate(samples, 1):
        baseline = (sample['baseline'].get('evaluation') or {}).get('f1')
        metrics = sample['resolver_metrics']
        cells = [html.escape(f"{index}. {sample['sample_id']}"), _number(baseline),
                 _number(metrics['f1']['mean']), _number(metrics['f1']['standard_deviation']),
                 _number(metrics['f1']['minimum']), _number(sample['paired_deltas']['mean']),
                 f"{sample['scored_repetitions']}/{len(sample['repetitions'])}", str(sample['failed_repetitions'])]
        rows.append('<tr>'+''.join(f'<td>{c}</td>' for c in cells)+'</tr>')
    return f'''<section id="{cohort}"><h2>{cohort.capitalize()} inputs</h2>
<p class="caption">{stats['samples']} paired inputs across {len(stats['cases'])} case identifiers. {stats['scored_repetitions']} scored resolver repetitions; {stats['failed_repetitions']} failed or unavailable; {stats['not_attempted_repetitions']} not attempted. {stats['paired_score_count']} paired deltas available.</p>
<div class="plot"><div class="legend"><span>Dashed line / square: no-op baseline</span><span>Solid line / circle: resolver mean; bars: range</span></div>{f1_chart(samples, cohort)}</div>
<div class="table-scroll"><table><caption>F1 by paired input; failures are excluded from scores and counted explicitly.</caption>
<thead><tr><th>Paired sample</th><th>Baseline</th><th>Resolver mean</th><th>Sample SD</th><th>Minimum</th><th>Mean delta</th><th>Scored/planned</th><th>Failed</th></tr></thead><tbody>{''.join(rows)}</tbody></table></div>
{_quality_table(stats)}
<div class="details">{''.join(_sample_details(s) for s in samples)}</div></section>'''


def _quality_table(stats: dict[str, Any]) -> str:
    rows = []
    for metric in ('precision', 'recall', 'f1', 'provenance_accuracy'):
        base, treatment = stats['baseline_metrics'][metric], stats['resolver_per_input_means'][metric]
        rows.append(f'<tr><td>{metric.replace("_", " ").capitalize()}</td><td>{_number(base["mean"])}</td><td>{_number(base["standard_deviation"])}</td><td>{_number(treatment["mean"])}</td><td>{_number(treatment["standard_deviation"])}</td><td>{base["n"]} / {treatment["n"]}</td></tr>')
    return '<div class="table-scroll"><table><caption>Equal-weight input means; SD measures variation across inputs.</caption><thead><tr><th>Metric</th><th>Baseline mean</th><th>Baseline SD</th><th>Resolver mean</th><th>Resolver SD</th><th>Scored inputs B / R</th></tr></thead><tbody>'+''.join(rows)+'</tbody></table></div>'


def _sample_details(sample: dict[str, Any]) -> str:
    rows = []
    for result in [sample['baseline'], *sample['repetitions']]:
        evaluation, identity = result.get('evaluation') or {}, result.get('identity')
        name = 'Baseline' if result.get('configuration') == 'noop' else f"Resolver {result.get('repetition', '')}"
        cells = [name, html.escape(result['status']), _number(evaluation.get('f1')),
                 str(identity['incorrect_merges']) if identity is not None else 'Unavailable',
                 str(identity['missed_merges']) if identity is not None else 'Unavailable',
                 _number(result.get('provider_seconds')), _number(result.get('incremental_cost'), 6)]
        rows.append('<tr>'+''.join(f'<td>{c}</td>' for c in cells)+'</tr>')
    return f'''<details><summary>{html.escape(sample['sample_id'])}: individual results and identity diagnostics</summary>
<div class="table-scroll"><table><thead><tr><th>Run</th><th>Status</th><th>F1</th><th>Incorrect merges</th><th>Missed merges</th><th>Provider s</th><th>Resolver cost</th></tr></thead><tbody>{''.join(rows)}</tbody></table></div>
<p>No-edit resolver responses: {sample['no_edit_repetitions']}. Mean single-pipeline cost: {_number(sample['single_pipeline_cost']['mean'],6)}. Mean single-pipeline latency: {_number(sample['single_pipeline_latency']['mean'])} s.</p>
<p>Failure fraction among attempted resolver calls: {_number(sample['failure_rate_among_attempted'])} ({sample['attempted_repetitions']} attempted). Paired score coverage of planned repetitions: {_number(sample['paired_score_coverage'])}. Baseline single-pipeline latency: {_number(sample['baseline_single_pipeline_latency'])} s. Historical original elapsed time: {_number(sample['historical_pipeline_seconds'])} s.</p>
{_details('Full predictions, denominators, metrics and stage timings', sample)}</details>'''


def _usage_table(tokens: dict[str, Any]) -> str:
    rows = ''.join(f'<tr><td>{name.replace("_", " ")}</td><td>{value["known_sum"]}</td><td>{value["known_attempts"]}</td><td>{value["unknown_attempts"]}</td></tr>' for name, value in tokens.items())
    return '<div class="table-scroll"><table><thead><tr><th>Usage</th><th>Known subtotal</th><th>Known attempts</th><th>Unknown attempts</th></tr></thead><tbody>'+rows+'</tbody></table></div>'
