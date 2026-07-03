import pytest

from labench.stats import bootstrap_diff_ci, wilson_interval


class TestWilsonInterval:
    def test_bounds_are_ordered_and_clamped(self):
        ci = wilson_interval(9, 10)
        assert 0.0 <= ci.low <= ci.point <= ci.high <= 1.0

    def test_zero_successes(self):
        ci = wilson_interval(0, 20)
        assert ci.point == 0.0
        assert ci.low == 0.0
        assert ci.high > 0.0  # honest upper bound, never claims certainty

    def test_all_successes(self):
        ci = wilson_interval(20, 20)
        assert ci.point == 1.0
        assert ci.low < 1.0
        assert ci.high == 1.0

    def test_larger_n_narrows_interval(self):
        narrow = wilson_interval(80, 100)
        wide = wilson_interval(8, 10)
        assert (narrow.high - narrow.low) < (wide.high - wide.low)

    def test_invalid_inputs_raise(self):
        with pytest.raises(ValueError):
            wilson_interval(1, 0)
        with pytest.raises(ValueError):
            wilson_interval(5, 3)


class TestBootstrapDiffCI:
    def test_deterministic_with_seed(self):
        a = [True] * 8 + [False] * 2
        b = [True] * 5 + [False] * 5
        ci1 = bootstrap_diff_ci(a, b, iterations=500, seed=7)
        ci2 = bootstrap_diff_ci(a, b, iterations=500, seed=7)
        assert (ci1.low, ci1.high) == (ci2.low, ci2.high)

    def test_point_estimate_is_rate_difference(self):
        a = [True] * 8 + [False] * 2
        b = [True] * 5 + [False] * 5
        ci = bootstrap_diff_ci(a, b, iterations=200)
        assert ci.point == pytest.approx(0.3)

    def test_identical_samples_include_zero(self):
        a = [True] * 5 + [False] * 5
        ci = bootstrap_diff_ci(a, list(a), iterations=1000)
        assert ci.low <= 0.0 <= ci.high

    def test_empty_sample_raises(self):
        with pytest.raises(ValueError):
            bootstrap_diff_ci([], [True])
