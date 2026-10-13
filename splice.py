import argparse
import sys
from pathlib import Path

from src import repair


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Splices a re-transcribed range (from retranscribe_range.py) "
        "into the main transcript, replacing the damaged section."
    )
    parser.add_argument("slug", help="Recording name: output/<slug>/")
    parser.add_argument("range_srt", type=Path, help="SRT of the new range")
    parser.add_argument("--offset", type=float, required=True, help="Range start in seconds")
    parser.add_argument(
        "--end",
        type=float,
        default=None,
        help="End of the replaced range in seconds (if omitted, everything up to the end of the file is replaced)",
    )
    args = parser.parse_args()

    try:
        count, backup_dir = repair.splice_range(args.slug, args.range_srt, args.offset, args.end)
    except Exception as exc:
        print(f"Error: {exc}", file=sys.stderr)
        sys.exit(1)

    print(f"Done. Replaced with {count} segments (old content: see backup).")
    print(f"Backups of the old files: {backup_dir}")


if __name__ == "__main__":
    main()
