import importlib.util
import inspect
import json
import os
import sys
import tempfile
import unittest

import yaml

REPO_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
CODE_DIR = os.path.join(REPO_ROOT, "app", "code")
SYSTEM_DIR = os.path.join(REPO_ROOT, "system")
sys.path.insert(0, REPO_ROOT)
sys.path.insert(0, CODE_DIR)
sys.path.insert(0, SYSTEM_DIR)

from debugger import build_simulator_command, configure_simulator_authorization
from system.entry_provision import validate_network_config
from system.provision.code.create_run_kits import extend_component_allow_list
from system.provision.code.generate_project_file import generate_project_file
from system.provision.code.provision_run import find_latest_production_directory

NVFLARE_AVAILABLE = importlib.util.find_spec("nvflare") is not None

if NVFLARE_AVAILABLE:
    import nvflare
    from framework.controller import ComputationController
    from nvflare.apis.shareable import Shareable


class ProvisioningMigrationTests(unittest.TestCase):
    def test_project_uses_single_port_and_no_removed_builders(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            project_path = os.path.join(temp_dir, "Project.yml")
            generate_project_file(
                project_name="project",
                host_identifier="server.example.com",
                fed_learn_port=8002,
                output_file_path=project_path,
                site_names=["site1", "site2"],
            )
            with open(project_path, encoding="utf-8") as project_file:
                project = yaml.safe_load(project_file)

        server = project["participants"][0]
        self.assertEqual(server["fed_learn_port"], 8002)
        self.assertNotIn("admin_port", server)
        builder_paths = [builder["path"] for builder in project["builders"]]
        self.assertNotIn("nvflare.lighter.impl.template.TemplateBuilder", builder_paths)
        self.assertNotIn("overseer", json.dumps(project).lower())
        self.assertNotIn("nvflare.ha", json.dumps(project).lower())

    def test_removed_admin_port_is_rejected(self):
        with self.assertRaisesRegex(ValueError, "admin_port.*removed"):
            validate_network_config(
                {
                    "fed_learn_port": 8002,
                    "admin_port": 8003,
                    "host_identifier": "server.example.com",
                }
            )

    def test_latest_provisioning_stage_is_selected(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            for name in ("prod_00", "prod_09", "prod_02", "state"):
                os.makedirs(os.path.join(temp_dir, name))
            self.assertEqual(
                find_latest_production_directory(temp_dir),
                os.path.join(temp_dir, "prod_09"),
            )

    def test_runtime_allow_list_extends_provisioned_defaults(self):
        with tempfile.TemporaryDirectory() as kit_path:
            local_path = os.path.join(kit_path, "local")
            os.makedirs(local_path)
            resources_path = os.path.join(local_path, "resources.json.default")
            with open(resources_path, "w", encoding="utf-8") as resources_file:
                json.dump(
                    {"format_version": 2, "class_allow_list": ["nvflare.Example"]},
                    resources_file,
                )

            extend_component_allow_list(
                kit_path,
                ("runtime.controller.RuntimeController",),
            )
            with open(resources_path, encoding="utf-8") as resources_file:
                resources = json.load(resources_file)

        self.assertEqual(
            resources["class_allow_list"],
            ["nvflare.Example", "runtime.controller.RuntimeController"],
        )
        self.assertEqual(resources["class_list_enforcement_mode"], "enforce")


class SimulatorCommandTests(unittest.TestCase):
    def test_simulator_authorization_preserves_existing_classes(self):
        with tempfile.TemporaryDirectory() as workspace:
            local_path = os.path.join(workspace, "local")
            os.makedirs(local_path)
            resources_path = os.path.join(local_path, "resources.json")
            with open(resources_path, "w", encoding="utf-8") as resources_file:
                json.dump({"class_allow_list": ["existing.Component"]}, resources_file)

            configure_simulator_authorization(workspace)

            with open(resources_path, encoding="utf-8") as resources_file:
                resources = json.load(resources_file)
            self.assertEqual(
                resources["class_allow_list"],
                ["existing.Component", "nvflare.", "runtime."],
            )

    def test_public_simulator_cli_command_preserves_wrapper_options(self):
        args = type(
            "Args",
            (),
            {
                "job_folder": "job",
                "workspace": "workspace",
                "n_clients": 2,
                "clients": "site1,site2",
                "threads": 1,
                "gpu": None,
                "log_config": "concise",
                "max_clients": 100,
                "end_run_for_all": True,
            },
        )()

        self.assertEqual(
            build_simulator_command(args),
            [
                "nvflare",
                "simulator",
                "job",
                "-w",
                "workspace",
                "-n",
                "2",
                "-c",
                "site1,site2",
                "-t",
                "1",
                "-l",
                "concise",
                "-m",
                "100",
                "--end_run_for_all",
            ],
        )


@unittest.skipUnless(NVFLARE_AVAILABLE, "NVFlare is not installed")
class NVFlare28ApiTests(unittest.TestCase):
    def test_expected_nvflare_version_is_installed(self):
        self.assertEqual(nvflare.__version__, "2.8.0")

    def test_unknown_task_callback_uses_28_signature(self):
        self.assertEqual(
            tuple(
                inspect.signature(
                    ComputationController.process_result_of_unknown_task
                ).parameters
            ),
            (
                "self",
                "client",
                "task_name",
                "client_task_id",
                "result",
                "fl_ctx",
            ),
        )

    def test_shareable_preserves_wrapper_payload(self):
        payload = {"result": {"kind": "dataclass", "items": [1, 2, 3]}}
        shareable = Shareable(payload)
        self.assertEqual(shareable["result"], payload["result"])


if __name__ == "__main__":
    unittest.main()
