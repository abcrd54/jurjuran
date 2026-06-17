import os
from pathlib import Path

BASE_DIR = Path(__file__).parent

SCRAPER_URL = os.getenv("SCRAPER_URL", "http://localhost:3000/api/scrape")

AI_BASE_URL = os.getenv("AI_BASE_URL", "http://192.168.28.199:20128/v1")
AI_MODEL = os.getenv("AI_MODEL", "cx/gpt-5.5")
AI_API_KEY = os.getenv("AI_API_KEY", "sk-placeholder")

TTS_VOICE = os.getenv("TTS_VOICE", "id-ID-ArdiNeural")
TTS_RATE = os.getenv("TTS_RATE", "+0%")

ASPECT_RATIOS = {
    "9:16": {"width": 1080, "height": 1920},
    "1:1": {"width": 1080, "height": 1080},
    "16:9": {"width": 1920, "height": 1080},
}
DEFAULT_ASPECT_RATIO = "9:16"

VIDEO_WIDTH = 1080
VIDEO_HEIGHT = 1920
VIDEO_FPS = 30
VIDEO_MIN_DURATION = 15
VIDEO_MAX_DURATION = 30
VIDEO_TARGET_DURATION = 25

TEMPLATES = {
    "promo": {
        "name": "Promo",
        "zoom_speed": 0.0004,
        "zoom_max": 1.08,
        "transition": "fade",
        "intro_duration": 3.5,
        "color_grading": "eq=brightness=0.02:saturation=1.1:contrast=1.05",
        "caption_style": "modern",
    },
    "review": {
        "name": "Review",
        "zoom_speed": 0.0002,
        "zoom_max": 1.05,
        "transition": "fadeblack",
        "intro_duration": 2.0,
        "color_grading": "eq=brightness=0.0:saturation=1.0:contrast=1.1",
        "caption_style": "clean",
    },
    "unboxing": {
        "name": "Unboxing",
        "zoom_speed": 0.0006,
        "zoom_max": 1.12,
        "transition": "slideleft",
        "intro_duration": 2.5,
        "color_grading": "eq=brightness=0.03:saturation=1.15:contrast=1.08",
        "caption_style": "bold",
    },
    "minimal": {
        "name": "Minimal",
        "zoom_speed": 0.0001,
        "zoom_max": 1.03,
        "transition": "fade",
        "intro_duration": 1.5,
        "color_grading": "eq=brightness=0.0:saturation=0.9:contrast=1.0",
        "caption_style": "minimal",
    },
}
DEFAULT_TEMPLATE = "promo"

CAPTION_FONT = "Arial"
CAPTION_FONT_SIZE = 44
CAPTION_COLOR = "white"
CAPTION_OUTLINE_COLOR = "black"
CAPTION_OUTLINE_WIDTH = 2
CAPTION_POSITION_Y = 100

CAPTION_STYLES = {
    "modern": {
        "font_size": 52,
        "bold": True,
        "border_style": 3,
        "outline": 2,
        "shadow": 0,
        "back_color": "&H96000000",
    },
    "clean": {
        "font_size": 48,
        "bold": False,
        "border_style": 1,
        "outline": 2,
        "shadow": 2,
        "back_color": "&H80000000",
    },
    "bold": {
        "font_size": 56,
        "bold": True,
        "border_style": 3,
        "outline": 3,
        "shadow": 0,
        "back_color": "&HA0000000",
    },
    "minimal": {
        "font_size": 42,
        "bold": False,
        "border_style": 1,
        "outline": 1,
        "shadow": 1,
        "back_color": "&H60000000",
    },
}

TRANSITION_DURATION = 0.5
ZOOM_SPEED = 0.0004
ZOOM_MAX = 1.08

MUSIC_VOLUME = 0.25
VOICEOVER_VOLUME = 1.0
FADE_DURATION = 1.5

TEMP_DIR = BASE_DIR / "temp"
OUTPUT_DIR = BASE_DIR / "output"
UPLOAD_DIR = BASE_DIR / "uploads"
FONT_PATH = BASE_DIR / "assets" / "fonts"

TEMP_DIR.mkdir(exist_ok=True)
OUTPUT_DIR.mkdir(exist_ok=True)
UPLOAD_DIR.mkdir(exist_ok=True)
