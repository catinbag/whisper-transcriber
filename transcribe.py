import argparse
import sys
from pathlib import Path

from src import pipeline


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Local audio and video transcription via whisper.cpp"
    )
    parser.add_argument("video", type=Path, help="Path to the video file")
    args = parser.parse_args()

    try:
        pipeline.run(args.video)
    except Exception as exc:
        print(f"Error: {exc}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
