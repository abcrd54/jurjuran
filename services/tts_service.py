import edge_tts
import asyncio
import logging
from pathlib import Path
from config import TTS_VOICE, TTS_RATE

logger = logging.getLogger(__name__)


def _split_sentence_to_words(sentence_text: str, start: float, duration: float) -> list[dict]:
    words = sentence_text.split()
    if not words:
        return []

    word_duration = duration / len(words)
    timings = []

    for i, word in enumerate(words):
        timings.append({
            "text": word,
            "offset": start + (i * word_duration),
            "duration": word_duration,
        })

    return timings


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
    logger.info(f"Generating TTS with timestamps (edge-tts {edge_tts.__version__})")

    communicate = edge_tts.Communicate(text, voice, rate=rate)
    word_timings = []
    sentence_timings = []
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
        elif chunk["type"] == "SentenceBoundary":
            sentence_timings.append({
                "text": chunk["text"],
                "offset": chunk["offset"] / 10_000_000,
                "duration": chunk["duration"] / 10_000_000,
            })

    output_path.parent.mkdir(parents=True, exist_ok=True)
    with open(output_path, "wb") as f:
        for chunk in audio_chunks:
            f.write(chunk)

    if word_timings:
        timings = word_timings
        timing_type = "word"
    elif sentence_timings:
        timings = []
        for sent in sentence_timings:
            timings.extend(_split_sentence_to_words(sent["text"], sent["offset"], sent["duration"]))
        timing_type = "word (from sentence)"
    else:
        timings = []
        timing_type = "none"

    logger.info(f"TTS saved: {len(timings)} {timing_type} timings")

    if not timings:
        logger.warning("No timings received - captions will use estimated timing")

    return output_path, timings
