import tempfile
import unittest
from pathlib import Path
from unittest import mock

from src import config, repair, srt_tools


class HhmmssTest(unittest.TestCase):
    def test_conversion(self):
        self.assertEqual(repair.hhmmss_to_seconds("00:00:00"), 0)
        self.assertEqual(repair.hhmmss_to_seconds("01:02:03.5"), 3723.5)


class RetranscribeRangeErrorsTest(unittest.TestCase):
    def test_missing_video(self):
        with tempfile.TemporaryDirectory() as tmp, \
                mock.patch.object(config, "INPUT_DIR", Path(tmp)):
            with self.assertRaisesRegex(FileNotFoundError, "video not found"):
                repair.retranscribe_range("nope", "00:00:01", "00:00:02")

    def test_end_before_start(self):
        with tempfile.TemporaryDirectory() as tmp, \
                mock.patch.object(config, "INPUT_DIR", Path(tmp)):
            (Path(tmp) / "v.mp4").touch()
            with self.assertRaisesRegex(ValueError, "range end"):
                repair.retranscribe_range("v", "00:00:10", "00:00:05")


class SpliceRangeTest(unittest.TestCase):
    def setUp(self):
        tmp = tempfile.TemporaryDirectory()
        self.addCleanup(tmp.cleanup)
        self.root = Path(tmp.name)
        patcher = mock.patch.object(config, "OUTPUT_DIR", self.root / "output")
        patcher.start()
        self.addCleanup(patcher.stop)

        self.out_dir = self.root / "output" / "v"
        self.out_dir.mkdir(parents=True)
        main = [
            {"start_ms": 0, "end_ms": 1000, "text": "a"},
            {"start_ms": 1000, "end_ms": 2000, "text": "broken"},
            {"start_ms": 2000, "end_ms": 3000, "text": "d"},
        ]
        srt_tools.write_srt(self.out_dir / "v.srt", main)
        srt_tools.write_vtt(self.out_dir / "v.vtt", main)
        srt_tools.write_txt(self.out_dir / "v.txt", main)

        self.range_srt = self.root / "range.srt"
        srt_tools.write_srt(self.range_srt, [{"start_ms": 0, "end_ms": 1000, "text": "fixed"}])

    def test_replaces_range_and_creates_backup(self):
        count, backup_dir = repair.splice_range("v", self.range_srt, offset_s=1.0, end_s=2.0)

        self.assertEqual(count, 1)
        texts = [s["text"] for s in srt_tools.parse_srt(self.out_dir / "v.srt")]
        self.assertEqual(texts, ["a", "fixed", "d"])
        self.assertEqual((self.out_dir / "v.txt").read_text(encoding="utf-8"), "a\nfixed\nd\n")

        self.assertEqual(backup_dir, self.out_dir / "pre-splice-backup")
        old_texts = [s["text"] for s in srt_tools.parse_srt(backup_dir / "v.srt")]
        self.assertEqual(old_texts, ["a", "broken", "d"])

    def test_missing_transcript(self):
        with self.assertRaisesRegex(FileNotFoundError, "not found"):
            repair.splice_range("other", self.range_srt, offset_s=0, end_s=None)

    def test_missing_range_file(self):
        with self.assertRaisesRegex(FileNotFoundError, "not found"):
            repair.splice_range("v", self.root / "missing.srt", offset_s=0, end_s=None)


if __name__ == "__main__":
    unittest.main()
