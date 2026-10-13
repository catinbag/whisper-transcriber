import unittest

from src import pipeline


class SlugifyTest(unittest.TestCase):
    def test_spaces_and_punctuation(self):
        self.assertEqual(pipeline.slugify("My Video (final)"), "my-video-final")

    def test_cyrillic_is_kept(self):
        self.assertEqual(pipeline.slugify("Видео 1"), "видео-1")

    def test_empty_falls_back(self):
        self.assertEqual(pipeline.slugify("!!!"), "recording")


if __name__ == "__main__":
    unittest.main()
