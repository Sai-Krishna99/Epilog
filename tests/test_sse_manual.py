import asyncio
import httpx
import json

async def test_sse():
    url = "http://localhost:8000/api/v1/traces/sessions/5e6dd95f-2033-4c4f-8165-673832d21369/events/stream"
    print(f"Connecting to {url}...")
    
    try:
        async with httpx.AsyncClient(timeout=None) as client:
            async with client.stream("GET", url) as response:
                print(f"Status: {response.status_code}")
                async for line in response.aiter_lines():
                    if line.startswith("data: "):
                        data = json.loads(line[len("data: "):])
                        print(f"Received: {data}")
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    asyncio.run(test_sse())
