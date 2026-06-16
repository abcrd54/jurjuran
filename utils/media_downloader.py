import httpx
import logging
from pathlib import Path

logger = logging.getLogger(__name__)


async def download_file(url: str, dest: Path, timeout: int = 30) -> Path:
    async with httpx.AsyncClient(follow_redirects=True, timeout=timeout) as client:
        resp = await client.get(url)
        resp.raise_for_status()
        dest.parent.mkdir(parents=True, exist_ok=True)
        dest.write_bytes(resp.content)
        logger.info(f"Downloaded: {url} -> {dest}")
        return dest


async def download_media_files(
    images: list[str],
    videos: list[str],
    work_dir: Path,
) -> tuple[list[Path], list[Path]]:
    downloaded_images = []
    downloaded_videos = []

    for i, url in enumerate(images):
        ext = ".jpg"
        if ".png" in url.lower():
            ext = ".png"
        elif ".webp" in url.lower():
            ext = ".webp"
        dest = work_dir / f"image_{i:03d}{ext}"
        try:
            path = await download_file(url, dest)
            downloaded_images.append(path)
        except Exception as e:
            logger.warning(f"Failed to download image {url}: {e}")

    for i, url in enumerate(videos):
        ext = ".mp4"
        if ".webm" in url.lower():
            ext = ".webm"
        dest = work_dir / f"video_{i:03d}{ext}"
        try:
            path = await download_file(url, dest, timeout=60)
            downloaded_videos.append(path)
        except Exception as e:
            logger.warning(f"Failed to download video {url}: {e}")

    return downloaded_images, downloaded_videos
