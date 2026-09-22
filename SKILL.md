---
name: podcast-generator
description: >
  台本(md)からラジオ音声(radio.mp3)と視聴ページ(index.html + episodes.json)を生成する
  ポッドキャスト生成パイプライン。さくらTTS → wav連結 → BGM/SEミックス → mp3、
  GitHub Actions の workflow_dispatch / schedule で自動生成・gh-pages公開。
  「podcast」「ラジオ」「台本」「mp3生成」「TTS音声」「視聴ページ」
  「podcast generate」「ラジオ生成」「podcast site」などのキーワードで発動。
  CLI: `python -m podcastgen.cli {list|generate|site}`
---

# podcast-generator — 台本 → ラジオmp3 + 視聴ページ

## パイプライン

```
design repo (theme json + 台本 md)
  └─ podcast-generator
       ├─ generate : さくらTTS → wav連結 → BGM/SEミックス → radio.mp3
       └─ site     : radio.mp3 → index.html + episodes.json（ブラウザ視聴）
```

## 使い方

```bash
# テーマ一覧（design repo の themes/）
python -m podcastgen.cli list

# ラジオ生成（BGM/SE は任意、TTS オプション付き）
SAKURA_API_KEY=... python -m podcastgen.cli generate --theme idol-playlist
SAKURA_API_KEY=... python -m podcastgen.cli generate --theme idol-playlist \
  --bgm out/bgm.wav --speed 1.2 --pitch 0.05

# 視聴ページ生成 → GitHub Pages 等に置く
python -m podcastgen.cli site --theme idol-playlist --out ~/repo/show-builder/site
```

## GitHub Actions

- `workflow_dispatch`（Actions タブの Run workflow）でテーマを選んで実行
- `schedule` (cron) で定期自動生成
- inputs: `theme` / `bgm`（default: `data/audio/lofi_bgm.mp3`）/ `se` / `speed` / `pitch` / `intonation-scale` / `volume-scale` / `pause-sentence`
- `generate` → `site` → `gh-pages` ブランチ公開 → ブラウザで `<audio>` 再生

## 環境変数

| 変数 | デフォルト | 説明 |
| --- | --- | --- |
| `VOICEVOX_API_URL` | `https://api.ai.sakura.ad.jp/v1/audio/speech` | TTS API |
| `VOICEVOX_MODEL` | `zundamon` | 音声モデル |
| `VOICEVOX_VOICE` | `normal` | 話者 |
| `VOICEVOX_MAX_CHARS` | `800` | 1リクエスト文字数 |
| `VOICEVOX_SPEED` 等 | — | TTSオプション（--speed 等と同一） |

## 設計 root

テーマ・台本・データ・music-json スキーマは **design repo**（`~/repo/show-builder`）がソース・オブ・トゥルース。
