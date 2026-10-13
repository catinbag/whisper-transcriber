import json
import tempfile
import unittest
from pathlib import Path

from src import qc


def whisper_segment(from_ms: int, to_ms: int, text: str) -> dict:
    def fmt(ms: int) -> str:
        h, rem = divmod(ms, 3_600_000)
        m, rem = divmod(rem, 60_000)
        s, ms = divmod(rem, 1000)
        return f"{h:02d}:{m:02d}:{s:02d},{ms:03d}"

    return {
        "timestamps": {"from": fmt(from_ms), "to": fmt(to_ms)},
        "offsets": {"from": from_ms, "to": to_ms},
        "text": text,
    }


class QcTest(unittest.TestCase):
    def write_json(self, segments: list[dict]) -> Path:
        tmp = tempfile.TemporaryDirectory()
        self.addCleanup(tmp.cleanup)
        path = Path(tmp.name) / "a.json"
        path.write_text(json.dumps({"transcription": segments}), encoding="utf-8")
        return path

    def test_long_segment_is_flagged(self):
        path = self.write_json([
            whisper_segment(0, 5_000, " short"),
            whisper_segment(5_000, 55_000, " very long"),
        ])
        flagged = qc.find_long_segments(path, max_seconds=45)
        self.assertEqual(len(flagged), 1)
        self.assertEqual(flagged[0]["duration_seconds"], 50.0)
        self.assertEqual(flagged[0]["text"], "very long")

    def test_segment_at_threshold_is_not_flagged(self):
        path = self.write_json([whisper_segment(0, 45_000, " edge")])
        self.assertEqual(qc.find_long_segments(path, max_seconds=45), [])

    def test_repetition_loop_is_flagged(self):
        segments = [whisper_segment(0, 1000, " intro")]
        segments += [whisper_segment(1000 + i * 1000, 2000 + i * 1000, " stuck") for i in range(4)]
        segments.append(whisper_segment(5000, 6000, " outro"))
        loops = qc.find_repetition_loops(self.write_json(segments), min_repeats=4)
        self.assertEqual(len(loops), 1)
        self.assertEqual(loops[0]["repeats"], 4)
        self.assertEqual(loops[0]["text"], "stuck")
        self.assertEqual(loops[0]["from"], "00:00:01,000")
        self.assertEqual(loops[0]["to"], "00:00:05,000")

    def test_run_shorter_than_min_repeats_is_ignored(self):
        segments = [whisper_segment(i * 1000, (i + 1) * 1000, " same") for i in range(3)]
        self.assertEqual(qc.find_repetition_loops(self.write_json(segments), min_repeats=4), [])


if __name__ == "__main__":
    unittest.main()
