import shutil
from dataclasses import dataclass
from pathlib import Path

from . import audio, config, srt_tools, whisper_runner


@dataclass
class RangeResult:
    output_prefix: Path
    start_s: float
    end_s: float


def hhmmss_to_seconds(value: str) -> float:
    h, m, s = value.split(":")
    return int(h) * 3600 + int(m) * 60 + float(s)


def retranscribe_range(
    slug: str,
    start: str,
    end: str,
    beam_size: int = config.BEAM_SIZE,
    max_context: int | None = None,
) -> RangeResult:
    """Re-transcribes only [start, end] (HH:MM:SS) of input/<slug>.mp4, in isolation.

    The result goes to tmp/<slug>_range_<start>_<end>.{srt,txt}; the main transcript is untouched.
    """
    video_path = config.INPUT_DIR / f"{slug}.mp4"
    if not video_path.exists():
        raise FileNotFoundError(f"video not found: {video_path}")

    start_s = hhmmss_to_seconds(start)
    end_s = hhmmss_to_seconds(end)
    duration_s = end_s - start_s
    if duration_s <= 0:
        raise ValueError("range end must be after range start")

    tmp_dir = config.PROJECT_ROOT / "tmp"
    range_tag = f"{start.replace(':', '-')}_{end.replace(':', '-')}"
    wav_path = tmp_dir / f"{slug}_range_{range_tag}.wav"
    output_prefix = tmp_dir / f"{slug}_range_{range_tag}"

    print(f"[1/2] Extracting range {start}-{end} from {video_path.name}...")
    audio.extract_wav(video_path, wav_path, start_s=start_s, duration_s=duration_s)

    print("[2/2] Transcribing the isolated range (without context of the whole recording)...")
    whisper_runner.transcribe(
        wav_path,
        output_prefix,
        beam_size=beam_size,
        max_context=max_context,
        formats=("txt", "srt"),
    )
    return RangeResult(output_prefix, start_s, end_s)


def splice_range(slug: str, range_srt: Path, offset_s: float, end_s: float | None) -> tuple[int, Path]:
    """Replaces [offset_s, end_s) of output/<slug>/ transcripts with the segments of range_srt.

    Backs up the old .srt/.vtt/.txt to pre-splice-backup/ first.
    Returns (number of inserted segments, backup dir).
    """
    out_dir = config.OUTPUT_DIR / slug
    srt_path = out_dir / f"{slug}.srt"
    vtt_path = out_dir / f"{slug}.vtt"
    txt_path = out_dir / f"{slug}.txt"

    if not srt_path.exists():
        raise FileNotFoundError(f"not found: {srt_path}")
    if not range_srt.exists():
        raise FileNotFoundError(f"not found: {range_srt}")

    backup_dir = out_dir / "pre-splice-backup"
    backup_dir.mkdir(exist_ok=True)
    for path in (srt_path, vtt_path, txt_path):
        if path.exists():
            shutil.copy2(path, backup_dir / path.name)

    main_segments = srt_tools.parse_srt(srt_path)
    range_segments = srt_tools.parse_srt(range_srt)

    offset_ms = int(round(offset_s * 1000))
    end_ms = int(round(end_s * 1000)) if end_s is not None else None

    merged = srt_tools.splice(main_segments, range_segments, offset_ms, end_ms)

    srt_tools.write_srt(srt_path, merged)
    srt_tools.write_vtt(vtt_path, merged)
    srt_tools.write_txt(txt_path, merged)

    return len(range_segments), backup_dir
