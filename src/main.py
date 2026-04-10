"""CLI エントリーポイント."""
from __future__ import annotations

import argparse
from pathlib import Path

from .ranking_video import generate_ranking_video
from .video_generator import generate_from_script


def main() -> None:
    parser = argparse.ArgumentParser(description="JSON からショート動画を生成する")
    subparsers = parser.add_subparsers(dest="command", required=True)

    scene_parser = subparsers.add_parser(
        "scene", help="シーンベースの動画を生成する"
    )
    scene_parser.add_argument(
        "script", type=Path, help="動画構成 JSON ファイルへのパス"
    )
    scene_parser.add_argument("-o", "--output", help="出力ファイル名 (任意)")

    ranking_parser = subparsers.add_parser(
        "ranking", help="大学ランキング推移動画を生成する"
    )
    ranking_parser.add_argument(
        "data", type=Path, help="ランキングデータ JSON ファイルへのパス"
    )
    ranking_parser.add_argument("-o", "--output", help="出力ファイル名 (任意)")

    args = parser.parse_args()

    if args.command == "scene":
        output = generate_from_script(args.script, args.output)
    elif args.command == "ranking":
        output = generate_ranking_video(args.data, args.output)
    else:
        parser.error(f"unknown command: {args.command}")
        return

    print(f"Generated: {output}")


if __name__ == "__main__":
    main()
