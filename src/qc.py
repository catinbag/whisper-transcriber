import json
from pathlib import Path

from . import config


def find_long_segments(json_path: Path, max_seconds: float = config.QC_MAX_SEGMENT_SECONDS) -> list[dict]:
    """Returns whisper segments longer than max_seconds, likely hallucinations."""
    data = json.loads(Path(json_path).read_text(encoding="utf-8"))
    flagged = []
    for seg in data.get("transcription", []):
        duration = (seg["offsets"]["to"] - seg["offsets"]["from"]) / 1000
        if duration > max_seconds:
            flagged.append({
                "from": seg["timestamps"]["from"],
                "to": seg["timestamps"]["to"],
                "duration_seconds": round(duration, 1),
                "text": seg["text"].strip(),
            })
    return flagged


def find_repetition_loops(json_path: Path, min_repeats: int = config.QC_MIN_REPEATS) -> list[dict]:
    """Finds runs of consecutive segments with identical text, a sign of decoder looping."""
    data = json.loads(Path(json_path).read_text(encoding="utf-8"))
    segments = data.get("transcription", [])
    flagged = []
    i = 0
    n = len(segments)
    while i < n:
        j = i + 1
        text = segments[i]["text"].strip()
        while j < n and segments[j]["text"].strip() == text:
            j += 1
        run_length = j - i
        if run_length >= min_repeats:
            flagged.append({
                "from": segments[i]["timestamps"]["from"],
                "to": segments[j - 1]["timestamps"]["to"],
                "repeats": run_length,
                "text": text,
            })
        i = j
    return flagged
