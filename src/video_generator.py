"""ショート動画生成の中心ロジック (シーンベース)."""
from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path

import numpy as np
from moviepy import (
    AudioFileClip,
    ColorClip,
    CompositeVideoClip,
    ImageClip,
    concatenate_videoclips,
)
from PIL import Image, ImageDraw, ImageFont

from .config import ASSETS_DIR, DEFAULT_CONFIG, OUTPUT_DIR, VideoConfig


@dataclass
class Scene:
    """動画を構成する 1 シーンの情報."""

    duration: float
    image: str | None = None
    caption: str | None = None

    @classmethod
    def from_dict(cls, data: dict) -> "Scene":
        return cls(
            duration=float(data["duration"]),
            image=data.get("image"),
            caption=data.get("caption"),
        )


@dataclass
class VideoScript:
    """JSON で記述された動画構成."""

    title: str
    scenes: list[Scene]
    bgm: str | None = None

    @classmethod
    def load(cls, path: Path) -> "VideoScript":
        data = json.loads(Path(path).read_text(encoding="utf-8"))
        return cls(
            title=data["title"],
            scenes=[Scene.from_dict(s) for s in data["scenes"]],
            bgm=data.get("bgm"),
        )


def _load_font(size: int) -> ImageFont.FreeTypeFont:
    """システムにある標準フォントをロードする."""
    candidates = [
        "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf",
        "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
        "/System/Library/Fonts/Helvetica.ttc",
    ]
    for path in candidates:
        if Path(path).exists():
            return ImageFont.truetype(path, size)
    return ImageFont.load_default()


def _render_caption_overlay(
    caption: str, width: int, height: int, font_size: int
) -> np.ndarray:
    """キャプションを透明背景の画像として PIL で描画する."""
    img = Image.new("RGBA", (width, height), (0, 0, 0, 0))
    draw = ImageDraw.Draw(img)
    font = _load_font(font_size)

    lines = caption.split("\n")
    line_heights = []
    line_widths = []
    for line in lines:
        bbox = draw.textbbox((0, 0), line, font=font)
        line_widths.append(bbox[2] - bbox[0])
        line_heights.append(bbox[3] - bbox[1])
    total_h = sum(line_heights) + (len(lines) - 1) * 10
    y = int(height * 0.78) - total_h // 2
    for line, lw, lh in zip(lines, line_widths, line_heights):
        x = (width - lw) // 2
        # 軽い縁取り
        for dx, dy in [(-2, 0), (2, 0), (0, -2), (0, 2)]:
            draw.text((x + dx, y + dy), line, font=font, fill=(0, 0, 0, 255))
        draw.text((x, y), line, font=font, fill=(255, 255, 255, 255))
        y += lh + 10
    return np.array(img)


class ShortVideoGenerator:
    """JSON スクリプトから縦型ショート動画を生成する."""

    def __init__(self, config: VideoConfig = DEFAULT_CONFIG) -> None:
        self.config = config

    def build_scene_clip(self, scene: Scene):
        cfg = self.config
        size = (cfg.width, cfg.height)

        if scene.image:
            image_path = ASSETS_DIR / "images" / scene.image
            pil_img = Image.open(image_path).convert("RGB")
            pil_img.thumbnail((cfg.width, cfg.height), Image.LANCZOS)
            canvas = Image.new("RGB", size, cfg.bg_color)
            offset = (
                (cfg.width - pil_img.width) // 2,
                (cfg.height - pil_img.height) // 2,
            )
            canvas.paste(pil_img, offset)
            clip = ImageClip(np.array(canvas)).with_duration(scene.duration)
        else:
            clip = ColorClip(
                size=size, color=cfg.bg_color, duration=scene.duration
            )

        if scene.caption:
            overlay = _render_caption_overlay(
                scene.caption, cfg.width, cfg.height, cfg.font_size
            )
            text_clip = ImageClip(overlay).with_duration(scene.duration)
            clip = CompositeVideoClip([clip, text_clip], size=size)

        return clip

    def generate(self, script: VideoScript, output_path: Path) -> Path:
        clips = [self.build_scene_clip(scene) for scene in script.scenes]
        video = concatenate_videoclips(clips, method="compose")

        if script.bgm:
            bgm_path = ASSETS_DIR / "audio" / script.bgm
            audio = AudioFileClip(str(bgm_path)).subclipped(0, video.duration)
            video = video.with_audio(audio)

        output_path.parent.mkdir(parents=True, exist_ok=True)
        video.write_videofile(
            str(output_path),
            fps=self.config.fps,
            codec=self.config.codec,
        )
        return output_path


def generate_from_script(script_path: Path, output_name: str | None = None) -> Path:
    script = VideoScript.load(script_path)
    output_file = OUTPUT_DIR / (output_name or f"{script.title}.mp4")
    return ShortVideoGenerator().generate(script, output_file)
