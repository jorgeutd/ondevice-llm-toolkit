"""Streaming chat against any OpenAI-compatible endpoint.

Usage:
    python chat_streaming.py --base-url http://localhost:8000/v1 \
        --model Qwen/Qwen2.5-1.5B-Instruct
"""

from __future__ import annotations

import argparse

from openai import OpenAI


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--base-url", required=True)
    parser.add_argument("--model", required=True)
    parser.add_argument("--api-key", default="not-needed")
    parser.add_argument(
        "--prompt", default="Explain the KV cache in LLM inference in three sentences."
    )
    args = parser.parse_args()

    client = OpenAI(base_url=args.base_url, api_key=args.api_key)
    stream = client.chat.completions.create(
        model=args.model,
        messages=[{"role": "user", "content": args.prompt}],
        max_tokens=256,
        temperature=0.2,
        stream=True,
    )
    for chunk in stream:
        if chunk.choices and chunk.choices[0].delta.content:
            print(chunk.choices[0].delta.content, end="", flush=True)
    print()


if __name__ == "__main__":
    main()
