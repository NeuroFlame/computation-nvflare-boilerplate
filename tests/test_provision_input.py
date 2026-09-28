import json
import os
import sys
import unittest

REPO_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, REPO_ROOT)
sys.path.insert(0, os.path.join(REPO_ROOT, "system"))

from system.entry_provision import build_computation_parameters


class BuildComputationParametersTest(unittest.TestCase):
    SITE_MAP = {"user1": "site_one", "user2": "site_two"}

    def test_leader_id_is_added_with_site_map(self):
        parameters = build_computation_parameters(
            {
                "consortium_leader_id": "user1",
                "computation_parameters": json.dumps({"key": "value"}),
            },
            self.SITE_MAP,
        )
        self.assertEqual(
            parameters,
            {
                "key": "value",
                "site_id_name_map": self.SITE_MAP,
                "consortium_leader_id": "user1",
            },
        )

    def test_leader_id_is_optional(self):
        parameters = build_computation_parameters(
            {"computation_parameters": "{}"}, self.SITE_MAP
        )
        self.assertNotIn("consortium_leader_id", parameters)

    def test_leader_need_not_be_a_participant(self):
        parameters = build_computation_parameters(
            {"consortium_leader_id": "leader-only"}, self.SITE_MAP
        )
        self.assertEqual(parameters["consortium_leader_id"], "leader-only")

    def test_invalid_leader_id_is_rejected(self):
        for leader_id in ("", "  ", 7):
            with self.assertRaisesRegex(ValueError, "consortium_leader_id"):
                build_computation_parameters(
                    {"consortium_leader_id": leader_id}, self.SITE_MAP
                )


if __name__ == "__main__":
    unittest.main()
