"""Render the qualitative coverage register from its structured records."""

from benchmark_v3 import commissioning
from benchmark_v3.research_contracts import AdmittedFamily, VerifiedFinding


def render_coverage() -> str:
    register = commissioning.coverage_register()
    lines = [
        "# Benchmark v3 coverage register",
        "",
        "Generated with `uv run python -m benchmark_v3.architect coverage`.",
        "The [admission register](admissions/2026-11-24.md) covers all 19 admitted development families.",
        "The [research catalogue](RESEARCH-CATALOGUE.md) describes their reasoning tests and limits.",
        "Each family counts once. Matched conditions share its history.",
        "Keep this register outside the blind packets.",
        "",
        "## Original five admissions and coverage reconciliations",
        "",
        "| Family | Primary axis | Secondary axes | Intended difficulty |",
        "| --- | --- | --- | --- |",
    ]
    for family in register.families:
        commissioning.verify_coverage_family(family)
        dossier = "admissions/2026-11-24.md"
        row = (
            f"[{family.family_id} · {_cell(family.name)}]({dossier})",
            _axis(family.primary_axis),
            ", ".join(map(_axis, family.secondary_axes)) or "—",
            _cell(family.intended_difficulty),
        )
        lines.append("| " + " | ".join(row) + " |")

    for family in register.families:
        lines.extend(_family_details(family))

    lines.extend(["", "## Difficulty taxonomy", "", "| Axis | Category | Scope | Meaning |",
                  "| --- | --- | --- | --- |"])
    for axis in register.taxonomy:
        lines.append(
            f"| {_axis(axis.id)} | {_axis(axis.category)} | {_axis(axis.scope)} | "
            f"{_cell(axis.description)} |"
        )
    lines.extend(["", "## Earlier coverage gaps", ""])
    for gap in register.gaps:
        finding = gap.finding.replace("](admission_d_f/OWNER-DECISIONS.md)", "](admissions/2026-11-24.md)")
        lines.append(f"- **{', '.join(map(_axis, gap.axes))}.** {finding}")
    lines.extend(_proposal_statuses())
    return "\n".join(lines) + "\n"


def _family_details(family: AdmittedFamily) -> list[str]:
    family_id = family.family_id
    admission = "admissions/2026-11-24.md"
    lines = ["", f"### {family_id} · {family.title}", ""]
    if family.hypothesis is None:
        lines.append(f"[Historical admission]({admission}) under the earlier protocol.")
    else:
        ref = family.hypothesis
        lines.append(
            f"[Human admission]({admission}) under approved hypothesis "
            f"`{ref.hypothesis_id}@{ref.revision}` (`{ref.hypothesis_sha256}`)."
        )
    reconciliation = commissioning.saved_reconciliation(family)
    findings = family.verified_findings
    if reconciliation:
        result = reconciliation.result
        findings = result.verified_findings
        lines.extend([
            "",
            f"[Coverage reconciliation](planning/reconciliations/{family_id}.json) recorded "
            f"**{_axis(result.operationalisation)}** operationalisation. {result.achieved_vs_intended}",
            "",
            f"**Additional coverage.** {result.additional_coverage}",
            f"**Redundancy.** {result.redundancy}",
            f"**Recommendation.** {_axis(result.recommendation).capitalize()}. {result.rationale}",
        ])
        for gap in result.remaining_gaps:
            lines.append(f"- **{', '.join(map(_axis, gap.axes))}.** {gap.finding}")
    lines.extend(["", "**Independently verified findings**", ""])
    lines.extend(_finding(finding) for finding in findings)
    if not findings:
        lines.append("No verified findings recorded.")
    lines.extend([
        "",
        f"- **Incidental challenges.** {' '.join(family.incidental_challenges)}",
        f"- **Matched controls.** {' '.join(family.matched_controls)}",
        f"- **Shortcuts and limits.** {' '.join(family.known_shortcuts_and_limits)}",
        f"- **Genres.** {', '.join(family.documentary_genres)}.",
        f"- **Overlap.** {family.overlap}",
    ])
    return lines


def _proposal_statuses() -> list[str]:
    history = commissioning.proposal_history()
    lines = ["", "## Hypothesis decisions", ""]
    if not history:
        return lines + ["No registered proposals."]
    lines.extend(["| Hypothesis | Family | Status | Revision digest |", "| --- | --- | --- | --- |"])
    for key, (hypothesis, ref, decision) in history.items():
        status = decision.status if decision else hypothesis.status
        title = _cell(hypothesis.title)
        lines.append(f"| `{key}` · {title} | {hypothesis.family_id} | {status} | `{ref.hypothesis_sha256}` |")
    return lines


def _axis(value: str) -> str:
    return value.replace("-", " ").replace("_", " ")


def _cell(value: str) -> str:
    return " ".join(value.splitlines()).replace("|", r"\|")


def _finding(finding: VerifiedFinding) -> str:
    references = ", ".join(f"`{item}`" for item in finding.evidence)
    return f"- **{_axis(finding.axis).capitalize()}.** {finding.finding} ({references})"
