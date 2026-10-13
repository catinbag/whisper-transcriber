# whisper

Local audio and video transcription via [whisper.cpp](https://github.com/ggml-org/whisper.cpp) (`large-v3` model, Silero VAD, Russian by default). Output: `.txt`, `.srt`, `.vtt`, `.json` and a `meta.json` with QC results.

It also includes tools for fixing Whisper hallucinations (looping on a single phrase, one long meaningless segment): re-transcribe a time range in isolation and splice the result back into the transcript while preserving timing.

## Requirements

- Python 3.10+ (no third-party dependencies, standard library only)
- `ffmpeg` and `ffprobe`
- `whisper-cli` from whisper.cpp in `PATH`

On macOS:

```bash
brew install ffmpeg whisper-cpp
```

## Models

Models are not stored in the repository. Download them into `models/`:

```bash
mkdir -p models
curl -L -o models/ggml-large-v3.bin \
  https://huggingface.co/ggerganov/whisper.cpp/resolve/main/ggml-large-v3.bin
curl -L -o models/ggml-silero-v6.2.0.bin \
  https://huggingface.co/ggml-org/whisper-vad/resolve/main/ggml-silero-v6.2.0.bin
```

`ggml-large-v3.bin` is about 3 GB.

## Usage

Put a video into `input/` and run:

```bash
python3 transcribe.py input/video.mp4
```

The result appears in `output/video/`: `video.txt`, `video.srt`, `video.vtt`, `video.json`, `meta.json`.

### QC

After transcription the following checks run:

- segments longer than `QC_MAX_SEGMENT_SECONDS` (45 s), which are likely hallucinations;
- runs of `QC_MIN_REPEATS` or more identical segments in a row, where the model got stuck.

Flagged sections are printed to the console and written to `output/<slug>/meta.json`.

### Fixing a problematic section

1. Re-transcribe only the needed range:

   ```bash
   python3 retranscribe_range.py video 00:12:00 00:28:00
   # if the model loops, disable context carry-over:
   python3 retranscribe_range.py video 00:12:00 00:28:00 --max-context 0
   ```

2. Splice the result back into the main transcript (`--offset` and `--end` in seconds):

   ```bash
   python3 splice.py video <range.srt> --offset 720 --end 1680
   ```

   The previous files are saved to `output/video/pre-splice-backup/`.

For argument details run `python3 retranscribe_range.py --help` and `python3 splice.py --help`.

### Digest

To get a compact view of a transcript (one line per segment, `HH:MM:SS text`), handy for skimming or passing to an LLM:

```bash
python3 digest.py video
```

The result is written to `output/video/video.digest.txt` (use `-o` for another path).

## Configuration

Settings live in `src/config.py`: model paths, language, `BEAM_SIZE`, QC thresholds, and `TECH_TERMS_PROMPT`, an optional prompt with domain-specific terms (empty by default).

## Tests

Unit tests cover the pure logic (SRT handling, QC checks, range splicing) and need no models, ffmpeg or whisper-cli:

```bash
python3 -m unittest
```

## Layout

```
transcribe.py            # entry point
retranscribe_range.py    # re-transcribe a time range
splice.py                # splice a range into the transcript
digest.py                # compact one-line-per-segment digest
src/
  pipeline.py            # main pipeline
  audio.py               # ffmpeg/ffprobe
  whisper_runner.py      # whisper-cli invocation
  qc.py                  # hallucination checks
  repair.py              # re-transcribe a range, splice it into the transcript
  srt_tools.py           # SRT/VTT/TXT/digest handling
  config.py              # settings
tests/                   # unit tests (unittest)
input/                   # input videos (not committed)
output/                  # results (not committed)
models/                  # models (not committed)
```
