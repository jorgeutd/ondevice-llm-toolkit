"""Function calling with a full tool-result round trip.

Sends a prompt with a tool definition, executes the (mock) tool locally,
returns the result to the model, and prints the final answer. This is the
minimal loop every agent framework builds on.

Requires an engine + model with tool-call support (vLLM/SGLang with a
tool-capable model; llama.cpp needs --jinja and a template with tools).

Usage:
    python tool_calling.py --base-url http://localhost:8000/v1 \
        --model Qwen/Qwen2.5-1.5B-Instruct
"""

from __future__ import annotations

import argparse
import json

from openai import OpenAI

WEATHER_TOOL = {
    "type": "function",
    "function": {
        "name": "get_weather",
        "description": "Get current weather for a city.",
        "parameters": {
            "type": "object",
            "properties": {
                "city": {"type": "string"},
                "unit": {"type": "string", "enum": ["celsius", "fahrenheit"]},
            },
            "required": ["city"],
        },
    },
}


def get_weather(city: str, unit: str = "celsius") -> dict:
    """Mock implementation — swap in a real API call."""
    return {"city": city, "temperature": 22 if unit == "celsius" else 72, "unit": unit}


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--base-url", required=True)
    parser.add_argument("--model", required=True)
    parser.add_argument("--api-key", default="not-needed")
    args = parser.parse_args()

    client = OpenAI(base_url=args.base_url, api_key=args.api_key)
    messages = [{"role": "user", "content": "What's the weather in Columbus, Ohio in celsius?"}]

    first = client.chat.completions.create(
        model=args.model,
        messages=messages,
        tools=[WEATHER_TOOL],
        temperature=0,
        max_tokens=200,
    )
    message = first.choices[0].message
    if not message.tool_calls:
        print("model answered without calling the tool:", message.content)
        return

    call = message.tool_calls[0]
    print(f"model called: {call.function.name}({call.function.arguments})")
    tool_result = get_weather(**json.loads(call.function.arguments))

    messages += [
        message.model_dump(exclude_none=True),
        {
            "role": "tool",
            "tool_call_id": call.id,
            "content": json.dumps(tool_result),
        },
    ]
    final = client.chat.completions.create(
        model=args.model, messages=messages, tools=[WEATHER_TOOL], temperature=0, max_tokens=200
    )
    print("final answer:", final.choices[0].message.content)


if __name__ == "__main__":
    main()
