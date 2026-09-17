import unittest

from storage_manager.models import ScanResult, format_bytes


class ModelsTests(unittest.TestCase):
    def test_scan_count(self):
        result = ScanResult(query="from:teste@example.com", message_ids=["1", "2"])
        self.assertEqual(result.count, 2)

    def test_format_bytes(self):
        self.assertEqual(format_bytes(0), "0 B")
        self.assertEqual(format_bytes(1024 * 1024), "1.0 MB")


if __name__ == "__main__":
    unittest.main()

