import asyncio
import httpx
from datetime import datetime
from pathlib import Path

API_URL = "http://localhost:8000/api/generate"


async def main():
    print("=" * 55)
    print("  Shopee Video Generator v2")
    print("=" * 55)
    print()

    shopee_url = input("Masukkan link Shopee: ").strip()
    if not shopee_url:
        print("Error: Link tidak boleh kosong!")
        return

    music_path = input("Path file musik (kosongkan jika tidak ada): ").strip()
    if music_path and not Path(music_path).exists():
        print(f"Error: File musik tidak ditemukan: {music_path}")
        return

    print()
    print("Voice:")
    print("  1. ArdiNeural (male)")
    print("  2. GadisNeural (female)")
    voice = input("Pilih voice [1]: ").strip()
    voice_id = "id-ID-GadisNeural" if voice == "2" else "id-ID-ArdiNeural"

    print()
    print("Template:")
    print("  1. Promo    - Zoom dinamis, transisi fade, warna vivid")
    print("  2. Review   - Zoom halus, transisi fadeblack, warna natural")
    print("  3. Unboxing - Zoom cepat, transisi slide, warna vivid")
    print("  4. Minimal  - Zoom sangat halus, transisi fade, warna soft")
    tpl = input("Pilih template [1]: ").strip()
    template = {"2": "review", "3": "unboxing", "4": "minimal"}.get(tpl, "promo")

    print()
    print("Aspect Ratio:")
    print("  1. 9:16  - Vertikal (Reels/TikTok/Shorts)")
    print("  2. 1:1   - Kotak (Instagram Feed)")
    print("  3. 16:9  - Landscape (YouTube)")
    ratio = input("Pilih aspect ratio [1]: ").strip()
    aspect = {"2": "1:1", "3": "16:9"}.get(ratio, "9:16")

    print()
    print(f"Link:         {shopee_url}")
    print(f"Voice:        {voice_id}")
    print(f"Template:     {template}")
    print(f"Aspect Ratio: {aspect}")
    print(f"Musik:        {music_path or '(tanpa musik)'}")
    print()
    print("Memproses video... (mungkin butuh 1-2 menit)")

    async with httpx.AsyncClient(timeout=300) as client:
        files = {}
        if music_path:
            files["music"] = (
                Path(music_path).name,
                open(music_path, "rb"),
                "audio/mpeg",
            )

        resp = await client.post(
            API_URL,
            data={
                "shopee_url": shopee_url,
                "voice": voice_id,
                "template": template,
                "aspect_ratio": aspect,
            },
            files=files if files else None,
        )

    if resp.status_code == 200:
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        output_dir = Path("output")
        output_dir.mkdir(exist_ok=True)
        output = output_dir / f"video_{timestamp}.mp4"
        output.write_bytes(resp.content)
        size_mb = len(resp.content) / 1024 / 1024
        print()
        print(f"Berhasil! Video disimpan: {output.absolute()}")
        print(f"Ukuran: {size_mb:.1f} MB")
    else:
        print()
        print(f"Gagal! Status: {resp.status_code}")
        try:
            print(resp.json())
        except Exception:
            print(resp.text[:500])


if __name__ == "__main__":
    asyncio.run(main())
