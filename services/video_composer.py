import logging
import subprocess
from pathlib import Path

logger = logging.getLogger(__name__)


def get_ffmpeg_path() -> str:
    try:
        import imageio_ffmpeg
        return imageio_ffmpeg.get_ffmpeg_exe()
    except Exception:
        return "ffmpeg"


def get_media_duration(path: Path) -> float:
    ffmpeg = get_ffmpeg_path()
    result = subprocess.run(
        [ffmpeg, "-i", str(path), "-f", "null", "-"],
        capture_output=True, text=True
    )
    for line in result.stderr.split("\n"):
        if "Duration" in line:
            parts = line.split("Duration:")[1].split(",")[0].strip()
            h, m, s = parts.split(":")
            return float(h) * 3600 + float(m) * 60 + float(s)
    return 0.0


def prepare_image(
    image_path: Path, output_path: Path, duration: float,
    index: int = 0, width: int = 1080, height: int = 1920,
    zoom_speed: float = 0.0004, zoom_max: float = 1.08,
    color_grading: str = "eq=brightness=0.02:saturation=1.1:contrast=1.05",
) -> Path:
    ffmpeg = get_ffmpeg_path()
    frames = int(duration * 30)

    if index % 2 == 0:
        zoom_expr = f"min(zoom+{zoom_speed},{zoom_max})"
    else:
        zoom_expr = f"max({zoom_max}-(on/{frames})*({zoom_max}-1.0),1.0)"

    vf = (
        f"scale={width}:{height}:force_original_aspect_ratio=increase,"
        f"crop={width}:{height},"
        f"zoompan=z='{zoom_expr}':x='iw/2-(iw/zoom/2)':y='ih/2-(ih/zoom/2)'"
        f":d={frames}:s={width}x{height}:fps=30,"
        f"{color_grading}"
    )

    subprocess.run(
        [
            ffmpeg, "-y", "-loop", "1", "-i", str(image_path),
            "-t", str(duration), "-vf", vf,
            "-c:v", "libx264", "-preset", "fast", "-pix_fmt", "yuv420p",
            "-an", str(output_path),
        ],
        capture_output=True, check=True,
    )
    return output_path


def prepare_video(
    video_path: Path, output_path: Path, max_duration: float,
    width: int = 1080, height: int = 1920,
    color_grading: str = "eq=brightness=0.02:saturation=1.1:contrast=1.05",
) -> float:
    ffmpeg = get_ffmpeg_path()
    duration = get_media_duration(video_path)
    use_duration = min(duration, max_duration)

    vf = (
        f"scale={width}:{height}:force_original_aspect_ratio=increase,"
        f"crop={width}:{height},"
        f"{color_grading}"
    )

    subprocess.run(
        [
            ffmpeg, "-y", "-i", str(video_path),
            "-t", str(use_duration), "-vf", vf,
            "-c:v", "libx264", "-preset", "fast", "-pix_fmt", "yuv420p",
            "-an", str(output_path),
        ],
        capture_output=True, check=True,
    )
    return use_duration


def create_text_clip(
    text: str, output_path: Path, duration: float,
    width: int = 1080, height: int = 1920,
    font_size: int = 60, color: str = "white",
    y_position: str = "(h-text_h)/2",
) -> Path:
    ffmpeg = get_ffmpeg_path()
    safe_text = text.replace("'", "\u2019").replace(":", " ")

    vf = (
        f"drawtext=text='{safe_text}'"
        f":fontfile='C\\\\:/Windows/Fonts/arialbd.ttf'"
        f":fontsize={font_size}"
        f":fontcolor={color}"
        f":borderw=2:bordercolor=black"
        f":x=(w-text_w)/2:y={y_position}"
    )

    subprocess.run(
        [
            ffmpeg, "-y",
            "-f", "lavfi", "-i",
            f"color=c=black@0.0:s={width}x{height}:d={duration}:r=30",
            "-vf", vf,
            "-c:v", "libx264", "-preset", "fast", "-pix_fmt", "yuv420p",
            "-an", str(output_path),
        ],
        capture_output=True, check=True,
    )
    return output_path


def concat_with_xfade(clips: list[Path], output_path: Path, fade_dur: float = 0.5, transition: str = "fade") -> Path:
    ffmpeg = get_ffmpeg_path()

    if len(clips) == 1:
        import shutil
        shutil.copy2(clips[0], output_path)
        return output_path

    if len(clips) == 2:
        dur0 = get_media_duration(clips[0])
        offset = max(0, dur0 - fade_dur)
        subprocess.run(
            [
                ffmpeg, "-y",
                "-i", str(clips[0]), "-i", str(clips[1]),
                "-filter_complex",
                f"[0:v][1:v]xfade=transition={transition}:duration={fade_dur}:offset={offset}[v]",
                "-map", "[v]",
                "-c:v", "libx264", "-preset", "fast", "-pix_fmt", "yuv420p",
                "-an", str(output_path),
            ],
            capture_output=True, check=True,
        )
        return output_path

    inputs = []
    for c in clips:
        inputs.extend(["-i", str(c)])

    filter_parts = []
    current_label = "[0:v]"
    cumulative_offset = 0

    for i in range(len(clips) - 1):
        dur = get_media_duration(clips[i])
        offset = max(0, cumulative_offset + dur - fade_dur)
        next_label = f"[v{i}]" if i < len(clips) - 2 else "[vout]"
        filter_parts.append(
            f"{current_label}[{i+1}:v]xfade=transition={transition}:duration={fade_dur}:offset={offset}{next_label}"
        )
        current_label = next_label
        cumulative_offset = offset

    filter_complex = ";".join(filter_parts)
    cmd = [ffmpeg, "-y"] + inputs + [
        "-filter_complex", filter_complex,
        "-map", "[vout]",
        "-c:v", "libx264", "-preset", "fast", "-pix_fmt", "yuv420p",
        "-an", str(output_path),
    ]

    result = subprocess.run(cmd, capture_output=True, text=True)
    if result.returncode != 0:
        logger.warning(f"xfade failed, falling back to simple concat")
        concat_videos_simple(clips, output_path)

    return output_path


def concat_videos_simple(inputs: list[Path], output_path: Path) -> Path:
    ffmpeg = get_ffmpeg_path()
    list_file = output_path.parent / "concat_list.txt"

    with open(list_file, "w", encoding="utf-8") as f:
        for p in inputs:
            f.write(f"file '{p.as_posix()}'\n")

    subprocess.run(
        [
            ffmpeg, "-y", "-f", "concat", "-safe", "0",
            "-i", str(list_file),
            "-c:v", "libx264", "-preset", "fast", "-pix_fmt", "yuv420p",
            "-an", str(output_path),
        ],
        capture_output=True, check=True,
    )
    list_file.unlink(missing_ok=True)
    return output_path


def add_audio_to_video(
    video_path: Path, audio_path: Path, output_path: Path,
    duration: float | None = None,
) -> Path:
    ffmpeg = get_ffmpeg_path()
    cmd = [
        ffmpeg, "-y",
        "-i", str(video_path), "-i", str(audio_path),
        "-c:v", "copy", "-c:a", "aac", "-b:a", "192k",
        "-map", "0:v:0", "-map", "1:a:0",
    ]
    if duration:
        cmd.extend(["-t", str(duration)])
    cmd.append(str(output_path))
    subprocess.run(cmd, capture_output=True, check=True)
    return output_path


async def compose_video(
    images: list[Path],
    videos: list[Path],
    voiceover_path: Path,
    music_path: Path | None,
    work_dir: Path,
    script: str,
    product_info: dict = None,
    template: dict = None,
    aspect_ratio: dict = None,
) -> tuple[Path, float]:
    from utils.audio_utils import get_audio_duration, mix_audio
    from config import VIDEO_MIN_DURATION, VIDEO_MAX_DURATION, TRANSITION_DURATION

    if template is None:
        from config import TEMPLATES, DEFAULT_TEMPLATE
        template = TEMPLATES[DEFAULT_TEMPLATE]
    if aspect_ratio is None:
        from config import ASPECT_RATIOS, DEFAULT_ASPECT_RATIO
        aspect_ratio = ASPECT_RATIOS[DEFAULT_ASPECT_RATIO]

    width = aspect_ratio["width"]
    height = aspect_ratio["height"]
    zoom_speed = template.get("zoom_speed", 0.0004)
    zoom_max = template.get("zoom_max", 1.08)
    transition = template.get("transition", "fade")
    color_grading = template.get("color_grading", "eq=brightness=0.02:saturation=1.1:contrast=1.05")
    intro_duration = template.get("intro_duration", 3.5)

    vo_duration = get_audio_duration(voiceover_path)
    total_duration = min(max(vo_duration, VIDEO_MIN_DURATION), VIDEO_MAX_DURATION)

    logger.info(f"Composing: {len(images)} images, {len(videos)} videos, "
                f"{width}x{height}, template={transition}, duration={total_duration:.1f}s")

    clips = []

    if product_info and product_info.get("name"):
        intro_path = work_dir / "intro.mp4"
        name = product_info["name"][:50]
        create_text_clip(name, intro_path, intro_duration, width, height, font_size=52)
        clips.append(intro_path)

        price = product_info.get("price", "")
        if price and price != "Harga tidak tersedia":
            price_path = work_dir / "price_intro.mp4"
            create_text_clip(price, price_path, 1.5, width, height, font_size=64, color="yellow",
                           y_position="(h-text_h)/2+80")
            clips.append(price_path)

    if videos:
        video_clip_path = work_dir / "video_part.mp4"
        vid_share = total_duration * 0.3 if images else total_duration * 0.8
        actual_vid_dur = prepare_video(videos[0], video_clip_path, vid_share, width, height, color_grading)
        clips.append(video_clip_path)

    if images:
        n_images = min(len(images), 10)
        remaining = total_duration - sum(get_media_duration(c) for c in clips)
        per_image = max(remaining / n_images, 1.5)

        for i in range(n_images):
            img_clip = work_dir / f"img_clip_{i:03d}.mp4"
            try:
                prepare_image(images[i], img_clip, per_image, i, width, height,
                            zoom_speed, zoom_max, color_grading)
                clips.append(img_clip)
            except Exception as e:
                logger.warning(f"Failed to prepare image {i}: {e}")

    if not clips:
        raise Exception("No media clips could be prepared")

    video_parts_path = work_dir / "video_parts.mp4"
    if len(clips) == 1:
        import shutil
        shutil.copy2(clips[0], video_parts_path)
    else:
        try:
            concat_with_xfade(clips, video_parts_path, TRANSITION_DURATION, transition)
        except Exception as e:
            logger.warning(f"Crossfade failed: {e}, using simple concat")
            concat_videos_simple(clips, video_parts_path)

    mixed_audio = work_dir / "mixed_audio.m4a"
    mix_audio(voiceover_path, music_path, mixed_audio, total_duration)

    final_video = work_dir / "final_video.mp4"
    add_audio_to_video(video_parts_path, mixed_audio, final_video, total_duration)

    logger.info(f"Video composed: {final_video}")
    return final_video, total_duration
