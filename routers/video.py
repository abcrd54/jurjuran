import asyncio
import logging
import shutil
import uuid
from datetime import datetime
from pathlib import Path
from fastapi import APIRouter, UploadFile, File, Form, HTTPException, Query
from fastapi.responses import FileResponse

from config import (
    SCRAPER_URL, AI_BASE_URL, AI_MODEL, AI_API_KEY,
    TTS_VOICE, TEMP_DIR, OUTPUT_DIR, UPLOAD_DIR,
    TEMPLATES, DEFAULT_TEMPLATE, ASPECT_RATIOS, DEFAULT_ASPECT_RATIO,
)
from services.scraper import scrape_shopee
from services.script_generator import generate_script
from services.tts_service import generate_tts, generate_tts_with_timestamps
from services.video_composer import compose_video
from services.progress import progress_manager, Step
from utils.media_downloader import download_media_files
from utils.caption_renderer import (
    build_captions_from_timestamps, split_script_to_captions, burn_captions,
)

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api", tags=["video"])


@router.post("/generate")
async def generate_video(
    shopee_url: str = Form(...),
    music: UploadFile = File(None),
    voice: str = Form(default=TTS_VOICE),
    template: str = Form(default=DEFAULT_TEMPLATE),
    aspect_ratio: str = Form(default=DEFAULT_ASPECT_RATIO),
    request_id: str = Form(default=None),
):
    if template not in TEMPLATES:
        raise HTTPException(400, f"Template '{template}' tidak tersedia. Pilih: {list(TEMPLATES.keys())}")
    if aspect_ratio not in ASPECT_RATIOS:
        raise HTTPException(400, f"Aspect ratio '{aspect_ratio}' tidak tersedia. Pilih: {list(ASPECT_RATIOS.keys())}")

    if not request_id:
        request_id = uuid.uuid4().hex[:12]
    work_dir = TEMP_DIR / request_id
    work_dir.mkdir(parents=True, exist_ok=True)
    tracker = progress_manager.create(request_id)
    music_path = None

    try:
        logger.info(f"[{request_id}] Starting: url={shopee_url}, template={template}, ratio={aspect_ratio}")

        tracker.update(Step.SCRAPE, "Mengambil data produk dari Shopee...")
        product_info = await scrape_shopee(shopee_url, SCRAPER_URL)
        tracker.details["product_name"] = product_info.get("name", "")[:50]
        tracker.details["images_count"] = len(product_info.get("images", []))

        if not product_info.get("images"):
            raise HTTPException(400, "No product images found")

        tracker.update(Step.SCRIPT, "Membuat script dubbing...")
        script = await generate_script(product_info, AI_BASE_URL, AI_MODEL, AI_API_KEY)
        script_file = work_dir / "script.txt"
        script_file.write_text(script, encoding="utf-8")
        tracker.details["script_words"] = len(script.split())

        tracker.update(Step.TTS, "Membuat suara dubbing...")
        voiceover_path = work_dir / "voiceover.mp3"
        voiceover_path, word_timings = await generate_tts_with_timestamps(
            script, voiceover_path, voice=voice
        )
        tracker.details["word_timings_count"] = len(word_timings)
        logger.info(f"[{request_id}] Word timings: {len(word_timings)}")

        tracker.update(Step.MEDIA, "Mengunduh foto dan video produk...")
        images, videos = await download_media_files(
            product_info["images"],
            product_info.get("videos", []),
            work_dir / "media",
        )
        tracker.details["downloaded_images"] = len(images)
        tracker.details["downloaded_videos"] = len(videos)

        if music:
            music_path = UPLOAD_DIR / f"{request_id}_{music.filename}"
            with open(music_path, "wb") as f:
                content = await music.read()
                f.write(content)

        tracker.update(Step.COMPOSE, "Menggabungkan video...")
        template_config = TEMPLATES[template]
        ratio_config = ASPECT_RATIOS[aspect_ratio]

        final_video, duration = await compose_video(
            images=images,
            videos=videos,
            voiceover_path=voiceover_path,
            music_path=music_path,
            work_dir=work_dir,
            script=script,
            product_info=product_info,
            template=template_config,
            aspect_ratio=ratio_config,
        )
        tracker.details["video_duration"] = round(duration, 1)

        tracker.update(Step.CAPTION, "Menambahkan caption...")
        if word_timings:
            captions = build_captions_from_timestamps(
                word_timings, segment_duration=1.8, time_offset=0
            )
        else:
            captions = split_script_to_captions(script, duration, words_per_caption=6)

        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        output_filename = f"video_{timestamp}_{request_id}.mp4"
        output_path = OUTPUT_DIR / output_filename
        burn_captions(final_video, output_path, captions, template_config.get("caption_style", "modern"))

        tracker.finish()
        tracker.details["output_file"] = output_filename

        from fastapi.responses import Response
        response = FileResponse(
            path=output_path,
            media_type="video/mp4",
            filename=output_filename,
        )
        response.headers["X-Request-ID"] = request_id
        return response

    except HTTPException:
        raise
    except Exception as e:
        tracker.fail(str(e))
        logger.error(f"[{request_id}] Error: {e}", exc_info=True)
        raise HTTPException(500, detail=str(e))

    finally:
        try:
            shutil.rmtree(work_dir, ignore_errors=True)
            if music_path and music_path.exists():
                music_path.unlink(missing_ok=True)
        except Exception:
            pass


@router.get("/progress/{request_id}")
async def get_progress(request_id: str):
    tracker = progress_manager.get(request_id)
    if not tracker:
        raise HTTPException(404, "Request not found")
    return tracker.to_dict()


@router.get("/templates")
async def list_templates():
    return {
        name: {
            "name": config["name"],
            "transition": config["transition"],
            "intro_duration": config["intro_duration"],
        }
        for name, config in TEMPLATES.items()
    }


@router.get("/aspect-ratios")
async def list_aspect_ratios():
    return ASPECT_RATIOS


@router.get("/voices")
async def list_voices():
    return {
        "id-ID-ArdiNeural": {"name": "Ardi", "gender": "Male"},
        "id-ID-GadisNeural": {"name": "Gadis", "gender": "Female"},
    }


@router.post("/batch")
async def batch_generate(
    shopee_urls: str = Form(...),
    music: UploadFile = File(None),
    voice: str = Form(default=TTS_VOICE),
    template: str = Form(default=DEFAULT_TEMPLATE),
    aspect_ratio: str = Form(default=DEFAULT_ASPECT_RATIO),
):
    urls = [u.strip() for u in shopee_urls.split(",") if u.strip()]
    if not urls:
        raise HTTPException(400, "No URLs provided")
    if len(urls) > 5:
        raise HTTPException(400, "Maximum 5 URLs per batch")

    results = []
    for url in urls:
        try:
            request_id = uuid.uuid4().hex[:12]
            results.append({
                "url": url,
                "request_id": request_id,
                "status": "queued",
                "progress_url": f"/api/progress/{request_id}",
            })
        except Exception as e:
            results.append({"url": url, "error": str(e)})

    return {"batch_id": uuid.uuid4().hex[:8], "total": len(urls), "results": results}


@router.get("/health")
async def health():
    return {"status": "ok", "service": "gen-video"}
