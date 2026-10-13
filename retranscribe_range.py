import argparse
import sys

from src import config, repair


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Re-transcribes only the given range of a video "
        "(fixes hallucinations without re-running the whole file)."
    )
    parser.add_argument("slug", help="Recording name: input/<slug>.mp4")
    parser.add_argument("start", help="Range start, HH:MM:SS")
    parser.add_argument("end", help="Range end, HH:MM:SS")
    parser.add_argument("--beam-size", type=int, default=config.BEAM_SIZE)
    parser.add_argument(
        "--max-context",
        type=int,
        default=None,
        help="Disable text context carry-over between segments (0) "
        "if the model loops on a repeated phrase",
    )
    args = parser.parse_args()

    try:
        result = repair.retranscribe_range(
            args.slug, args.start, args.end, args.beam_size, args.max_context
        )
    except Exception as exc:
        print(f"Error: {exc}", file=sys.stderr)
        sys.exit(1)

    print(f"\nReady for review: {result.output_prefix}.srt / {result.output_prefix}.txt")
    print(
        f"To splice: python3 splice.py {args.slug} {result.output_prefix}.srt "
        f"--offset {result.start_s} --end {result.end_s}"
    )


if __name__ == "__main__":
    main()
