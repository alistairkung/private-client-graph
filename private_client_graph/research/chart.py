"""Accessible inline SVG: missing observations break the plotted line."""
from html import escape
from typing import Any


def f1_chart(samples: list[dict[str, Any]], cohort: str) -> str:
    left, top, width, height = 58, 28, 780, 210
    bottom = top + height
    elements = [f'<svg viewBox="0 0 880 310" role="img" aria-labelledby="chart-{cohort}">',
                f'<title id="chart-{cohort}">{escape(cohort)}: baseline and resolver F1 by paired sample; exact values in the table below.</title>']
    for score in (0, .25, .5, .75, 1):
        y = bottom - height * score
        elements.append(f'<line class="grid" x1="{left}" x2="{left + width}" y1="{y}" y2="{y}"/>'
                        f'<text x="{left - 12}" y="{y + 5}" text-anchor="end">{score:g}</text>')
    elements.append('<text x="14" y="20">F1</text>')
    xs = [left + width * ((i + .5) / len(samples)) for i in range(len(samples))]
    for i, x in enumerate(xs, 1):
        elements.append(f'<text x="{x}" y="{bottom + 26}" text-anchor="middle">{i}</text>')
    elements.append('<text x="448" y="298" text-anchor="middle">Paired extraction sample index</text>')
    for kind in ('baseline', 'resolver'):
        previous = None
        for x, sample in zip(xs, samples):
            stats = sample['resolver_metrics']['f1']
            value = ((sample['baseline'].get('evaluation') or {}).get('f1')
                     if kind == 'baseline' else stats['mean'])
            if value is None:
                previous = None
                continue
            y = bottom - height * value
            if previous is not None:
                elements.append(f'<line class="{kind}" x1="{previous[0]}" y1="{previous[1]}" x2="{x}" y2="{y}"/>')
            if kind == 'resolver':
                low, high = bottom - height * stats['minimum'], bottom - height * stats['maximum']
                elements.append(f'<path class="range" d="M{x} {low} V{high} M{x-5} {low} H{x+5} M{x-5} {high} H{x+5}"/>')
                elements.append(f'<circle class="resolver point" cx="{x}" cy="{y}" r="5"><title>{escape(sample["sample_id"])} resolver mean {value:.3f}</title></circle>')
            else:
                elements.append(f'<rect class="baseline point" x="{x-4}" y="{y-4}" width="8" height="8"><title>{escape(sample["sample_id"])} baseline {value:.3f}</title></rect>')
            previous = x, y
    return ''.join(elements) + '</svg>'
