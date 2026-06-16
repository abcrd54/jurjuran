import logging
import subprocess
from pathlib import Path
from config import (
    CAPTION_FONT, CAPTION_FONT_SIZE, CAPTION_COLOR,
    CAPTION_OUTLINE_COLOR, CAPTION_OUTLINE_WIDTH, CAPTION_POSITION_Y,
    CAPTION_STYLES, VIDEO_WIDTH, VIDEO_HEIGHT,
)

logger = logging.getLogger(__name__)


def get_ffmpeg_path() -> str:
    try:
        import imageio_ffmpeg
        return imageio_ffmpeg.get_ffmpeg_exe()
    except Exception:
        return "ffmpeg"


def build_captions_from_timestamps(
    word_timings: list[dict],
    segment_duration: float = 1.8,
    time_offset: float = 0.0,
) -> list[dict]:
    if not word_timings:
        return []

    captions = []
    current_words = []
    current_start = None

    for timing in word_timings:
        if current_start is None:
            current_start = max(0, timing["offset"] - 0.1)

        current_words.append(timing["text"])
        current_duration = (timing["offset"] + timing["duration"]) - current_start

        if current_duration >= segment_duration:
            end_time = timing["offset"] + timing["duration"]
            captions.append({
                "start": round(current_start + time_offset, 3),
                "end": round(end_time + time_offset, 3),
                "text": " ".join(current_words),
            })
            current_words = []
            current_start = None

    if current_words:
        last = word_timings[-1]
        end_time = last["offset"] + last["duration"]
        captions.append({
            "start": round(current_start + time_offset, 3),
            "end": round(end_time + time_offset, 3),
            "text": " ".join(current_words),
        })

    return captions


def split_script_to_captions(
    script: str,
    total_duration: float,
    words_per_caption: int = 6,
) -> list[dict]:
    words = script.split()
    if not words:
        return []

    segments = []
    for i in range(0, len(words), words_per_caption):
        segments.append(" ".join(words[i : i + words_per_caption]))

    time_per_segment = total_duration / len(segments)
    captions = []
    for i, text in enumerate(segments):
        start = i * time_per_segment
        end = (i + 1) * time_per_segment
        captions.append({
            "start": round(start, 3),
            "end": round(end, 3),
            "text": text,
        })

    return captions


def generate_ass(captions: list[dict], output_path: Path, style: str = "modern") -> Path:
    style_config = CAPTION_STYLES.get(style, CAPTION_STYLES["modern"])
    font_size = style_config.get("font_size", CAPTION_FONT_SIZE)
    bold = -1 if style_config.get("bold", True) else 0
    border_style = style_config.get("border_style", 3)
    outline = style_config.get("outline", CAPTION_OUTLINE_WIDTH)
    shadow = style_config.get("shadow", 0)
    back_color = style_config.get("back_color", "&H96000000")
    margin_v = CAPTION_POSITION_Y

    ass_content = f"""[Script Info]
Title: Shopee Video Captions
ScriptType: v4.00+
PlayResX: {VIDEO_WIDTH}
PlayResY: {VIDEO_HEIGHT}
WrapStyle: 0
ScaledBorderAndShadow: yes

[V4+ Styles]
Format: Name,Fontname,Fontsize,PrimaryColour,SecondaryColour,OutlineColour,BackColour,Bold,Italic,Underline,StrikeOut,ScaleX,ScaleY,Spacing,Angle,BorderStyle,Outline,Shadow,Alignment,MarginL,MarginR,MarginV,Encoding
Style: Default,{CAPTION_FONT},{font_size},&H00FFFFFF,&H000000FF,&H00000000,{back_color},{bold},0,0,0,100,100,1,0,{border_style},{outline},{shadow},2,40,40,{margin_v},1

[Events]
Format: Layer,Start,End,Style,Name,MarginL,MarginR,MarginV,Effect,Text
"""

    for cap in captions:
        start = _format_ass_time(cap["start"])
        end = _format_ass_time(cap["end"])
        text = cap["text"].replace("\n", "\\N")
        ass_content += f"Dialogue: 0,{start},{end},Default,,0,0,0,,{text}\n"

    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(ass_content, encoding="utf-8")
    return output_path


def _format_ass_time(seconds: float) -> str:
    h = int(seconds // 3600)
    m = int((seconds % 3600) // 60)
    s = int(seconds % 60)
    cs = int((seconds % 1) * 100)
    return f"{h}:{m:02d}:{s:02d}.{cs:02d}"


def generate_srt(captions: list[dict], output_path: Path) -> Path:
    with open(output_path, "w", encoding="utf-8") as f:
        for i, cap in enumerate(captions, 1):
            start = _format_srt_time(cap["start"])
            end = _format_srt_time(cap["end"])
            f.write(f"{i}\n{start} --> {end}\n{cap['text']}\n\n")
    return output_path


def _format_srt_time(seconds: float) -> str:
    h = int(seconds // 3600)
    m = int((seconds % 3600) // 60)
    s = int(seconds % 60)
    ms = int((seconds % 1) * 1000)
    return f"{h:02d}:{m:02d}:{s:02d},{ms:03d}"


def build_subtitle_filter(ass_path: Path) -> str:
    path_str = str(ass_path).replace("\\", "/").replace(":", "\\:")
    return f"ass='{path_str}'"


def burn_captions(
    input_video: Path,
    output_video: Path,
    captions: list[dict],
    style: str = "modern",
) -> Path:
    ffmpeg = get_ffmpeg_path()

    if not captions:
        import shutil
        shutil.copy2(input_video, output_video)
        return output_video

    ass_path = input_video.parent / "captions.ass"
    generate_ass(captions, ass_path, style)

    vf = build_subtitle_filter(ass_path)

    cmd = [
        ffmpeg, "-y",
        "-i", str(input_video),
        "-vf", vf,
        "-c:a", "copy",
        "-c:v", "libx264", "-preset", "fast", "-crf", "23",
        str(output_video),
    ]

    logger.info(f"Burning captions (style={style})")
    result = subprocess.run(cmd, capture_output=True, text=True)
    if result.returncode != 0:
        logger.error(f"FFmpeg stderr: {result.stderr[-1000:]}")
        raise subprocess.CalledProcessError(result.returncode, cmd, result.stdout, result.stderr)

    ass_path.unlink(missing_ok=True)
    return output_video
