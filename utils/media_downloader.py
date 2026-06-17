import httpx
import asyncio
import logging
from pathlib import Path

logger = logging.getLogger(__name__)


async def download_file(url: str, dest: Path, timeout: int = 30) -> Path:
    async with httpx.AsyncClient(follow_redirects=True, timeout=timeout) as client:
        resp = await client.get(url)
        resp.raise_for_status()
        dest.parent.mkdir(parents=True, exist_ok=True)
        dest.write_bytes(resp.content)
        logger.info(f"Downloaded: {dest.name}")
        return dest


async def download_media_files(
    images: list[str],
    videos: list[str],
    work_dir: Path,
) -> tuple[list[Path], list[Path]]:
    tasks = []

    for i, url in enumerate(images):
        ext = ".jpg"
        if ".png" in url.lower():
            ext = ".png"
        elif ".webp" in url.lower():
            ext = ".webp"
        dest = work_dir / f"image_{i:03d}{ext}"
        tasks.append(download_file(url, dest))

    for i, url in enumerate(videos):
        ext = ".mp4"
        if ".webm" in url.lower():
            ext = ".webm"
        dest = work_dir / f"video_{i:03d}{ext}"
        tasks.append(download_file(url, dest, timeout=60))

    results = await asyncio.gather(*tasks, return_exceptions=True)

    downloaded_images = []
    downloaded_videos = []

    for i, result in enumerate(results):
        if isinstance(result, Exception):
            logger.warning(f"Download failed: {result}")
        elif i < len(images):
            downloaded_images.append(result)
        else:
            downloaded_videos.append(result)

    logger.info(f"Downloaded: {len(downloaded_images)} images, {len(downloaded_videos)} videos")
    return downloaded_images, downloaded_videos
