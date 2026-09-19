"""podcast-generator: 視聴ページ (HTML5 audio + エピソード JSON) を生成する。

生成した radio.mp3 とメタデータから、ブラウザだけで聴ける静的ページを
出力する。GitHub Pages などに置けば mp3 ラジオ視聴が成立する。
"""
from pathlib import Path
import json
import shutil
from datetime import datetime, timezone


def _duration_of(mp3: Path) -> int:
    """ffprobe で秒数を得る。無ければ 0。"""
    import subprocess
    try:
        out = subprocess.run(
            ["ffprobe", "-v", "error", "-show_entries", "format=duration",
             "-of", "csv=p=0", str(mp3)],
            capture_output=True, text=True, check=True,
        )
        return int(float(out.stdout.strip()))
    except (subprocess.CalledProcessError, ValueError):
        return 0


def build_site(theme: dict, theme_dir: Path, out_site: Path,
               mp3: Path | None = None) -> Path:
    """テーマの radio.mp3 を site ディレクトリにコピーし視聴ページを作る。"""
    import shutil

    out_site.mkdir(parents=True, exist_ok=True)
    brand = theme.get("brand", "radio")
    subtitle = theme.get("subtitle", "")

    # audio 本体をコピー
    audio_name = theme.get("audio_name", "radio.mp3")
    if mp3 is None:
        mp3 = theme_dir / theme.get("audio_dir", "data/audio") / audio_name
    audio_dst = out_site / "audio" / audio_name
    audio_dst.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(mp3, audio_dst)
    duration = _duration_of(audio_dst)

    # エピソード JSON
    episodes_path = out_site / "episodes.json"
    episodes = []
    if episodes_path.exists():
        episodes = json.loads(episodes_path.read_text(encoding="utf-8"))
    episodes.append({
        "title": f"{brand} {subtitle}",
        "file": f"audio/{audio_name}",
        "duration": duration,
        "published": datetime.now(timezone.utc).isoformat(),
    })
    episodes_path.write_text(
        json.dumps(episodes, ensure_ascii=False, indent=2), encoding="utf-8"
    )

    # 最新エピソード（先頭）で audio 再生
    ep = episodes[-1]
    html = f"""<!doctype html>
<html lang="ja"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>{ep['title']}</title>
<style>
body {{ font-family: sans-serif; max-width: 640px; margin: 40px auto; padding: 0 16px; background: #10121c; color: #eee; }}
h1 {{ font-size: 1.5rem }}
.ep {{ border: 1px solid #333; border-radius: 8px; padding: 12px 16px; margin: 8px 0; }}
audio {{ width: 100% }}
</style></head><body>
<h1>{ep['title']}</h1>
<p>{ep['duration']} sec</p>
<audio controls preload="none">
  <source src="{ep['file']}" type="audio/mpeg">
</audio>
<h2>過去のエピソード</h2>
{''.join(f'<div class="ep"><a href="#{i}">{e["title"]}</a> · {e.get("duration", 0)}s</div>' for i, e in enumerate(episodes))}
</body></html>
"""
    (out_site / "index.html").write_text(html, encoding="utf-8")
    return out_site