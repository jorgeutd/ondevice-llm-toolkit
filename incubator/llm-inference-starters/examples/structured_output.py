"""JSON-schema-constrained output against any OpenAI-compatible endpoint.

Uses `response_format` with a JSON schema, which vLLM, SGLang, llama.cpp
(llama-server), and Ollama all support (implementations vary: guided
decoding, grammars/GBNF, or output validation). Falls back gracefully so
you can see what an engine returns either way.

Usage:
    python structured_output.py --base-url http://localhost:8000/v1 \
        --model Qwen/Qwen2.5-1.5B-Instruct
"""

from __future__ import annotations

import argparse
import json

from openai import OpenAI

TICKET_SCHEMA = {
    "type": "object",
    "properties": {
        "category": {"type": "string", "enum": ["billing", "technical", "account", "other"]},
        "priority": {"type": "string", "enum": ["low", "medium", "high"]},
        "summary": {"type": "string"},
    },
    "required": ["category", "priority", "summary"],
    "additionalProperties": False,
}

CUSTOMER_MESSAGE = (
    "I was charged twice for my subscription this month and support chat "
    "keeps disconnecting. Please fix the double charge urgently."
)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--base-url", required=True)
    parser.add_argument("--model", required=True)
    parser.add_argument("--api-key", default="not-needed")
    args = parser.parse_args()

    client = OpenAI(base_url=args.base_url, api_key=args.api_key)
    response = client.chat.completions.create(
        model=args.model,
        messages=[
            {
                "role": "system",
                "content": "Classify the customer message into a support ticket. JSON only.",
            },
            {"role": "user", "content": CUSTOMER_MESSAGE},
        ],
        max_tokens=200,
        temperature=0,
        response_format={
            "type": "json_schema",
            "json_schema": {"name": "ticket", "schema": TICKET_SCHEMA, "strict": True},
        },
    )
    raw = response.choices[0].message.content or ""
    print("raw response:", raw)
    ticket = json.loads(raw)  # raises if the engine did not honor the schema
    print("parsed ticket:", json.dumps(ticket, indent=2))


if __name__ == "__main__":
    main()
