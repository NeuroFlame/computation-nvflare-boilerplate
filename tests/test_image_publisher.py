import tempfile
import unittest
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch

from scripts import publish_computation_image
from scripts.neuroflame_manifest import write_manifest


class ImagePublisherTests(unittest.TestCase):
    def test_dirty_tracked_files_are_rejected_for_publication(self):
        with patch.object(
            publish_computation_image.subprocess,
            "run",
            return_value=SimpleNamespace(returncode=1),
        ):
            with self.assertRaisesRegex(ValueError, "tracked uncommitted"):
                publish_computation_image._ensure_tracked_files_clean(Path("."))

    def test_build_labels_reads_committed_contract_versions(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            repository = Path(temp_dir)
            write_manifest(
                repository,
                {
                    "manifestVersion": 1,
                    "computation": {"version": "1.2.3"},
                    "compatibility": {
                        "computationApiVersion": "0.1.0",
                        "boilerplateVersion": "0.1.0",
                    },
                    "image": {
                        "title": "example",
                        "repository": "example/computation",
                        "floatingTag": "latest",
                        "tagPrefix": "",
                        "source": "https://example.test/computation",
                    },
                },
            )
            (repository / "requirements.txt").write_text(
                "nvflare==2.8.0\n", encoding="utf-8"
            )

            labels, config = publish_computation_image.build_labels(
                repository, "a" * 40
            )

            self.assertEqual(labels["org.opencontainers.image.version"], "1.2.3")
            self.assertEqual(labels["org.neuroflame.computation-api.version"], "0.1.0")
            self.assertEqual(labels["org.neuroflame.nvflare.version"], "2.8.0")
            self.assertEqual(config["repository"], "example/computation")

    def test_image_tags_include_floating_release_and_revision(self):
        config = {
            "repository": "example/computations",
            "floatingTag": "ridge",
            "tagPrefix": "ridge-",
        }

        tags = publish_computation_image._image_tags(config, "1.2.3", "abc1234")

        self.assertEqual(
            tags,
            [
                "example/computations:ridge",
                "example/computations:ridge-1.2.3",
                "example/computations:ridge-abc1234",
            ],
        )


if __name__ == "__main__":
    unittest.main()
