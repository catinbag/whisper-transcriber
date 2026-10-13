import subprocess
from pathlib import Path


def extract_wav(
    video_path: Path,
    wav_path: Path,
    start_s: float | None = None,
    duration_s: float | None = None,
) -> None:
    """Extracts mono 16 kHz WAV, the format whisper.cpp expects.

    If start_s/duration_s are given, only that range of the recording is extracted.
    """
    wav_path.parent.mkdir(parents=True, exist_ok=True)
    cmd = ["ffmpeg", "-y"]
    if start_s is not None:
        cmd += ["-ss", str(start_s)]
    cmd += ["-i", str(video_path)]
    if duration_s is not None:
        cmd += ["-t", str(duration_s)]
    cmd += [
        "-ar", "16000",
        "-ac", "1",
        "-c:a", "pcm_s16le",
        str(wav_path),
    ]
    result = subprocess.run(cmd, capture_output=True, text=True)
    if result.returncode != 0:
        raise RuntimeError(f"ffmpeg failed:\n{result.stderr}")


def get_duration_seconds(media_path: Path) -> float:
    cmd = [
        "ffprobe",
        "-v", "error",
        "-show_entries", "format=duration",
        "-of", "default=noprint_wrappers=1:nokey=1",
        str(media_path),
    ]
    result = subprocess.run(cmd, capture_output=True, text=True)
    if result.returncode != 0:
        raise RuntimeError(f"ffprobe failed:\n{result.stderr}")
    return float(result.stdout.strip())
