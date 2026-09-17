import json
import tempfile
import unittest
from pathlib import Path

from storage_manager.config import load_config
from storage_manager.errors import AppError


class ConfigTests(unittest.TestCase):
    def write_config(self, values: dict) -> Path:
        directory = tempfile.TemporaryDirectory()
        self.addCleanup(directory.cleanup)
        path = Path(directory.name) / "app_config.json"
        path.write_text(json.dumps(values), encoding="utf-8")
        return path

    def test_builds_exact_sender_query(self):
        path = self.write_config(
            {
                "app_name": "Teste",
                "expected_account": "conta@gmail.com",
                "target_sender": "diligencia@mlradvogados.com",
                "preview_limit": 100,
                "delete_batch_size": 500,
            }
        )
        config = load_config(path)
        self.assertEqual(config.gmail_query, "from:diligencia@mlradvogados.com")

    def test_rejects_invalid_sender(self):
        path = self.write_config(
            {
                "expected_account": "conta@gmail.com",
                "target_sender": "endereco-invalido",
                "preview_limit": 100,
                "delete_batch_size": 500,
            }
        )
        with self.assertRaises(AppError):
            load_config(path)

    def test_accepts_any_google_account_when_expected_account_is_empty(self):
        path = self.write_config(
            {
                "expected_account": "",
                "target_sender": "diligencia@mlradvogados.com",
                "preview_limit": 100,
                "delete_batch_size": 500,
            }
        )
        config = load_config(path)
        self.assertEqual(config.expected_account, "")


if __name__ == "__main__":
    unittest.main()
