import json
import re
import time
from pathlib import Path

from . import audio, config, qc, whisper_runner


def slugify(name: str) -> str:
    name = name.lower()
    name = re.sub(r"[\W_]+", "-", name)
    return name.strip("-") or "recording"


def run(video_path: Path) -> Path:
    video_path = video_path.resolve()
    if not video_path.exists():
        raise FileNotFoundError(f"Video not found: {video_path}")

    if not config.MODEL_PATH.exists():
        raise FileNotFoundError(
            f"Model not found: {config.MODEL_PATH}. Download it using the command from the README."
        )

    if not config.VAD_MODEL_PATH.exists():
        raise FileNotFoundError(
            f"VAD model not found: {config.VAD_MODEL_PATH}. Download it using the command from the README."
        )

    slug = slugify(video_path.stem)
    out_dir = config.OUTPUT_DIR / slug
    out_dir.mkdir(parents=True, exist_ok=True)

    wav_path = out_dir / f"{slug}.wav"
    output_prefix = out_dir / slug

    print(f"[1/3] Extracting audio from {video_path.name}...")
    audio.extract_wav(video_path, wav_path)
    duration = audio.get_duration_seconds(wav_path)

    print("[2/3] Transcribing (whisper-cli, model large-v3)...")
    started = time.time()
    whisper_runner.transcribe(wav_path, output_prefix)
    elapsed = time.time() - started

    wav_path.unlink(missing_ok=True)

    json_path = output_prefix.with_suffix(".json")
    flagged_segments = qc.find_long_segments(json_path)
    repetition_loops = qc.find_repetition_loops(json_path)

    meta = {
        "source_file": video_path.name,
        "duration_seconds": round(duration, 1),
        "model": config.MODEL_PATH.name,
        "language": config.LANGUAGE,
        "beam_size": config.BEAM_SIZE,
        "prompt": config.TECH_TERMS_PROMPT,
        "vad": True,
        "vad_model": config.VAD_MODEL_PATH.name,
        "processing_seconds": round(elapsed, 1),
        "qc_flagged_segments": flagged_segments,
        "qc_repetition_loops": repetition_loops,
    }
    (out_dir / "meta.json").write_text(
        json.dumps(meta, ensure_ascii=False, indent=2), encoding="utf-8"
    )

    print(f"[3/3] Done: {out_dir}")
    if flagged_segments:
        print(f"⚠ Found {len(flagged_segments)} suspiciously long segments (see meta.json):")
        for seg in flagged_segments:
            print(f"  {seg['from']} → {seg['to']} ({seg['duration_seconds']}s): {seg['text'][:80]}")
    if repetition_loops:
        print(f"⚠ Found {len(repetition_loops)} repetition loops (see meta.json):")
        for loop in repetition_loops:
            print(f"  {loop['from']} → {loop['to']} ({loop['repeats']}x): {loop['text'][:80]}")
    return out_dir
