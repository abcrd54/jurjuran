import httpx
import logging

logger = logging.getLogger(__name__)

SCRIPT_PROMPT = """Kamu adalah copywriter profesional untuk video promosi produk Shopee.

Buatkan narasi dubbing untuk video pendek vertikal (15-30 detik) berdasarkan info produk berikut:

Nama Produk: {name}
Harga: {price}
Deskripsi: {description}
Rating: {rating}
Terjual: {sold}
Toko: {shop_name}

Aturan:
1. Bahasa Indonesia yang natural dan persuasif
2. Panjang 60-80 kata (sekitar 20-25 detik saat dibacakan)
3. Langsung ke poin, tidak bertele-tele
4. Sebutkan nama produk, keunggulan utama, dan harga
5. Ajakan bertindak di akhir (misal: "Beli sekarang di Shopee!")
6. Jangan gunakan emoji atau simbol khusus
7. Format: hanya teks narasi, tanpa judul atau penjelasan

Narasi:"""


def _build_fallback_script(product_info: dict) -> str:
    name = product_info.get("name", "Produk ini")
    price = product_info.get("price", "")
    desc = product_info.get("description", "")
    rating = product_info.get("rating", "")
    sold = product_info.get("sold", "")

    short_name = name[:60] if len(name) > 60 else name

    highlights = ""
    if desc:
        lines = [l.strip() for l in desc.replace("\r", "").split("\n") if l.strip()]
        keywords = []
        for line in lines:
            for kw in ["bahan", "busui", "premium", "nyaman", "elegant", "elegan",
                        "kekinian", "friendly", "desain", "kualitas", "cocok"]:
                if kw in line.lower():
                    keywords.append(line.strip("- •�? "))
                    break
        if keywords:
            highlights = ". ".join(keywords[:2])

    parts = [f"{short_name}."]
    if highlights:
        parts.append(highlights + ".")
    if price and price != "Harga tidak tersedia":
        parts.append(f"Harga hanya {price}.")
    if rating and rating != "-":
        parts.append(f"Rating {rating}.")
    if sold and sold not in ("-", "None", "1000+"):
        parts.append(f"Sudah terjual {sold}.")
    parts.append("Tersedia di Shopee. Beli sekarang sebelum kehabisan!")

    script = " ".join(parts)

    words = script.split()
    if len(words) > 80:
        script = " ".join(words[:80]) + "."

    return script


async def generate_script(
    product_info: dict,
    base_url: str,
    model: str,
    api_key: str,
) -> str:
    prompt = SCRIPT_PROMPT.format(
        name=product_info.get("name", "Produk"),
        price=product_info.get("price", "Harga tidak tersedia"),
        description=product_info.get("description", "")[:500],
        rating=product_info.get("rating", "-"),
        sold=product_info.get("sold", "-"),
        shop_name=product_info.get("shop_name", "Shopee"),
    )

    try:
        logger.info(f"Generating script via AI ({base_url})")
        async with httpx.AsyncClient(timeout=30) as client:
            resp = await client.post(
                f"{base_url}/chat/completions",
                json={
                    "model": model,
                    "messages": [
                        {"role": "system", "content": "Kamu adalah copywriter video promosi produk."},
                        {"role": "user", "content": prompt},
                    ],
                    "temperature": 0.7,
                    "max_tokens": 300,
                },
                headers={
                    "Authorization": f"Bearer {api_key}",
                    "Content-Type": "application/json",
                },
            )
            resp.raise_for_status()
            result = resp.json()

        script = result["choices"][0]["message"]["content"].strip()
        script = script.strip('"').strip("'")
        if script.startswith("Narasi:"):
            script = script[7:].strip()

    except Exception as e:
        logger.warning(f"AI service unavailable ({e}), using fallback script")
        script = _build_fallback_script(product_info)

    logger.info(f"Script ({len(script.split())} words): {script[:120]}...")
    return script
