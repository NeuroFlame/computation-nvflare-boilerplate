import json
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

REPOSITORY = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPOSITORY))

from system.provision.code.create_job import create_job


class JobParticipantCountTests(unittest.TestCase):
    def test_job_admission_and_each_step_require_all_participants(self):
        for count in (1, 2, 3, 5):
            with self.subTest(count=count), tempfile.TemporaryDirectory() as directory:
                source = Path(directory, "source")
                config_dir = source / "config"
                config_dir.mkdir(parents=True)
                original = {
                    "workflows": [
                        {
                            "path": "runtime.controller.RuntimeController",
                            "args": {"wait_time_after_min_received": 10},
                        }
                    ],
                    "components": [],
                }
                config_file = config_dir / "config_fed_server.json"
                config_file.write_text(json.dumps(original), encoding="utf-8")
                job = Path(directory, "job")
                with patch(
                    "system.provision.code.create_job.update_client_tasks_from_spec"
                ):
                    create_job(str(source), str(job), min_clients=count)
                meta = json.loads((job / "meta.json").read_text())
                server = json.loads(
                    (job / "app/config/config_fed_server.json").read_text()
                )
                self.assertEqual(meta["min_clients"], count)
                self.assertEqual(server["workflows"][0]["args"]["min_clients"], count)
                self.assertEqual(
                    server["workflows"][0]["args"]["wait_time_after_min_received"], 10
                )
                self.assertEqual(json.loads(config_file.read_text()), original)

    def test_invalid_participant_count_is_rejected_before_copying(self):
        for count in (0, -1, True, "3", 2.5):
            with self.subTest(count=count), tempfile.TemporaryDirectory() as directory:
                source = Path(directory, "source")
                source.mkdir()
                job = Path(directory, "job")
                with self.assertRaisesRegex(ValueError, "positive integer"):
                    create_job(str(source), str(job), min_clients=count)
                self.assertFalse(job.exists())


if __name__ == "__main__":
    unittest.main()
