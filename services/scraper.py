import httpx
import logging
import re

logger = logging.getLogger(__name__)

SHOPEE_CDN_PATTERNS = [
    r"https?://cf\.shopee\.[a-z.]+/file/[a-zA-Z0-9_-]+",
    r"https?://down-id\.img\.svcdn\.net/[^\s\"']+",
    r"https?://img\.srv\.sqp\.shopee\.id/[^\s\"']+",
]


def extract_media_urls(raw_data: dict) -> tuple[list[str], list[str]]:
    images = []
    videos = []

    if isinstance(raw_data, dict):
        for key in ["images", "cover_image", "long_images", "tier_images"]:
            val = raw_data.get(key)
            if isinstance(val, list):
                images.extend([v for v in val if isinstance(v, str)])
            elif isinstance(val, str) and val:
                images.append(val)

        video_data = raw_data.get("videos", [])
        if isinstance(video_data, list):
            for v in video_data:
                if isinstance(v, dict) and v.get("url"):
                    videos.append(v["url"])
                elif isinstance(v, str):
                    videos.append(v)

        if "data" in raw_data and isinstance(raw_data["data"], dict):
            sub_img, sub_vid = extract_media_urls(raw_data["data"])
            images.extend(sub_img)
            videos.extend(sub_vid)

    if not images and isinstance(raw_data, dict):
        raw_str = str(raw_data)
        for pattern in SHOPEE_CDN_PATTERNS:
            found = re.findall(pattern, raw_str)
            img_candidates = [u for u in found if not any(
                ext in u.lower() for ext in [".mp4", ".webm", ".m3u8", ".mpd"]
            )]
            vid_candidates = [u for u in found if any(
                ext in u.lower() for ext in [".mp4", ".webm", ".m3u8", ".mpd"]
            )]
            images.extend(img_candidates)
            videos.extend(vid_candidates)

    seen = set()
    unique_images = []
    for u in images:
        if u not in seen:
            seen.add(u)
            unique_images.append(u)

    seen = set()
    unique_videos = []
    for u in videos:
        if u not in seen:
            seen.add(u)
            unique_videos.append(u)

    return unique_images, unique_videos


def extract_product_info(data: dict) -> dict:
    if "data" in data and isinstance(data["data"], dict):
        data = data["data"]

    info = {}

    info["name"] = data.get("title") or data.get("name") or "Produk Shopee"
    info["description"] = data.get("description", "")

    price = data.get("price") or data.get("price_min") or data.get("price_range")
    if price:
        info["price"] = f"Rp {price}" if not str(price).startswith("Rp") else str(price)
    else:
        info["price"] = "Harga tidak tersedia"

    rating = data.get("rating")
    info["rating"] = str(round(rating, 1)) if rating else "-"

    sold = data.get("historical_sold") or data.get("global_sold")
    info["sold"] = str(sold) if sold else "1000+"

    info["shop_name"] = data.get("shop_location") or "Shopee"

    images, videos = extract_media_urls(data)
    info["images"] = images
    info["videos"] = videos

    return info


async def scrape_shopee(url: str, scraper_url: str) -> dict:
    logger.info(f"Scraping: {url}")
    async with httpx.AsyncClient(timeout=30) as client:
        resp = await client.post(
            scraper_url,
            json={"url": url},
            headers={"Content-Type": "application/json"},
        )
        resp.raise_for_status()
        result = resp.json()

    if not result.get("success"):
        error = result.get("error", {})
        raise Exception(f"Scrape failed: {error.get('message', 'Unknown error')}")

    raw_data = result.get("data", result)
    if "content" in raw_data and isinstance(raw_data["content"], dict):
        raw_data = raw_data["content"]
    product_info = extract_product_info(raw_data)

    logger.info(
        f"Scraped: {product_info.get('name', 'N/A')} | "
        f"{len(product_info.get('images', []))} images | "
        f"{len(product_info.get('videos', []))} videos"
    )

    return product_info
