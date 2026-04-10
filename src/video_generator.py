"""ショート動画生成の中心ロジック."""
from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path

from moviepy.editor import (
    AudioFileClip,
    ColorClip,
    CompositeVideoClip,
    ImageClip,
    TextClip,
    concatenate_videoclips,
)

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


class ShortVideoGenerator:
    """JSON スクリプトから縦型ショート動画を生成する."""

    def __init__(self, config: VideoConfig = DEFAULT_CONFIG) -> None:
        self.config = config

    def build_scene_clip(self, scene: Scene):
        cfg = self.config
        size = (cfg.width, cfg.height)

        if scene.image:
            image_path = ASSETS_DIR / "images" / scene.image
            clip = (
                ImageClip(str(image_path))
                .set_duration(scene.duration)
                .resize(height=cfg.height)
                .on_color(size=size, color=cfg.bg_color, pos=("center", "center"))
            )
        else:
            clip = ColorClip(size=size, color=cfg.bg_color, duration=scene.duration)

        if scene.caption:
            text = TextClip(
                scene.caption,
                fontsize=cfg.font_size,
                color=cfg.text_color,
                font=cfg.font,
                method="caption",
                size=(cfg.width - 120, None),
                align="center",
            ).set_duration(scene.duration).set_position(("center", cfg.height * 0.78))
            clip = CompositeVideoClip([clip, text], size=size)

        return clip

    def generate(self, script: VideoScript, output_path: Path) -> Path:
        clips = [self.build_scene_clip(scene) for scene in script.scenes]
        video = concatenate_videoclips(clips, method="compose")

        if script.bgm:
            bgm_path = ASSETS_DIR / "audio" / script.bgm
            audio = AudioFileClip(str(bgm_path)).subclip(0, video.duration)
            video = video.set_audio(audio)

        output_path.parent.mkdir(parents=True, exist_ok=True)
        video.write_videofile(
            str(output_path),
            fps=self.config.fps,
            codec=self.config.codec,
            audio_codec=self.config.audio_codec,
        )
        return output_path


def generate_from_script(script_path: Path, output_name: str | None = None) -> Path:
    script = VideoScript.load(script_path)
    output_file = OUTPUT_DIR / (output_name or f"{script.title}.mp4")
    return ShortVideoGenerator().generate(script, output_file)
