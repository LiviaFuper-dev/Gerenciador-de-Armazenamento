import unittest

from storage_manager.utils import chunks, get_header


class HelperTests(unittest.TestCase):
    def test_chunks_keep_every_id(self):
        values = [str(index) for index in range(1001)]
        groups = list(chunks(values, 500))
        self.assertEqual([len(group) for group in groups], [500, 500, 1])
        self.assertEqual([item for group in groups for item in group], values)

    def test_header_lookup_is_case_insensitive(self):
        self.assertEqual(get_header([{"name": "Subject", "value": "Teste"}], "subject"), "Teste")


if __name__ == "__main__":
    unittest.main()
