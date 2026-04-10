# Short Video Generator

テキスト・画像・音声からショート動画(縦型 1080x1920)を自動生成するPythonプロジェクトです。

## 特徴

- 縦型 (9:16) ショート動画フォーマット対応
- 画像スライドショーにテキストキャプションと BGM を重ねて出力
- JSON で動画構成を宣言的に記述
- MoviePy をベースに実装

## セットアップ

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

`ffmpeg` がシステムにインストールされている必要があります。

## 使い方

```bash
python -m src.main scripts/sample_script.json
```

生成された動画は `output/` ディレクトリに保存されます。

## スクリプトフォーマット

`scripts/sample_script.json` を参照してください。各シーンに画像、キャプション、表示時間を指定できます。

## ディレクトリ構成

```
.
├── assets/         # 画像・音声素材
├── output/         # 生成された動画
├── scripts/        # 動画構成 JSON
└── src/            # ソースコード
```
