import unittest

from agent_review_ledger import evaluate_candidate


class GateTests(unittest.TestCase):
    def setUp(self):
        self.valid = {
            "baseline_score": 0.5,
            "candidate_score": 0.6,
            "regressions": 0,
            "cost_cents": 10,
            "budget_cents": 10,
            "independent_review": True,
            "holdout_passed": True,
        }

    def test_accepts_qualified_candidate(self):
        self.assertEqual(evaluate_candidate(**self.valid), {"eligible": True, "reasons": []})

    def test_returns_every_rejection_reason(self):
        result = evaluate_candidate(0.5, 0.4, 1, 11, 10, False, False)
        self.assertEqual(result["reasons"], [
            "no_improvement", "regressions_present", "budget_exceeded",
            "independent_review_required", "holdout_required",
        ])

    def test_rejects_invalid_values(self):
        cases = {
            "baseline_score": [None, True, "0.5", -0.1, 1.1, float("nan"), float("inf")],
            "candidate_score": [None, False, "0.6", -0.1, 1.1, float("nan")],
            "regressions": [None, False, "0", -1, 0.0, 2**63],
            "cost_cents": [None, False, "0", -1, 0.0, 2**63],
            "budget_cents": [None, False, "0", -1, 0.0, 2**63],
            "independent_review": [None, 1, "true"],
            "holdout_passed": [None, 1, "true"],
        }
        for field, values in cases.items():
            for bad in values:
                with self.subTest(field=field, bad=bad), self.assertRaises(ValueError):
                    evaluate_candidate(**dict(self.valid, **{field: bad}))


if __name__ == "__main__":
    unittest.main()
