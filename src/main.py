"""CLI エントリーポイント."""
from __future__ import annotations

import argparse
from pathlib import Path

from .video_generator import generate_from_script


def main() -> None:
    parser = argparse.ArgumentParser(description="JSON からショート動画を生成する")
    parser.add_argument("script", type=Path, help="動画構成 JSON ファイルへのパス")
    parser.add_argument("-o", "--output", help="出力ファイル名 (任意)")
    args = parser.parse_args()

    output = generate_from_script(args.script, args.output)
    print(f"Generated: {output}")


if __name__ == "__main__":
    main()
