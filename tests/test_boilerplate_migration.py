import tempfile
import unittest
from contextlib import redirect_stdout
from io import StringIO
from pathlib import Path
from unittest.mock import patch

from scripts import migrate_computation


class RequirementMigrationTests(unittest.TestCase):
    def test_framework_pins_are_updated_and_custom_packages_are_preserved(self):
        source = "nvflare==2.8.0\nnumpy==1.24.4\n"
        target = "nvflare==2.4.0\ncustom-math==7.1\n"

        self.assertEqual(
            migrate_computation.merge_requirements(source, target),
            "nvflare==2.8.0\ncustom-math==7.1\nnumpy==1.24.4\n",
        )


class BoilerplateMigrationTests(unittest.TestCase):
    def test_apply_replaces_only_managed_content(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            source = root / "source"
            target = root / "target"
            (source / "managed").mkdir(parents=True)
            (source / "managed/current.py").write_text("new\n", encoding="utf-8")
            (source / "wrapper.py").write_text("new wrapper\n", encoding="utf-8")
            (source / "requirements.txt").write_text(
                "nvflare==2.8.0\n", encoding="utf-8"
            )
            (source / ".dockerignore").write_text(".git\n*.tgz\n", encoding="utf-8")
            (source / migrate_computation.VERSION_FILE).write_text(
                "0.1.0\n", encoding="utf-8"
            )

            (target / "managed").mkdir(parents=True)
            (target / "managed/stale.py").write_text("old\n", encoding="utf-8")
            (target / "app/code/computation").mkdir(parents=True)
            author_file = target / "app/code/computation/remote_math.py"
            author_file.write_text("author math\n", encoding="utf-8")
            (target / "requirements.txt").write_text(
                "nvflare==2.4.0\ncustom-math==7.1\n", encoding="utf-8"
            )
            (target / ".dockerignore").write_text("custom-output\n", encoding="utf-8")

            with (
                patch.object(
                    migrate_computation,
                    "MANAGED_DIRECTORIES",
                    (Path("managed"),),
                ),
                patch.object(
                    migrate_computation,
                    "MANAGED_FILES",
                    (Path("wrapper.py"),),
                ),
            ):
                migrate_computation.apply_boilerplate(source, target)

            self.assertEqual(author_file.read_text(encoding="utf-8"), "author math\n")
            self.assertFalse((target / "managed/stale.py").exists())
            self.assertEqual(
                (target / "managed/current.py").read_text(encoding="utf-8"),
                "new\n",
            )
            self.assertEqual(
                (target / "requirements.txt").read_text(encoding="utf-8"),
                "nvflare==2.8.0\ncustom-math==7.1\n",
            )
            self.assertEqual(migrate_computation.read_version(target), "0.1.0")
            self.assertEqual(
                (target / ".dockerignore").read_text(encoding="utf-8"),
                "custom-output\n.git\n*.tgz\n",
            )

    def test_in_place_mode_requires_force(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            target = Path(temp_dir)
            (target / "app/code/computation").mkdir(parents=True)
            (target / "requirements.txt").write_text("", encoding="utf-8")

            with (
                patch.object(migrate_computation, "planned_changes", return_value=[]),
                self.assertRaisesRegex(ValueError, "requires --force"),
                redirect_stdout(StringIO()),
            ):
                migrate_computation.main([str(target), "--in-place"])


if __name__ == "__main__":
    unittest.main()
