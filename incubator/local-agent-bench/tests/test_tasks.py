from pathlib import Path

import pytest

from labench.tasks import Expectation, Task, load_tasks

REPO_TASKS = Path(__file__).resolve().parents[1] / "tasks"


class TestBuiltinSuite:
    def test_builtin_suite_loads(self):
        tasks = load_tasks(REPO_TASKS)
        assert len(tasks) >= 12
        assert {t.category for t in tasks} == {"tool_call", "no_tool", "structured_output"}

    def test_ids_are_unique_and_sorted(self):
        tasks = load_tasks(REPO_TASKS)
        ids = [t.id for t in tasks]
        assert ids == sorted(ids)
        assert len(ids) == len(set(ids))


class TestTaskValidation:
    def test_tool_call_requires_tool_name(self):
        with pytest.raises(ValueError, match="expected.tool_name"):
            Task(
                id="bad",
                category="tool_call",
                prompt="p",
                tools=[{"type": "function", "function": {"name": "f"}}],
                expected=Expectation(),
            )

    def test_tool_call_requires_tools(self):
        with pytest.raises(ValueError, match="tool definitions"):
            Task(
                id="bad",
                category="tool_call",
                prompt="p",
                expected=Expectation(tool_name="f"),
            )

    def test_structured_output_requires_schema(self):
        with pytest.raises(ValueError, match="json_schema"):
            Task(id="bad", category="structured_output", prompt="p", expected=Expectation())

    def test_missing_dir_raises(self, tmp_path):
        with pytest.raises(FileNotFoundError):
            load_tasks(tmp_path / "nope")

    def test_duplicate_ids_raise(self, tmp_path):
        (tmp_path / "a.yaml").write_text(
            "- id: dup\n  category: no_tool\n  prompt: hi\n  expected: {}\n"
            "- id: dup\n  category: no_tool\n  prompt: hi again\n  expected: {}\n"
        )
        with pytest.raises(ValueError, match="duplicate task id"):
            load_tasks(tmp_path)
