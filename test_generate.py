import asyncio
import sys
import httpx
from datetime import datetime
from pathlib import Path


async def test_generate():
    url = "http://localhost:8000/api/generate"
    shopee_url = sys.argv[1] if len(sys.argv) > 1 else "https://s.shopee.co.id/8ASztTawGm"

    print(f"Testing video generation...")
    print(f"Shopee URL: {shopee_url}")
    print(f"API: {url}")
    print()

    async with httpx.AsyncClient(timeout=300) as client:
        print("Sending request (this may take 1-2 minutes)...")
        resp = await client.post(
            url,
            data={"shopee_url": shopee_url},
        )

        if resp.status_code == 200:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            output_dir = Path("output")
            output_dir.mkdir(exist_ok=True)
            output_file = output_dir / f"test_{timestamp}.mp4"
            with open(output_file, "wb") as f:
                f.write(resp.content)
            print(f"SUCCESS! Video saved to: {output_file}")
            print(f"Size: {len(resp.content) / 1024 / 1024:.1f} MB")
        else:
            print(f"FAILED: {resp.status_code}")
            print(resp.text)


if __name__ == "__main__":
    asyncio.run(test_generate())
