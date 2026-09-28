import unittest

from storage_manager.updates import update_from_release, version_tuple


class UpdateTests(unittest.TestCase):
    def test_compares_semantic_versions_numerically(self):
        self.assertGreater(version_tuple("v1.10.0"), version_tuple("1.9.9"))

    def test_returns_newer_release_from_expected_repository(self):
        update = update_from_release(
            "0.1.0",
            {
                "tag_name": "v0.2.0",
                "html_url": (
                    "https://github.com/LiviaFuper-dev/"
                    "Gerenciador-de-Armazenamento/releases/tag/v0.2.0"
                ),
                "assets": [
                    {
                        "name": "GerenciadorDeArmazenamento-v0.2.0-windows-setup.exe",
                        "browser_download_url": (
                            "https://github.com/LiviaFuper-dev/"
                            "Gerenciador-de-Armazenamento/releases/download/v0.2.0/"
                            "GerenciadorDeArmazenamento-v0.2.0-windows-setup.exe"
                        ),
                    }
                ],
            },
        )

        self.assertIsNotNone(update)
        self.assertEqual(update.version, "0.2.0")
        self.assertTrue(update.download_url.endswith("windows-setup.exe"))

    def test_ignores_current_version_and_unexpected_urls(self):
        current = {
            "tag_name": "v0.1.0",
            "html_url": (
                "https://github.com/LiviaFuper-dev/"
                "Gerenciador-de-Armazenamento/releases/tag/v0.1.0"
            ),
        }
        external = {
            "tag_name": "v9.0.0",
            "html_url": "https://example.com/releases/v9.0.0",
        }
        missing_installer = {
            "tag_name": "v9.0.0",
            "html_url": (
                "https://github.com/LiviaFuper-dev/"
                "Gerenciador-de-Armazenamento/releases/tag/v9.0.0"
            ),
            "assets": [],
        }

        self.assertIsNone(update_from_release("0.1.0", current))
        self.assertIsNone(update_from_release("0.1.0", external))
        self.assertIsNone(update_from_release("0.1.0", missing_installer))


if __name__ == "__main__":
    unittest.main()
