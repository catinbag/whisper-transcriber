import tempfile
import unittest
from pathlib import Path

from src import srt_tools


def seg(start_ms: int, end_ms: int, text: str) -> dict:
    return {"start_ms": start_ms, "end_ms": end_ms, "text": text}


class TimeConversionTest(unittest.TestCase):
    def test_srt_time_to_ms(self):
        self.assertEqual(srt_tools.srt_time_to_ms("01:02:03,456"), 3_723_456)

    def test_srt_time_accepts_dot_separator(self):
        self.assertEqual(srt_tools.srt_time_to_ms("00:00:01.500"), 1500)

    def test_ms_to_srt_time(self):
        self.assertEqual(srt_tools.ms_to_srt_time(3_723_456), "01:02:03,456")

    def test_roundtrip(self):
        for ms in (0, 999, 61_001, 86_399_999):
            self.assertEqual(srt_tools.srt_time_to_ms(srt_tools.ms_to_srt_time(ms)), ms)


class SrtFilesTest(unittest.TestCase):
    def test_write_then_parse_roundtrip(self):
        segments = [seg(0, 1500, "Hello"), seg(1500, 4000, "two\nlines")]
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "a.srt"
            srt_tools.write_srt(path, segments)
            self.assertEqual(srt_tools.parse_srt(path), segments)

    def test_parse_srt_without_index(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "a.srt"
            path.write_text("00:00:01,000 --> 00:00:02,000\ntext\n", encoding="utf-8")
            self.assertEqual(srt_tools.parse_srt(path), [seg(1000, 2000, "text")])

    def test_write_vtt_and_txt(self):
        segments = [seg(0, 1000, " one "), seg(1000, 2000, "two")]
        with tempfile.TemporaryDirectory() as tmp:
            vtt, txt = Path(tmp) / "a.vtt", Path(tmp) / "a.txt"
            srt_tools.write_vtt(vtt, segments)
            srt_tools.write_txt(txt, segments)
            self.assertTrue(vtt.read_text(encoding="utf-8").startswith("WEBVTT"))
            self.assertIn("00:00:01.000 --> 00:00:02.000", vtt.read_text(encoding="utf-8"))
            self.assertEqual(txt.read_text(encoding="utf-8"), "one\ntwo\n")


class SpliceTest(unittest.TestCase):
    def setUp(self):
        self.main = [
            seg(0, 1000, "a"),
            seg(1000, 2000, "b"),      # replaced
            seg(2000, 3000, "c"),      # replaced
            seg(3000, 4000, "d"),
        ]
        self.new = [seg(0, 500, "x"), seg(500, 2000, "y")]

    def test_replaces_range_and_shifts_timings(self):
        result = srt_tools.splice(self.main, self.new, offset_ms=1000, end_ms=3000)
        self.assertEqual(
            [s["text"] for s in result], ["a", "x", "y", "d"]
        )
        self.assertEqual(result[1]["start_ms"], 1000)
        self.assertEqual(result[2]["end_ms"], 3000)

    def test_without_end_drops_the_tail(self):
        result = srt_tools.splice(self.main, self.new, offset_ms=1000, end_ms=None)
        self.assertEqual([s["text"] for s in result], ["a", "x", "y"])


class DigestTest(unittest.TestCase):
    def test_one_line_per_segment(self):
        segments = [seg(3000, 4000, "first"), seg(3_723_000, 3_724_000, "multi\n line")]
        self.assertEqual(
            srt_tools.format_digest(segments),
            "00:00:03 first\n01:02:03 multi line\n",
        )


if __name__ == "__main__":
    unittest.main()
