"""podcast-generator: 台本 → radio.mp3 + 視聴ページ(HTML) を生成する。

design repo（ソース・オブ・トゥルース）の theme json + 台本 md を読み、
さくらのAI Engine (VOICEVOX音声モデル) で TTS し、BGM/SE をミックスして
mp3 にまとめ、ブラウザで聴ける視聴ページを出力する。

video-generator との違い: 動画(motion)や YouTube 投稿は持たない。
"""
from pathlib import Path
import json
import os
import re
import shutil
import subprocess
import tempfile
import urllib.error
import urllib.request
import wave

TTS_URL = os.environ.get(
    "VOICEVOX_API_URL", "https://api.ai.sakura.ad.jp/v1/audio/speech"
)
TTS_MODEL = os.environ.get("VOICEVOX_MODEL", "zundamon")
TTS_VOICE = os.environ.get("VOICEVOX_VOICE", "normal")
TTS_MAX_CHARS = int(os.environ.get("VOICEVOX_MAX_CHARS", "800"))


# ---------- script → text ----------

def script_to_text(path: Path) -> str:
    lines = []
    for raw in path.read_text(encoding="utf-8").splitlines():
        line = raw.strip()
        if not line or line.startswith("#") or line.startswith("##"):
            continue
        line = re.sub(r"[*_]", "", line)
        line = re.sub(r"^[-–—]\s*", "", line)
        if line.startswith("「") and line.endswith("」"):
            line = line[1:-1]
        lines.append(line)
    return "\n".join(lines)


def split_text(text: str, max_length: int = TTS_MAX_CHARS) -> list[str]:
    parts = [p for p in re.split(r"(?<=[。！？\n])", text) if p.strip()]
    chunks: list[str] = []
    current = ""
    for part in parts:
        if len(current) + len(part) <= max_length:
            current += part
        else:
            if current:
                chunks.append(current)
            current = part
    if current:
        chunks.append(current)
    return chunks


# ---------- TTS (Sakura/VOICEVOX) ----------

def synthesize(text: str) -> bytes:
    api_key = os.environ.get("SAKURA_API_KEY")
    if not api_key:
        raise RuntimeError("SAKURA_API_KEY is not set")
    payload = json.dumps(
        {
            "model": TTS_MODEL,
            "input": text,
            "voice": TTS_VOICE,
            "response_format": "wav",
        },
        ensure_ascii=False,
    ).encode("utf-8")
    req = urllib.request.Request(
        TTS_URL,
        data=payload,
        headers={
            "Accept": "audio/wav",
            "Content-Type": "application/json; charset=utf-8",
            "Authorization": f"Bearer {api_key}",
        },
        method="POST",
    )
    with urllib.request.urlopen(req, timeout=120) as res:
        return res.read()


def concatenate_wav(chunks: list[bytes], output: Path) -> None:
    with wave.open(str(output), "wb") as out_wav:
        for i, data in enumerate(chunks):
            with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as tf:
                tf.write(data)
                tmp = tf.name
            try:
                with wave.open(tmp, "rb") as in_wav:
                    if i == 0:
                        out_wav.setparams(in_wav.getparams())
                    out_wav.writeframes(in_wav.readframes(in_wav.getnframes()))
            finally:
                os.remove(tmp)


# ---------- ffmpeg mix ----------

def mix_audio(narration: Path, output: Path,
              bgm: Path | None = None, se: Path | None = None) -> Path:
    """ナレーションに BGM/SE を指定があればミックス。BGM はループ。"""
    output.parent.mkdir(parents=True, exist_ok=True)
    args = ["ffmpeg", "-y"]
    if bgm and bgm.exists():
        args += ["-stream_loop", "-1", "-i", str(bgm)]
    if se and se.exists():
        args += ["-i", str(se)]
    args += ["-i", str(narration)]
    filters = []
    inputs = 1
    if bgm and bgm.exists():
        filters.append(
            f"[0:a]volume=0.3,apad=pad_dur=5[bgm]"
        )
        filters.append(f"[bgm][{inputs}:a]amix=inputs=2:duration=first[a]")
        inputs += 1
    elif se and se.exists():
        filters.append(f"[0:a][{inputs}:a]amix=inputs=2:duration=first[a]")
    else:
        filters.append(f"[0:a]anull[a]")
    args += ["-filter_complex", ";".join(filters), "-map", "[a]"]
    args += ["-c:a", "libmp3lame", "-b:a", "128k", str(output)]
    subprocess.run(args, check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    return output


# ---------- generate ----------

def generate_podcast(theme: dict, theme_dir: Path,
                     bgm: Path | None = None, se: Path | None = None) -> Path:
    """theme json (design repo) から radio.mp3 を生成して返す。"""
    script = theme_dir / theme.get("script", "data/programs/test/talk-script-60s.md")
    if not script.exists():
        raise FileNotFoundError(f"talk script not found: {script}")
    audio_dir = theme_dir / theme.get("audio_dir", "data/audio")
    audio_dir.mkdir(parents=True, exist_ok=True)
    output_audio = audio_dir / theme.get("audio_name", "radio.mp3")

    text = script_to_text(script)
    chunks = split_text(text)
    wavs = [synthesize(c) for c in chunks]

    with tempfile.TemporaryDirectory() as tmp:
        merged = Path(tmp) / "merged.wav"
        concatenate_wav(wavs, merged)
        narration = Path(tmp) / "narration.wav"
        subprocess.run(
            ["ffmpeg", "-y", "-i", str(merged), "-c:a", "pcm_s16le", str(narration)],
            check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
        )
        mix_audio(narration, output_audio, bgm=bgm, se=se)
    return output_audio