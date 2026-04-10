"""大学ランキング推移のショート動画を生成するモジュール.

年ごとのランキングを水平棒グラフとしてレンダリングし、
縦型 (1080x1920) のショート動画に結合する。
"""
from __future__ import annotations

import io
import json
from dataclasses import dataclass
from pathlib import Path

import matplotlib

matplotlib.use("Agg")

import matplotlib.pyplot as plt  # noqa: E402
import numpy as np  # noqa: E402
from matplotlib import cm  # noqa: E402
from moviepy import ImageClip, concatenate_videoclips  # noqa: E402
from PIL import Image  # noqa: E402

from .config import DEFAULT_CONFIG, OUTPUT_DIR, VideoConfig


@dataclass
class RankingEntry:
    rank: int
    name: str


@dataclass
class YearRanking:
    year: int
    rankings: list[RankingEntry]

    @classmethod
    def from_dict(cls, data: dict) -> "YearRanking":
        return cls(
            year=int(data["year"]),
            rankings=[RankingEntry(**r) for r in data["rankings"]],
        )


@dataclass
class RankingScript:
    title: str
    subtitle: str | None
    duration_per_year: float
    years: list[YearRanking]

    @classmethod
    def load(cls, path: Path) -> "RankingScript":
        data = json.loads(Path(path).read_text(encoding="utf-8"))
        return cls(
            title=data["title"],
            subtitle=data.get("subtitle"),
            duration_per_year=float(data.get("duration_per_year", 2.5)),
            years=[YearRanking.from_dict(y) for y in data["years"]],
        )


class RankingFrameRenderer:
    """1 年分のランキングを 1 フレーム画像としてレンダリングする."""

    def __init__(self, config: VideoConfig = DEFAULT_CONFIG) -> None:
        self.config = config

    def render(
        self,
        year_ranking: YearRanking,
        title: str,
        subtitle: str | None,
        top_n: int = 10,
    ) -> np.ndarray:
        cfg = self.config
        dpi = 100
        fig_w = cfg.width / dpi
        fig_h = cfg.height / dpi

        fig = plt.figure(figsize=(fig_w, fig_h), dpi=dpi)
        fig.patch.set_facecolor("#0a0a1a")

        # タイトル領域
        fig.text(
            0.5,
            0.95,
            title,
            ha="center",
            va="top",
            color="white",
            fontsize=28,
            fontweight="bold",
        )
        if subtitle:
            fig.text(
                0.5,
                0.915,
                subtitle,
                ha="center",
                va="top",
                color="#8a8aa8",
                fontsize=18,
            )

        # 年表示 (大きく目立たせる)
        fig.text(
            0.5,
            0.86,
            str(year_ranking.year),
            ha="center",
            va="top",
            color="#ffcc33",
            fontsize=96,
            fontweight="bold",
        )

        ax = fig.add_axes([0.08, 0.05, 0.88, 0.70])
        ax.set_facecolor("#0a0a1a")

        sorted_entries = sorted(year_ranking.rankings, key=lambda e: e.rank)[:top_n]
        # 1 位を上に表示するため逆順にする
        display = list(reversed(sorted_entries))
        names = [e.name for e in display]
        # rank=1 が最長になるようスコア化
        scores = [top_n - e.rank + 1 for e in display]

        colors = cm.viridis(np.linspace(0.25, 0.9, len(display)))
        bars = ax.barh(names, scores, color=colors, edgecolor="none", height=0.72)

        for bar, entry in zip(bars, display):
            width = bar.get_width()
            y = bar.get_y() + bar.get_height() / 2
            ax.text(
                width - 0.25,
                y,
                f"#{entry.rank}",
                ha="right",
                va="center",
                color="white",
                fontsize=22,
                fontweight="bold",
            )
            ax.text(
                0.15,
                y,
                entry.name,
                ha="left",
                va="center",
                color="white",
                fontsize=26,
                fontweight="bold",
            )

        ax.set_xlim(0, top_n + 0.5)
        ax.set_xticks([])
        ax.set_yticks([])
        for spine in ax.spines.values():
            spine.set_visible(False)

        fig.text(
            0.5,
            0.02,
            "Illustrative sample data",
            ha="center",
            va="bottom",
            color="#666680",
            fontsize=14,
            style="italic",
        )

        buf = io.BytesIO()
        fig.savefig(buf, format="png", facecolor=fig.get_facecolor())
        plt.close(fig)
        buf.seek(0)

        img = np.array(Image.open(buf).convert("RGB"))
        # サイズが多少ずれることがあるので確実に合わせる
        if img.shape[:2] != (cfg.height, cfg.width):
            img = np.array(
                Image.fromarray(img).resize((cfg.width, cfg.height), Image.LANCZOS)
            )
        return img


class RankingVideoGenerator:
    def __init__(self, config: VideoConfig = DEFAULT_CONFIG) -> None:
        self.config = config
        self.renderer = RankingFrameRenderer(config)

    def generate(self, script: RankingScript, output_path: Path) -> Path:
        clips = []
        for year_ranking in script.years:
            frame = self.renderer.render(
                year_ranking, script.title, script.subtitle
            )
            clip = ImageClip(frame).with_duration(script.duration_per_year)
            clips.append(clip)

        video = concatenate_videoclips(clips, method="compose")
        output_path.parent.mkdir(parents=True, exist_ok=True)
        video.write_videofile(
            str(output_path),
            fps=self.config.fps,
            codec=self.config.codec,
        )
        return output_path


def generate_ranking_video(
    data_path: Path, output_name: str | None = None
) -> Path:
    script = RankingScript.load(data_path)
    safe_name = output_name or "university_rankings.mp4"
    output_file = OUTPUT_DIR / safe_name
    return RankingVideoGenerator().generate(script, output_file)
