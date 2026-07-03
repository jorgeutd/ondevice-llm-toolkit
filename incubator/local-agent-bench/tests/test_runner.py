import json

from labench.client import ModelResponse, ToolCall, parse_completion
from labench.report import render_markdown
from labench.runner import RunResult, run_suite
from labench.scoring import Score
from labench.tasks import Expectation, Task


class FakeClient:
    """Deterministic stand-in for ChatClient."""

    def __init__(self, responses: dict[str, ModelResponse]):
        self._responses = responses
        self.calls: list[str] = []

    def complete(self, messages, tools=None) -> ModelResponse:
        prompt = messages[-1]["content"]
        self.calls.append(prompt)
        return self._responses[prompt]


def make_tasks() -> list[Task]:
    weather_tool = {
        "type": "function",
        "function": {
            "name": "get_weather",
            "parameters": {
                "type": "object",
                "properties": {"city": {"type": "string"}},
                "required": ["city"],
            },
        },
    }
    return [
        Task(
            id="a",
            category="tool_call",
            prompt="weather?",
            tools=[weather_tool],
            expected=Expectation(tool_name="get_weather"),
        ),
        Task(id="b", category="no_tool", prompt="capital?", expected=Expectation()),
    ]


class TestRunSuite:
    def test_runs_all_tasks_with_repetitions(self):
        client = FakeClient(
            {
                "weather?": ModelResponse(
                    content=None,
                    tool_calls=[ToolCall(name="get_weather", arguments='{"city": "Rome"}')],
                ),
                "capital?": ModelResponse(content="Paris.", tool_calls=[]),
            }
        )
        result = run_suite(client, make_tasks(), model="m", base_url="u", repetitions=2)
        assert len(result.scores) == 4
        assert all(s.passed for s in result.scores)
        assert result.overall().pass_rate.point == 1.0

    def test_summary_groups_by_category(self):
        client = FakeClient(
            {
                "weather?": ModelResponse(content="it is sunny", tool_calls=[]),  # fails
                "capital?": ModelResponse(content="Paris.", tool_calls=[]),  # passes
            }
        )
        result = run_suite(client, make_tasks(), model="m", base_url="u", repetitions=1)
        summary = result.summary()
        assert summary["tool_call"].passed == 0
        assert summary["tool_call"].failure_reasons == {"no_tool_call": 1}
        assert summary["no_tool"].passed == 1

    def test_json_roundtrip(self):
        result = RunResult(
            model="m",
            base_url="u",
            repetitions=1,
            started_at="2026-01-01T00:00:00Z",
            scores=[Score(task_id="a", category="no_tool", passed=True, reason="ok")],
        )
        payload = json.loads(result.to_json())
        assert payload["model"] == "m"
        assert payload["scores"][0]["passed"] is True


class TestReport:
    def test_markdown_contains_summary_and_failures(self):
        result = RunResult(
            model="qwen2.5-1.5b-q4_k_m",
            base_url="http://localhost:8080/v1",
            repetitions=1,
            started_at="2026-01-01T00:00:00Z",
            duration_s=12.3,
            scores=[
                Score(task_id="a", category="tool_call", passed=True, reason="ok"),
                Score(
                    task_id="b",
                    category="tool_call",
                    passed=False,
                    reason="wrong_tool",
                    detail="expected x got y",
                ),
            ],
        )
        md = render_markdown(result)
        assert "qwen2.5-1.5b-q4_k_m" in md
        assert "| tool_call | 1 | 2 " in md
        assert "`wrong_tool`: 1" in md
        assert "expected x got y" in md


class TestParseCompletion:
    def test_parses_tool_calls(self):
        payload = {
            "choices": [
                {
                    "message": {
                        "content": None,
                        "tool_calls": [
                            {
                                "id": "1",
                                "type": "function",
                                "function": {"name": "f", "arguments": '{"x": 1}'},
                            }
                        ],
                    }
                }
            ]
        }
        response = parse_completion(payload)
        assert response.tool_calls[0].name == "f"
        assert json.loads(response.tool_calls[0].arguments) == {"x": 1}

    def test_parses_plain_content(self):
        payload = {"choices": [{"message": {"content": "hello"}}]}
        response = parse_completion(payload)
        assert response.content == "hello"
        assert response.tool_calls == []
