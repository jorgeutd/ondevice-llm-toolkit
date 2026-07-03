import pytest

from llmstart.streaming import (
    extract_completion_tokens,
    extract_content_delta,
    parse_sse_line,
)


class TestParseSseLine:
    def test_parses_data_line(self):
        chunk = parse_sse_line('data: {"choices": [{"delta": {"content": "hi"}}]}')
        assert chunk == {"choices": [{"delta": {"content": "hi"}}]}

    def test_done_sentinel_returns_none(self):
        assert parse_sse_line("data: [DONE]") is None

    def test_blank_and_comment_lines_return_none(self):
        assert parse_sse_line("") is None
        assert parse_sse_line(": keep-alive") is None
        assert parse_sse_line("event: ping") is None

    def test_malformed_json_raises(self):
        with pytest.raises(ValueError, match="malformed SSE"):
            parse_sse_line("data: {not json")


class TestExtractors:
    def test_content_delta(self):
        chunk = {"choices": [{"delta": {"content": "hello"}}]}
        assert extract_content_delta(chunk) == "hello"

    def test_role_only_delta_returns_none(self):
        chunk = {"choices": [{"delta": {"role": "assistant"}}]}
        assert extract_content_delta(chunk) is None

    def test_usage_chunk_has_no_choices(self):
        chunk = {"choices": [], "usage": {"completion_tokens": 42, "prompt_tokens": 10}}
        assert extract_content_delta(chunk) is None
        assert extract_completion_tokens(chunk) == 42

    def test_no_usage_returns_none(self):
        assert extract_completion_tokens({"choices": []}) is None
