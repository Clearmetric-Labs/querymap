from __future__ import annotations

import pytest

from .ground_truth import (
    FIXTURES_ROOT,
    Probe,
    WarningExpectation,
    diff_sets,
    diff_warnings,
    false_negatives,
    false_positives,
    load_ground_truth_file,
    run_probe,
)


def _all_probes() -> list[Probe]:
    probes: list[Probe] = []
    for path in sorted((FIXTURES_ROOT / "ground_truth").glob("*.yaml")):
        probes.extend(load_ground_truth_file(path))
    return probes


@pytest.mark.parametrize(
    "probe",
    _all_probes(),
    ids=lambda probe: f"{probe.source_file.stem}:{probe.selection}",
)
def test_ground_truth_probe_matches_exact_truth_sets(probe: Probe):
    result = run_probe(probe)

    assert false_negatives(probe.expected_upstream, result.actual_upstream) == set(), (
        diff_sets(
            expected=probe.expected_upstream,
            actual=result.actual_upstream,
            label=f"upstream {probe.selection}",
        )
    )
    assert false_positives(probe.expected_upstream, result.actual_upstream) == set(), (
        diff_sets(
            expected=probe.expected_upstream,
            actual=result.actual_upstream,
            label=f"upstream {probe.selection}",
        )
    )

    assert (
        false_negatives(probe.expected_downstream, result.actual_downstream) == set()
    ), diff_sets(
        expected=probe.expected_downstream,
        actual=result.actual_downstream,
        label=f"downstream {probe.selection}",
    )
    assert (
        false_positives(probe.expected_downstream, result.actual_downstream) == set()
    ), diff_sets(
        expected=probe.expected_downstream,
        actual=result.actual_downstream,
        label=f"downstream {probe.selection}",
    )

    expected_warnings = tuple(
        sorted(
            probe.expected_warnings,
            key=lambda item: (item.dataset, item.code, item.subject_id or ""),
        )
    )
    actual_warnings = tuple(
        sorted(
            _warnings_for_probe(result.actual_warnings, selection=probe.selection),
            key=lambda item: (item.dataset, item.code, item.subject_id or ""),
        )
    )
    assert actual_warnings == expected_warnings, diff_warnings(
        expected=expected_warnings,
        actual=actual_warnings,
    )


def _warnings_for_probe(
    warnings: tuple[WarningExpectation, ...], *, selection: str
) -> tuple[WarningExpectation, ...]:
    selected_dataset = selection.rsplit(".", 1)[0]
    selection_subject_id = f"column:{selection}"
    matching = [
        warning
        for warning in warnings
        if warning.subject_id == selection_subject_id
        or (warning.subject_id is None and warning.dataset == selected_dataset)
    ]
    return tuple(matching)
