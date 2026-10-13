import subprocess
from pathlib import Path

from . import config

ALL_FORMATS = ("txt", "srt", "vtt", "json")
_FORMAT_FLAGS = {"txt": "-otxt", "srt": "-osrt", "vtt": "-ovtt", "json": "-oj"}


def transcribe(
    wav_path: Path,
    output_prefix: Path,
    language: str = config.LANGUAGE,
    beam_size: int = config.BEAM_SIZE,
    max_context: int | None = None,
    formats: tuple[str, ...] = ALL_FORMATS,
) -> None:
    """Runs whisper-cli; -of creates <prefix>.<format> files itself."""
    output_prefix.parent.mkdir(parents=True, exist_ok=True)
    cmd = [
        config.WHISPER_BIN,
        "-m", str(config.MODEL_PATH),
        "-f", str(wav_path),
        "-l", language,
        "-bs", str(beam_size),
        *(_FORMAT_FLAGS[fmt] for fmt in formats),
        "-of", str(output_prefix),
        "-pp",
        "--vad",
        "--vad-model", str(config.VAD_MODEL_PATH),
    ]
    if config.TECH_TERMS_PROMPT:
        cmd += ["--prompt", config.TECH_TERMS_PROMPT]
    if max_context is not None:
        cmd += ["-mc", str(max_context)]
    result = subprocess.run(cmd)
    if result.returncode != 0:
        raise RuntimeError(f"whisper-cli exited with code {result.returncode}")
