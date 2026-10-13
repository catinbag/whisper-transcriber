from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent

WHISPER_BIN = "whisper-cli"
MODEL_PATH = PROJECT_ROOT / "models" / "ggml-large-v3.bin"
VAD_MODEL_PATH = PROJECT_ROOT / "models" / "ggml-silero-v6.2.0.bin"

LANGUAGE = "ru"
BEAM_SIZE = 5

# A segment longer than this is suspected to be a hallucination: a normal
# phrase does not last that long. Whisper sometimes collapses an unclear
# stretch of speech (quiet off-screen talk, keyboard noise) into one long
# segment of meaningless text instead of splitting it properly. VAD threshold
# parameters (--vad-max-speech-duration-s, --vad-threshold) do not reliably
# fix this in practice, so instead of tuning them such segments are simply
# flagged for manual review against a reference text.
QC_MAX_SEGMENT_SECONDS = 45

# Another hallucination pattern: not one long segment but a run of short
# segments with identical text, where the model gets stuck repeating the last
# recognized phrase instead of new speech. A real speaker does not repeat a
# phrase word for word N times in a row, so such a run is almost always a
# lost piece of the recording worth re-transcribing separately (see
# retranscribe_range.py).
QC_MIN_REPEATS = 4

# Optional domain-terms prompt. An empty string means no prompt.
# A full sentence works better than a comma-separated word list: Whisper
# treats the prompt as speech context, not as a dictionary.
# Example: "This is a talk about machine learning: PyTorch, transformer, batch."
TECH_TERMS_PROMPT = ""

INPUT_DIR = PROJECT_ROOT / "input"
OUTPUT_DIR = PROJECT_ROOT / "output"
