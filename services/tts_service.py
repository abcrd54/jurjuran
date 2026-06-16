import edge_tts
import asyncio
import logging
from pathlib import Path
from config import TTS_VOICE, TTS_RATE

logger = logging.getLogger(__name__)


async def generate_tts(
    text: str,
    output_path: Path,
    voice: str = TTS_VOICE,
    rate: str = TTS_RATE,
) -> Path:
    logger.info(f"Generating TTS with voice={voice}, rate={rate}")

    communicate = edge_tts.Communicate(text, voice, rate=rate)
    await communicate.save(str(output_path))

    logger.info(f"TTS saved: {output_path}")
    return output_path


async def generate_tts_with_timestamps(
    text: str,
    output_path: Path,
    voice: str = TTS_VOICE,
    rate: str = TTS_RATE,
) -> tuple[Path, list[dict]]:
    logger.info(f"Generating TTS with word timestamps")

    communicate = edge_tts.Communicate(text, voice, rate=rate)
    word_timings = []
    audio_chunks = []

    async for chunk in communicate.stream():
        if chunk["type"] == "audio":
            audio_chunks.append(chunk["data"])
        elif chunk["type"] == "WordBoundary":
            word_timings.append({
                "text": chunk["text"],
                "offset": chunk["offset"] / 10_000_000,
                "duration": chunk["duration"] / 10_000_000,
            })

    output_path.parent.mkdir(parents=True, exist_ok=True)
    with open(output_path, "wb") as f:
        for chunk in audio_chunks:
            f.write(chunk)

    logger.info(f"TTS saved with {len(word_timings)} word timings: {output_path}")
    return output_path, word_timings
