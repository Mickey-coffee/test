"""ショート動画生成の共通設定."""
from dataclasses import dataclass
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parent.parent
ASSETS_DIR = PROJECT_ROOT / "assets"
OUTPUT_DIR = PROJECT_ROOT / "output"


@dataclass(frozen=True)
class VideoConfig:
    """出力動画のフォーマット設定."""

    width: int = 1080
    height: int = 1920
    fps: int = 30
    codec: str = "libx264"
    audio_codec: str = "aac"
    font: str = "DejaVu-Sans-Bold"
    font_size: int = 72
    text_color: str = "white"
    bg_color: tuple[int, int, int] = (0, 0, 0)


DEFAULT_CONFIG = VideoConfig()
