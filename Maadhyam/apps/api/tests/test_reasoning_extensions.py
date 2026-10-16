"""Run with: uv run pytest -q tests/test_reasoning_extensions.py"""
from maadhyam_api.routes.reasoning_engine import (
    ReasoningRequest, _graph_diagnostics, _minimum_review_path, reason,
)


def test_cycle_detection():
    result = _graph_diagnostics([
        {'id': 'a', 'dependsOn': ['b']},
        {'id': 'b', 'dependsOn': ['a']},
    ])
    assert result['cyclesDetected'] is True
    assert len(result['cycles']) == 1


def test_missing_dependency_detection():
    result = _graph_diagnostics([{'id': 'a', 'dependsOn': ['missing']}])
    assert result['missingDependencyIds'] == ['missing']


def test_minimum_dependency_closure():
    assessment = {
        'tasks': [
            {'id': 'prep', 'priority': 2, 'dependsOn': []},
            {'id': 'critical', 'priority': 1, 'dependsOn': ['prep']},
            {'id': 'optional', 'priority': 2, 'dependsOn': []},
        ],
        'executionOrder': ['prep', 'critical', 'optional'],
    }
    result = _minimum_review_path(assessment)
    assert result['selectedTaskIds'] == ['prep', 'critical']
    assert result['excludedOptionalTaskIds'] == ['optional']


def test_reasoning_response_backward_compatible():
    result = reason(ReasoningRequest(documents=[]))
    for key in ('baseline', 'dependencyGraph', 'familyEvidence', 'simulations',
                'minimumCorrectionPath', 'deadlockAnalysis', 'proofSubstitution', 'deadlineRescue'):
        assert key in result
    assert result['officialEligibilityDetermined'] is False
    assert result['proofSubstitution']['officialSubstitutionApproved'] is False
