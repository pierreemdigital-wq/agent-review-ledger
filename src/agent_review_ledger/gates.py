"""Deterministic evaluation gates with no external side effects."""


def _nonnegative_int(value, name):
    if type(value) is not int or not 0 <= value <= 2**63 - 1:
        raise ValueError(name + " must be an integer in [0, 2**63-1]")


def evaluate_candidate(
    baseline_score,
    candidate_score,
    regressions,
    cost_cents,
    budget_cents,
    independent_review,
    holdout_passed,
):
    """Return deterministic eligibility and every rejection reason."""
    for name, score in (
        ("baseline_score", baseline_score),
        ("candidate_score", candidate_score),
    ):
        if type(score) not in (int, float) or not 0 <= score <= 1:
            raise ValueError(name + " must be a finite number in [0, 1]")
    for name, value in (
        ("regressions", regressions),
        ("cost_cents", cost_cents),
        ("budget_cents", budget_cents),
    ):
        _nonnegative_int(value, name)
    for name, value in (
        ("independent_review", independent_review),
        ("holdout_passed", holdout_passed),
    ):
        if type(value) is not bool:
            raise ValueError(name + " must be a bool")

    reasons = []
    for rejected, reason in (
        (candidate_score <= baseline_score, "no_improvement"),
        (regressions != 0, "regressions_present"),
        (cost_cents > budget_cents, "budget_exceeded"),
        (not independent_review, "independent_review_required"),
        (not holdout_passed, "holdout_required"),
    ):
        if rejected:
            reasons.append(reason)
    return {"eligible": not reasons, "reasons": reasons}
