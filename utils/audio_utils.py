import logging
import subprocess
import json
from pathlib import Path

logger = logging.getLogger(__name__)


def get_ffmpeg_path() -> str:
    import shutil
    system_ffmpeg = shutil.which("ffmpeg")
    if system_ffmpeg:
        return system_ffmpeg
    try:
        import imageio_ffmpeg
        return imageio_ffmpeg.get_ffmpeg_exe()
    except Exception:
        return "ffmpeg"


def get_audio_duration(audio_path: Path) -> float:
    ffmpeg = get_ffmpeg_path()
    result = subprocess.run(
        [ffmpeg, "-i", str(audio_path), "-f", "null", "-"],
        capture_output=True, text=True
    )
    for line in result.stderr.split("\n"):
        if "Duration" in line:
            parts = line.split("Duration:")[1].split(",")[0].strip()
            h, m, s = parts.split(":")
            return float(h) * 3600 + float(m) * 60 + float(s)
    return 0.0


def trim_audio(input_path: Path, output_path: Path, duration: float) -> Path:
    ffmpeg = get_ffmpeg_path()
    subprocess.run(
        [
            ffmpeg, "-y", "-i", str(input_path),
            "-t", str(duration),
            "-af", f"afade=t=out:st={duration - 1}:d=1",
            "-c:a", "aac", "-b:a", "192k",
            str(output_path),
        ],
        capture_output=True, check=True,
    )
    return output_path


def mix_audio(
    voiceover_path: Path,
    music_path: Path | None,
    output_path: Path,
    duration: float,
    music_volume: float = 0.25,
    voice_volume: float = 1.0,
) -> Path:
    ffmpeg = get_ffmpeg_path()

    if music_path and music_path.exists():
        fade_start = max(duration - 1.5, 0)
        subprocess.run(
            [
                ffmpeg, "-y",
                "-i", str(voiceover_path),
                "-i", str(music_path),
                "-filter_complex",
                (
                    f"[0:a]volume={voice_volume}[vo];"
                    f"[1:a]volume={music_volume},afade=t=out:st={fade_start}:d=1.5,"
                    f"atrim=0:{duration}[mus];"
                    f"[vo][mus]amix=inputs=2:duration=first:dropout_transition=1,"
                    f"loudnorm=I=-16:TP=-1.5:LRA=11[out]"
                ),
                "-map", "[out]",
                "-t", str(duration),
                "-c:a", "aac", "-b:a", "192k",
                str(output_path),
            ],
            capture_output=True, check=True,
        )
    else:
        subprocess.run(
            [
                ffmpeg, "-y",
                "-i", str(voiceover_path),
                "-af", f"volume={voice_volume}",
                "-t", str(duration),
                "-c:a", "aac", "-b:a", "192k",
                str(output_path),
            ],
            capture_output=True, check=True,
        )
    return output_path
