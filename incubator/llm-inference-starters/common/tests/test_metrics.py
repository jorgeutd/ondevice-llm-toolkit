import pytest

from llmstart.metrics import RequestTiming, compute_timing, percentile, summarize


class TestComputeTiming:
    def test_prefers_usage_token_count(self):
        timing = compute_timing(
            start_t=0.0,
            first_delta_t=0.5,
            last_delta_t=2.5,
            end_t=2.6,
            chunk_count=90,
            usage_completion_tokens=101,
        )
        assert timing.ttft_s == pytest.approx(0.5)
        assert timing.completion_tokens == 101
        assert timing.tokens_source == "usage"
        # (101 - 1) tokens over 2.0s decode window
        assert timing.decode_tps == pytest.approx(50.0)

    def test_falls_back_to_chunk_count(self):
        timing = compute_timing(
            start_t=0.0,
            first_delta_t=0.2,
            last_delta_t=1.2,
            end_t=1.3,
            chunk_count=11,
            usage_completion_tokens=None,
        )
        assert timing.completion_tokens == 11
        assert timing.tokens_source == "chunk_count"
        assert timing.decode_tps == pytest.approx(10.0)

    def test_single_token_has_no_decode_rate(self):
        timing = compute_timing(
            start_t=0.0,
            first_delta_t=0.3,
            last_delta_t=0.3,
            end_t=0.4,
            chunk_count=1,
            usage_completion_tokens=1,
        )
        assert timing.decode_tps is None

    def test_zero_chunks_raise(self):
        with pytest.raises(ValueError, match="no content deltas"):
            compute_timing(0.0, 0.1, 0.1, 0.2, chunk_count=0, usage_completion_tokens=None)


class TestPercentile:
    def test_median_of_odd_list(self):
        assert percentile([3.0, 1.0, 2.0], 50) == 2.0

    def test_interpolates(self):
        assert percentile([0.0, 10.0], 25) == pytest.approx(2.5)

    def test_extremes(self):
        values = [5.0, 1.0, 3.0]
        assert percentile(values, 0) == 1.0
        assert percentile(values, 100) == 5.0

    def test_invalid_inputs_raise(self):
        with pytest.raises(ValueError):
            percentile([], 50)
        with pytest.raises(ValueError):
            percentile([1.0], 150)


def make_timing(ttft: float, tps: float | None, total: float) -> RequestTiming:
    return RequestTiming(
        ttft_s=ttft, total_s=total, completion_tokens=100, decode_tps=tps, tokens_source="usage"
    )


class TestSummarize:
    def test_aggregates_percentiles(self):
        timings = [make_timing(0.1, 50.0, 2.0), make_timing(0.2, 40.0, 3.0)]
        summary = summarize(timings)
        assert summary.n == 2
        assert summary.ttft_p50 == pytest.approx(0.15)
        assert summary.ttft_max == pytest.approx(0.2)
        assert summary.tps_min == pytest.approx(40.0)
        assert summary.tokens_source == "usage"

    def test_throughput_tail_uses_low_side(self):
        timings = [make_timing(0.1, tps, 1.0) for tps in [10.0, 50.0, 50.0, 50.0]]
        summary = summarize(timings)
        assert summary.tps_p95 is not None
        assert summary.tps_p95 < summary.tps_p50  # tail is the slow side

    def test_missing_rates_yield_none(self):
        summary = summarize([make_timing(0.1, None, 1.0)])
        assert summary.tps_p50 is None

    def test_mixed_sources_flagged(self):
        timings = [
            make_timing(0.1, 50.0, 1.0),
            RequestTiming(
                ttft_s=0.1,
                total_s=1.0,
                completion_tokens=90,
                decode_tps=45.0,
                tokens_source="chunk_count",
            ),
        ]
        assert summarize(timings).tokens_source == "mixed/chunk_count"

    def test_empty_raises(self):
        with pytest.raises(ValueError):
            summarize([])
