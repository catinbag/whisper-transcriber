import argparse
import sys
from pathlib import Path

from src import config, srt_tools


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Builds a compact digest of a transcript: one line per segment, "
        "'HH:MM:SS text'."
    )
    parser.add_argument("slug", help="Recording name: output/<slug>/<slug>.srt")
    parser.add_argument(
        "-o",
        "--output",
        type=Path,
        default=None,
        help="Output file (default: output/<slug>/<slug>.digest.txt)",
    )
    args = parser.parse_args()

    out_dir = config.OUTPUT_DIR / args.slug
    srt_path = out_dir / f"{args.slug}.srt"
    if not srt_path.exists():
        print(f"Error: not found: {srt_path}", file=sys.stderr)
        sys.exit(1)

    digest_path = args.output or out_dir / f"{args.slug}.digest.txt"
    segments = srt_tools.parse_srt(srt_path)
    digest_path.write_text(srt_tools.format_digest(segments), encoding="utf-8")

    print(f"Done. {len(segments)} segments -> {digest_path}")


if __name__ == "__main__":
    main()
