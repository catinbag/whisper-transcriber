import re
from pathlib import Path

_TIME_RE = re.compile(r"(\d\d):(\d\d):(\d\d)[,.](\d\d\d)")


def srt_time_to_ms(value: str) -> int:
    h, m, s, ms = _TIME_RE.match(value.strip()).groups()
    return ((int(h) * 3600 + int(m) * 60 + int(s)) * 1000) + int(ms)


def ms_to_srt_time(ms: int) -> str:
    h, rem = divmod(ms, 3_600_000)
    m, rem = divmod(rem, 60_000)
    s, ms = divmod(rem, 1000)
    return f"{h:02d}:{m:02d}:{s:02d},{ms:03d}"


def parse_srt(path: Path) -> list[dict]:
    text = Path(path).read_text(encoding="utf-8")
    blocks = re.split(r"\n\s*\n", text.strip())
    segments = []
    for block in blocks:
        lines = block.strip().splitlines()
        if len(lines) < 2:
            continue
        has_index = lines[0].strip().isdigit()
        time_line = lines[1] if has_index else lines[0]
        match = re.match(r"(.+?)\s*-->\s*(.+)", time_line)
        if not match:
            continue
        body_lines = lines[2:] if has_index else lines[1:]
        segments.append({
            "start_ms": srt_time_to_ms(match.group(1)),
            "end_ms": srt_time_to_ms(match.group(2)),
            "text": "\n".join(body_lines),
        })
    return segments


def write_srt(path: Path, segments: list[dict]) -> None:
    lines = []
    for i, seg in enumerate(segments, start=1):
        lines.append(str(i))
        lines.append(f"{ms_to_srt_time(seg['start_ms'])} --> {ms_to_srt_time(seg['end_ms'])}")
        lines.append(seg["text"])
        lines.append("")
    Path(path).write_text("\n".join(lines), encoding="utf-8")


def write_vtt(path: Path, segments: list[dict]) -> None:
    lines = ["WEBVTT", ""]
    for seg in segments:
        start = ms_to_srt_time(seg["start_ms"]).replace(",", ".")
        end = ms_to_srt_time(seg["end_ms"]).replace(",", ".")
        lines.append(f"{start} --> {end}")
        lines.append(seg["text"])
        lines.append("")
    Path(path).write_text("\n".join(lines), encoding="utf-8")


def write_txt(path: Path, segments: list[dict]) -> None:
    body = "\n".join(seg["text"].strip() for seg in segments)
    Path(path).write_text(body + "\n", encoding="utf-8")


def splice(main_segments: list[dict], range_segments: list[dict], offset_ms: int, end_ms: int | None) -> list[dict]:
    """Replaces the [offset_ms, end_ms) section of the main transcript with range_segments (shifted)."""
    shifted = []
    for seg in range_segments:
        shifted.append({
            "start_ms": seg["start_ms"] + offset_ms,
            "end_ms": seg["end_ms"] + offset_ms,
            "text": seg["text"],
        })

    before = [s for s in main_segments if s["start_ms"] < offset_ms]
    after = [s for s in main_segments if end_ms is not None and s["start_ms"] >= end_ms]

    return before + shifted + after


def format_digest(segments: list[dict]) -> str:
    """One line per segment: 'HH:MM:SS text'. Compact form for reading or feeding to an LLM."""
    lines = []
    for seg in segments:
        stamp = ms_to_srt_time(seg["start_ms"])[:8]
        text = " ".join(line.strip() for line in seg["text"].splitlines())
        lines.append(f"{stamp} {text}")
    return "\n".join(lines) + "\n"
