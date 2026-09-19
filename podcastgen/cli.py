"""pg CLI: 台本 → radio.mp3 → 視聴ページ。"""

import argparse
import json
import os
from pathlib import Path

from podcastgen.radio import generate_podcast
from podcastgen.site import build_site

DESIGN_HOME = Path(os.environ.get("SG_DESIGN_HOME", Path.home() / "repo" / "show-builder"))
THEMES_DIR = DESIGN_HOME / "themes"


def load_theme(slug: str) -> tuple[dict, Path]:
    path = THEMES_DIR / f"{slug}.json"
    if not path.exists():
        raise FileNotFoundError(f"theme not found: {path}")
    data = json.loads(path.read_text(encoding="utf-8"))
    return data, THEMES_DIR.parent


def cmd_list(_args) -> None:
    for p in sorted(THEMES_DIR.glob("*.json")):
        data = json.loads(p.read_text(encoding="utf-8"))
        print(f"{p.stem:20s} {data.get('brand', '')}")


def cmd_generate(args) -> None:
    theme, base = load_theme(args.theme)
    bgm = Path(args.bgm).expanduser() if args.bgm else None
    se = Path(args.se).expanduser() if args.se else None
    out = generate_podcast(theme, base, bgm=bgm, se=se)
    print(json.dumps({"audio": str(out)}, ensure_ascii=False))


def cmd_site(args) -> None:
    theme, base = load_theme(args.theme)
    out_site = Path(args.out).expanduser() if args.out else base / "site"
    mp3 = Path(args.mp3).expanduser() if args.mp3 else None
    build_site(theme, base, out_site, mp3=mp3)


def main() -> None:
    p = argparse.ArgumentParser(prog="pg")
    sub = p.add_subparsers(dest="command")

    sub.add_parser("list", help="利用可能なテーマ一覧 (design repo)")

    sp = sub.add_parser("generate", help="台本 → radio.mp3 を生成")
    sp.add_argument("--theme", required=True, help="themes/<slug>.json")
    sp.add_argument("--bgm", default=None, help="BGM wav (ループ・音量0.3)")
    sp.add_argument("--se", default=None, help="SE wav")

    sp = sub.add_parser("site", help="radio.mp3 → 視聴ページを生成")
    sp.add_argument("--theme", required=True, help="themes/<slug>.json")
    sp.add_argument("--out", default=None, help="出力 site ディレクトリ")
    sp.add_argument("--mp3", default=None, help="既存 radio.mp3 を指定")

    args = p.parse_args()
    if args.command == "list":
        cmd_list(args)
    elif args.command == "generate":
        cmd_generate(args)
    elif args.command == "site":
        cmd_site(args)
    else:
        p.print_help()


if __name__ == "__main__":
    main()