import json

from labench.client import ModelResponse, ToolCall
from labench.scoring import score_response
from labench.tasks import Expectation, Task

WEATHER_TOOL = {
    "type": "function",
    "function": {
        "name": "get_weather",
        "description": "Get weather",
        "parameters": {
            "type": "object",
            "properties": {"city": {"type": "string"}},
            "required": ["city"],
        },
    },
}


def make_tool_task(argument_match: str = "subset", arguments: dict | None = None) -> Task:
    return Task(
        id="t1",
        category="tool_call",
        prompt="weather in Paris?",
        tools=[WEATHER_TOOL],
        expected=Expectation(
            tool_name="get_weather",
            arguments=arguments or {"city": "Paris"},
            argument_match=argument_match,
        ),
    )


def call(name: str, args: dict) -> ModelResponse:
    return ModelResponse(content=None, tool_calls=[ToolCall(name=name, arguments=json.dumps(args))])


class TestToolCallScoring:
    def test_correct_call_passes(self):
        score = score_response(make_tool_task(), call("get_weather", {"city": "Paris"}))
        assert score.passed and score.reason == "ok"

    def test_subset_allows_extra_keys(self):
        response = call("get_weather", {"city": "Paris", "unit": "celsius"})
        assert score_response(make_tool_task("subset"), response).passed

    def test_exact_rejects_extra_keys(self):
        response = call("get_weather", {"city": "Paris", "unit": "celsius"})
        score = score_response(make_tool_task("exact"), response)
        assert not score.passed and score.reason == "wrong_arguments"

    def test_no_call_fails(self):
        response = ModelResponse(content="It is sunny.", tool_calls=[])
        score = score_response(make_tool_task(), response)
        assert not score.passed and score.reason == "no_tool_call"

    def test_wrong_tool_fails(self):
        score = score_response(make_tool_task(), call("get_stock_price", {"ticker": "X"}))
        assert not score.passed and score.reason == "wrong_tool"

    def test_malformed_arguments_fail(self):
        response = ModelResponse(
            content=None, tool_calls=[ToolCall(name="get_weather", arguments="{not json")]
        )
        score = score_response(make_tool_task(), response)
        assert not score.passed and score.reason == "malformed_arguments"

    def test_multiple_calls_fail(self):
        response = ModelResponse(
            content=None,
            tool_calls=[
                ToolCall(name="get_weather", arguments="{}"),
                ToolCall(name="get_weather", arguments="{}"),
            ],
        )
        score = score_response(make_tool_task(), response)
        assert not score.passed and score.reason == "multiple_tool_calls"


class TestNoToolScoring:
    def make_task(self) -> Task:
        return Task(
            id="n1",
            category="no_tool",
            prompt="capital of France?",
            tools=[WEATHER_TOOL],
            expected=Expectation(),
        )

    def test_direct_answer_passes(self):
        response = ModelResponse(content="Paris.", tool_calls=[])
        assert score_response(self.make_task(), response).passed

    def test_tool_call_fails(self):
        score = score_response(self.make_task(), call("get_weather", {"city": "Paris"}))
        assert not score.passed and score.reason == "unexpected_tool_call"

    def test_empty_response_fails(self):
        response = ModelResponse(content="  ", tool_calls=[])
        score = score_response(self.make_task(), response)
        assert not score.passed and score.reason == "empty_response"


class TestStructuredOutputScoring:
    def make_task(self) -> Task:
        return Task(
            id="s1",
            category="structured_output",
            prompt="extract as JSON",
            expected=Expectation(
                json_schema={
                    "type": "object",
                    "properties": {"name": {"type": "string"}},
                    "required": ["name"],
                    "additionalProperties": False,
                }
            ),
        )

    def test_valid_json_passes(self):
        response = ModelResponse(content='{"name": "Maria"}', tool_calls=[])
        assert score_response(self.make_task(), response).passed

    def test_fenced_json_passes(self):
        response = ModelResponse(content='```json\n{"name": "Maria"}\n```', tool_calls=[])
        assert score_response(self.make_task(), response).passed

    def test_invalid_json_fails(self):
        response = ModelResponse(content="name is Maria", tool_calls=[])
        score = score_response(self.make_task(), response)
        assert not score.passed and score.reason == "invalid_json"

    def test_schema_violation_fails(self):
        response = ModelResponse(content='{"name": 42}', tool_calls=[])
        score = score_response(self.make_task(), response)
        assert not score.passed and score.reason == "schema_violation"

    def test_extra_property_fails(self):
        response = ModelResponse(content='{"name": "Maria", "age": 30}', tool_calls=[])
        score = score_response(self.make_task(), response)
        assert not score.passed and score.reason == "schema_violation"
