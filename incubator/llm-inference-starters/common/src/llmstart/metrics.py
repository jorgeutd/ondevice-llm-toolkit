"""Latency and throughput metrics for streaming completions.

Definitions (documented so numbers are comparable across engines):

- TTFT: wall-clock seconds from request start to first content delta.
- Decode tokens/sec: (completion_tokens - 1) / (last_delta_t - first_delta_t).
  Prefill is excluded; the first token's cost is attributed to TTFT.
- Token counts prefer the server `usage` field; falling back to counting
  content deltas is flagged, since deltas may not map 1:1 to tokens.
"""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class RequestTiming:
    ttft_s: float
    total_s: float
    completion_tokens: int
    decode_tps: float | None
    tokens_source: str  # "usage" or "chunk_count"


def compute_timing(
    start_t: float,
    first_delta_t: float,
    last_delta_t: float,
    end_t: float,
    chunk_count: int,
    usage_completion_tokens: int | None,
) -> RequestTiming:
    if chunk_count <= 0:
        raise ValueError("no content deltas received; cannot compute timing")
    if usage_completion_tokens is not None and usage_completion_tokens > 0:
        tokens, source = usage_completion_tokens, "usage"
    else:
        tokens, source = chunk_count, "chunk_count"
    decode_window = last_delta_t - first_delta_t
    decode_tps = (tokens - 1) / decode_window if tokens > 1 and decode_window > 0 else None
    return RequestTiming(
        ttft_s=first_delta_t - start_t,
        total_s=end_t - start_t,
        completion_tokens=tokens,
        decode_tps=decode_tps,
        tokens_source=source,
    )


def percentile(values: list[float], p: float) -> float:
    """Linear-interpolated percentile, p in [0, 100]."""
    if not values:
        raise ValueError("values must be non-empty")
    if not 0 <= p <= 100:
        raise ValueError("p must be within [0, 100]")
    ordered = sorted(values)
    if len(ordered) == 1:
        return ordered[0]
    rank = (p / 100) * (len(ordered) - 1)
    lower = int(rank)
    upper = min(lower + 1, len(ordered) - 1)
    frac = rank - lower
    return ordered[lower] * (1 - frac) + ordered[upper] * frac


@dataclass(frozen=True)
class BenchSummary:
    n: int
    ttft_p50: float
    ttft_p95: float
    ttft_max: float
    tps_p50: float | None
    tps_p95: float | None
    tps_min: float | None
    total_p50: float
    total_p95: float
    total_max: float
    tokens_source: str


def summarize(timings: list[RequestTiming]) -> BenchSummary:
    if not timings:
        raise ValueError("no timings to summarize")
    ttfts = [t.ttft_s for t in timings]
    totals = [t.total_s for t in timings]
    rates = [t.decode_tps for t in timings if t.decode_tps is not None]
    sources = {t.tokens_source for t in timings}
    return BenchSummary(
        n=len(timings),
        ttft_p50=percentile(ttfts, 50),
        ttft_p95=percentile(ttfts, 95),
        ttft_max=max(ttfts),
        # For throughput, the "bad tail" is the low side, so p95 uses p=5.
        tps_p50=percentile(rates, 50) if rates else None,
        tps_p95=percentile(rates, 5) if rates else None,
        tps_min=min(rates) if rates else None,
        total_p50=percentile(totals, 50),
        total_p95=percentile(totals, 95),
        total_max=max(totals),
        tokens_source="usage" if sources == {"usage"} else "mixed/chunk_count",
    )
