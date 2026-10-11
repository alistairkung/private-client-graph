"""Pair historical observations only when frozen scientific inputs match."""
from .contracts import ComparedObservation, Comparison, Exclusion, ExperimentDetail, Sample


def compare_experiments(left: ExperimentDetail, right: ExperimentDetail) -> Comparison:
    differences = []
    for label, first, second in (
        ('Configuration', left.configuration, right.configuration),
        ('Code/dependency/prompt provenance', left.provenance, right.provenance),
        ('Execution mode', left.history.kind, right.history.kind),
    ):
        if first != second:
            differences.append(f'{label} differs; inspect each experiment’s recorded metadata.')
    comparison = Comparison(left=left.history, right=right.history, differences=differences,
                            observations=[], exclusions=[], matched_inputs=0, scored_pairs=0)
    unmatched = list(right.samples)
    left_keys = [_input_key(sample) for sample in left.samples]
    for sample in left.samples:
        matches = [other for other in unmatched if _input_key(sample) == _input_key(other)
                   and sample.extraction_digest is not None]
        if len(matches) != 1 or left_keys.count(_input_key(sample)) != 1:
            comparison.exclusions.append(Exclusion(side='left', sample_id=sample.id,
                reason='No unique match for cohort, Source, truth and extraction bytes.'))
            continue
        other = matches[0]
        unmatched.remove(other)
        comparison.matched_inputs += 1
        comparison.observations.extend(_paired_observations(sample, other))
    comparison.exclusions.extend(Exclusion(side='right', sample_id=sample.id,
        reason='No unique matched frozen input.') for sample in unmatched)
    comparison.scored_pairs = sum(row.delta_f1 is not None for row in comparison.observations)
    return comparison


def _input_key(sample: Sample) -> tuple:
    return (sample.case_id, sample.cohort, sample.source_digest,
            sample.truth_digest, sample.extraction_digest)


def _paired_observations(left: Sample, right: Sample) -> list[ComparedObservation]:
    first = {(row.configuration, row.repetition): row for row in left.observations}
    second = {(row.configuration, row.repetition): row for row in right.observations}
    rows = []
    for key in sorted(first.keys() | second.keys(), key=str):
        a, b = first.get(key), second.get(key)
        left_f1 = a.evaluation.f1 if a and a.evaluation else None
        right_f1 = b.evaluation.f1 if b and b.evaluation else None
        available = left_f1 is not None and right_f1 is not None
        rows.append(ComparedObservation(
            left_sample=left.id, right_sample=right.id, configuration=key[0], repetition=key[1],
            left_f1=left_f1, right_f1=right_f1,
            delta_f1=right_f1 - left_f1 if right_f1 is not None and left_f1 is not None else None,
            reason=None if available else 'One or both observations are absent or unscored.',
        ))
    return rows
