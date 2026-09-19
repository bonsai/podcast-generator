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

# ラジオ生成（BGM/SE は任意、TTS オプション付き）
SAKURA_API_KEY=... python -m podcastgen.cli generate --theme idol-playlist
SAKURA_API_KEY=... python -m podcastgen.cli generate --theme idol-playlist --bgm out/bgm.wav \
  --speed 1.2 --pitch 0.05 --intonation-scale 1.1 --volume-scale 1.2 --pause-sentence 300

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

## TTS オプション（--speed / --pitch / --intonation-scale / --volume-scale / --pause-sentence）

| オプション | 意味 | 例 |
| --- | --- | --- |
| `--speed` | 話速 | `1.2` = 速め |
| `--pitch` | ピッチ | `0.1` |
| `--intonation-scale` | 抑揚 | `1.1` |
| `--volume-scale` | 音量 | `1.2` |
| `--pause-sentence` | 文間ポーズ(ms) | `300` |

対応する環境変数（`VOICEVOX_SPEED`, `VOICEVOX_PITCH`, `VOICEVOX_INTONATION_SCALE`, `VOICEVOX_VOLUME_SCALE`, `VOICEVOX_PAUSE_SENTENCE`）でも指定可能です。

## 設計 root

テーマ・台本・データ・music-json スキーマは **design repo**（`~/repo/show-builder`）がソース・オブ・トゥルース。