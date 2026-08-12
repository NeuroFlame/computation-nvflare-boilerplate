import importlib.util
import json
import os
import sys
import tempfile
import unittest
from types import SimpleNamespace
from unittest.mock import Mock, patch

REPO_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
CODE_DIR = os.path.join(REPO_ROOT, "app", "code")
sys.path.insert(0, CODE_DIR)

from framework import ComputationSpec, local_step, remote_step, stepped_workflow
from framework.errors import (
    find_terminal_errors,
    raise_for_terminal_errors,
    record_terminal_error,
)

NVFLARE_AVAILABLE = importlib.util.find_spec("nvflare") is not None

if NVFLARE_AVAILABLE:
    from framework.controller import ComputationController
    from framework.executor import ComputationExecutor
    from nvflare.apis.controller_spec import TaskCompletionStatus
    from nvflare.apis.fl_constant import FLContextKey, ReturnCode
    from nvflare.apis.job_def import JobMetaKey, RunStatus
    from nvflare.apis.shareable import make_reply

    NVFLARE_AVAILABLE = True


class FakeContext:
    def __init__(self, current_round=0, parameters=None, client_name=None):
        self.props = {
            "CURRENT_ROUND": current_round,
            "COMPUTATION_PARAMETERS": parameters or {},
        }
        if NVFLARE_AVAILABLE and client_name is not None:
            self.props[FLContextKey.CLIENT_NAME] = client_name

    def get_prop(self, key, default=None):
        return self.props.get(key, default)

    def set_prop(self, key, value, **_kwargs):
        self.props[key] = value


def load_module(name, relative_path):
    spec = importlib.util.spec_from_file_location(
        name, os.path.join(REPO_ROOT, relative_path)
    )
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


class TerminalErrorMarkerTests(unittest.TestCase):
    def test_terminal_error_marker_preserves_message_and_traceback(self):
        with tempfile.TemporaryDirectory() as output_dir:
            try:
                raise ValueError("bad computation input")
            except ValueError as error:
                record_terminal_error(output_dir, "input", error)

            errors = find_terminal_errors(output_dir)
            self.assertEqual(len(errors), 1)
            self.assertEqual(errors[0]["scope"], "input")
            self.assertEqual(errors[0]["message"], "bad computation input")
            self.assertIn("ValueError: bad computation input", errors[0]["traceback"])
            with self.assertRaisesRegex(RuntimeError, "bad computation input"):
                raise_for_terminal_errors(output_dir)


@unittest.skipUnless(
    NVFLARE_AVAILABLE, "NVFlare is not installed in this Python environment"
)
class RuntimeErrorHandlingTests(unittest.TestCase):
    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp_dir.cleanup)
        self.output_dir = os.path.join(self.temp_dir.name, "output")
        self.parameters_path = os.path.join(self.temp_dir.name, "parameters.json")
        with open(self.parameters_path, "w", encoding="utf-8") as parameters_file:
            json.dump({}, parameters_file)
        environment = patch.dict(
            os.environ,
            {
                "DATA_DIR": self.temp_dir.name,
                "OUTPUT_DIR": self.output_dir,
                "PARAMETERS_FILE_PATH": self.parameters_path,
            },
        )
        environment.start()
        self.addCleanup(environment.stop)

    def test_non_ok_client_result_is_terminal(self):
        client_task = SimpleNamespace(
            result=make_reply(ReturnCode.EXECUTION_EXCEPTION),
            task=SimpleNamespace(name="compute"),
            client=SimpleNamespace(name="site1"),
        )

        with self.assertRaisesRegex(
            RuntimeError,
            "compute.*site1.*EXECUTION_EXCEPTION",
        ):
            ComputationController._validate_site_result(
                None,
                client_task=client_task,
                fl_ctx=None,
            )

    def test_non_ok_task_completion_is_terminal(self):
        def broadcast_and_wait(**kwargs):
            kwargs["task"].completion_status = TaskCompletionStatus.TIMEOUT

        harness = SimpleNamespace(
            _task_timeout=5,
            _min_clients=1,
            _wait_time_after_min_received=0,
            broadcast_and_wait=broadcast_and_wait,
        )

        with self.assertRaisesRegex(RuntimeError, "compute.*TIMEOUT|compute.*timeout"):
            ComputationController._broadcast_task(
                harness,
                task_name="compute",
                data=make_reply(ReturnCode.OK),
                result_cb=lambda *_args, **_kwargs: True,
                fl_ctx=None,
                abort_signal=None,
            )

    def test_executor_logs_traceback_and_reraises_author_error(self):
        def fail_local(_payload):
            raise ValueError("local math failed")

        workflow = stepped_workflow(
            local_step(fn=fail_local),
            remote_step(fn=lambda site_results: site_results),
        )
        executor = ComputationExecutor()
        executor.SPEC = ComputationSpec(workflow)

        with self.assertRaisesRegex(ValueError, "local math failed"):
            executor.execute(
                "fail_local",
                make_reply(ReturnCode.OK),
                FakeContext(client_name="site1"),
                None,
            )

        with open(
            os.path.join(self.output_dir, "site1.log"), encoding="utf-8"
        ) as log_file:
            log_text = log_file.read()
        self.assertIn("Computation task 'fail_local' failed", log_text)
        self.assertIn("ValueError: local math failed", log_text)

    def test_controller_startup_error_records_terminal_marker(self):
        def compute(payload):
            return payload

        workflow = stepped_workflow(
            local_step(fn=compute),
            remote_step(fn=lambda site_results: site_results),
        )

        class TestController(ComputationController):
            SPEC = ComputationSpec(workflow)

        controller = TestController(min_clients=1)
        controller._engine = SimpleNamespace(get_component=lambda _component_id: Mock())
        with open(self.parameters_path, "w", encoding="utf-8") as parameters_file:
            parameters_file.write("not json")

        with self.assertRaises(json.JSONDecodeError):
            controller.start_controller(FakeContext())

        errors = find_terminal_errors(self.output_dir)
        self.assertEqual(len(errors), 1)
        self.assertEqual(errors[0]["scope"], "controller startup")
        self.assertIn("JSONDecodeError", errors[0]["traceback"])

    def test_executor_setup_error_records_terminal_marker(self):
        def compute(payload):
            return payload

        workflow = stepped_workflow(
            local_step(fn=compute),
            remote_step(fn=lambda site_results: site_results),
        )
        executor = ComputationExecutor()
        executor.SPEC = ComputationSpec(workflow)
        with open(self.parameters_path, "w", encoding="utf-8") as parameters_file:
            parameters_file.write("not json")

        with self.assertRaises(json.JSONDecodeError):
            executor.execute(
                "compute",
                make_reply(ReturnCode.OK),
                FakeContext(client_name="site1"),
                None,
            )

        errors = find_terminal_errors(self.output_dir)
        self.assertEqual(len(errors), 1)
        self.assertEqual(errors[0]["scope"], "site task compute")
        self.assertIn("JSONDecodeError", errors[0]["traceback"])


@unittest.skipUnless(
    NVFLARE_AVAILABLE, "NVFlare is not installed in this Python environment"
)
class EntrypointErrorHandlingTests(unittest.TestCase):
    def test_central_abnormal_job_shuts_down_and_raises(self):
        entry_central = load_module("test_entry_central", "system/entry_central.py")
        session = Mock()
        session.submit_job.return_value = "job-id"
        session.get_job_meta.return_value = {
            JobMetaKey.STATUS.value: RunStatus.FINISHED_EXECUTION_EXCEPTION.value,
        }

        with patch.object(entry_central, "start_server"), patch.object(
            entry_central,
            "new_secure_session",
            return_value=session,
        ):
            with self.assertRaisesRegex(RuntimeError, "FINISHED:EXECUTION_EXCEPTION"):
                entry_central.main()

        session.shutdown.assert_called_once_with("all")

    def test_central_completed_job_shuts_down_without_error(self):
        entry_central = load_module(
            "test_entry_central_success", "system/entry_central.py"
        )
        session = Mock()
        session.submit_job.return_value = "job-id"
        session.get_job_meta.return_value = {
            JobMetaKey.STATUS.value: RunStatus.FINISHED_COMPLETED.value,
        }

        with patch.object(entry_central, "start_server"), patch.object(
            entry_central,
            "new_secure_session",
            return_value=session,
        ):
            entry_central.main()

        session.shutdown.assert_called_once_with("all")

    def test_edge_tracks_foreground_nvflare_daemon(self):
        entry_edge = load_module("test_entry_edge", "system/entry_edge.py")
        completed_process = Mock()

        with patch.object(
            entry_edge.subprocess,
            "run",
            return_value=completed_process,
        ) as run:
            entry_edge.main()

        run.assert_called_once_with(
            ["/bin/bash", "/workspace/runKit/startup/sub_start.sh"],
            check=False,
        )
        completed_process.check_returncode.assert_called_once_with()

    def test_edge_reports_terminal_marker_before_subprocess_status(self):
        entry_edge = load_module("test_entry_edge_marker", "system/entry_edge.py")
        completed_process = Mock()

        with patch.object(
            entry_edge.subprocess,
            "run",
            return_value=completed_process,
        ), patch.object(
            entry_edge,
            "raise_for_terminal_errors",
            side_effect=RuntimeError("local math failed"),
        ):
            with self.assertRaisesRegex(RuntimeError, "local math failed"):
                entry_edge.main()

        completed_process.check_returncode.assert_not_called()

    def test_debugger_escalates_marker_after_zero_simulator_status(self):
        debugger = load_module("test_debugger", "debugger.py")
        simulator = Mock()
        simulator.run.return_value = 0
        simulator_args = SimpleNamespace(
            job_folder="job",
            workspace="workspace",
            clients="site1",
            n_clients=1,
            threads=None,
            gpu=None,
            max_clients=100,
        )

        with patch.object(
            debugger,
            "SimulatorRunner",
            return_value=simulator,
        ), patch.object(
            debugger,
            "raise_for_terminal_errors",
            side_effect=RuntimeError("remote math failed"),
        ):
            with self.assertRaisesRegex(RuntimeError, "remote math failed"):
                debugger.run_simulator(simulator_args)


if __name__ == "__main__":
    unittest.main()
