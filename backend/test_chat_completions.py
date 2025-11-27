#!/usr/bin/env python3
"""Test Chat Completions API"""
import asyncio
import os
from dotenv import load_dotenv
from openai import AsyncOpenAI

load_dotenv('.env')

async def test_chat_completions():
    api_key = os.getenv('OPENAI_API_KEY')
    print(f"API Key exists: {bool(api_key)}")
    print(f"API Key prefix: {api_key[:20] if api_key else 'None'}...")

    client = AsyncOpenAI(api_key=api_key)

    print("\n=== Testing Chat Completions API ===")
    try:
        response = await client.chat.completions.create(
            model="gpt-4",
            messages=[
                {"role": "system", "content": "You are a helpful assistant."},
                {"role": "user", "content": "Say hello in one sentence."}
            ],
            max_tokens=50,
            stream=True
        )

        print("Streaming response:")
        full_response = ""
        async for chunk in response:
            if chunk.choices[0].delta.content:
                content = chunk.choices[0].delta.content
                print(content, end='', flush=True)
                full_response += content

        print(f"\n\nTotal length: {len(full_response)} chars")
        print(f"SUCCESS: {full_response}")

    except Exception as e:
        print(f"ERROR: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(test_chat_completions())
