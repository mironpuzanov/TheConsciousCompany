#!/usr/bin/env python3
"""Test Responses API"""
import asyncio
import os
from dotenv import load_dotenv
from openai import AsyncOpenAI

load_dotenv('.env')

async def test_responses_api():
    api_key = os.getenv('OPENAI_API_KEY')
    print(f"API Key exists: {bool(api_key)}")
    print(f"API Key prefix: {api_key[:20] if api_key else 'None'}...")

    client = AsyncOpenAI(api_key=api_key)

    print("\n=== Testing Responses API ===")
    try:
        response = await client.responses.create(
            model="gpt-5.1",
            input="Say hello in one sentence.",
            reasoning={"effort": "low"},
            text={"verbosity": "low"},
            stream=True
        )

        print(f"Response type: {type(response)}")
        print(f"Response dir: {[x for x in dir(response) if not x.startswith('_')]}")

        print("\nStreaming response:")
        full_response = ""
        chunk_count = 0
        async for chunk in response:
            chunk_count += 1
            print(f"Chunk #{chunk_count}: {type(chunk)}")
            print(f"Chunk attributes: {[x for x in dir(chunk) if not x.startswith('_')]}")

            if hasattr(chunk, 'output_text'):
                print(f"output_text: {chunk.output_text}")
                full_response = chunk.output_text
            if hasattr(chunk, 'text'):
                print(f"text: {chunk.text}")
                full_response += chunk.text

        print(f"\n\nTotal chunks: {chunk_count}")
        print(f"Total length: {len(full_response)} chars")
        print(f"SUCCESS: {full_response}")

    except Exception as e:
        print(f"ERROR: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(test_responses_api())
