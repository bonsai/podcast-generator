# podcast-generator

台本(md) → **radio.mp3** → **視聴ページ(index.html + episodes.json)** を生成する。
**video なし**の「ポッドキャスト的ラジオ」専用 repo。

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

# ラジオ生成（BGM/SE は任意）
SAKURA_API_KEY=... python -m podcastgen.cli generate --theme idol-playlist
SAKURA_API_KEY=... python -m podcastgen.cli generate --theme idol-playlist --bgm out/bgm.wav

# 視聴ページ生成 → GitHub Pages 等に置く
python -m podcastgen.cli site --theme idol-playlist --out ~/repo/show-builder/site
```

## GitHub Actions で「ブラウザ指示 → mp3 ラジオ視聴」

- `workflow_dispatch`（Actions タブの Run workflow ボタン）でテーマを選んで実行
- `schedule` (cron) で定期自動生成
- Actions が `generate` → `site` を実行し、`gh-pages` ブランチで公開 → ブラウザで `<audio>` 再生
- YouTube アップロード不要（OAuth 待ちでも mp3 ラジオ視聴は成立）

## 環境変数

| 変数 | デフォルト | 説明 |
| --- | --- | --- |
| `SAKURA_API_KEY` | (必須) | さくらのAI Engine key |
| `VOICEVOX_API_URL` | `https://api.ai.sakura.ad.jp/v1/audio/speech` | TTS API |
| `VOICEVOX_MODEL` | `zundamon` | 音声モデル |
| `VOICEVOX_VOICE` | `normal` | 話者 |
| `VOICEVOX_MAX_CHARS` | `800` | 1リクエスト文字数 |

## 設計 root

テーマ・台本・データ・music-json スキーマは **design repo**（`~/repo/show-builder`）がソース・オブ・トゥルース。