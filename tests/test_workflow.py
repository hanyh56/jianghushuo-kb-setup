# -*- coding: utf-8 -*-
from pathlib import Path
import shutil
import sys
import tempfile
import unittest
from unittest import mock
from urllib.parse import parse_qs, urlparse

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
import desktop
import setup as workflow


def contents(root):
    return {p.relative_to(root).as_posix(): p.read_bytes() for p in root.rglob("*") if p.is_file()}


class WindowsRecoveryTests(unittest.TestCase):
    def info(self, path):
        return {"system": "Windows", "installed": True, "launch_command": ["Obsidian.exe"],
                "desktop_session_detected": True,
                "registered_vaults": [{"id": "real-vault-id", "path": path}]}

    def test_windows_case_separators_unicode_and_exact_folder_match(self):
        registered = "C:/Users/Administrator/Documents/个人 知识库"
        info = self.info(registered)
        for variant in [registered, "c:\\users\\administrator\\documents\\个人 知识库\\",
                        "C:\\Users\\Administrator\\Documents\\other\\..\\个人 知识库"]:
            plan = desktop.open_plan(info, variant)
            query = parse_qs(urlparse(plan["command"][-1]).query)
            self.assertEqual(query["vault"], ["real-vault-id"])
            self.assertEqual(query["file"], ["知识资产工作台.md"])
            self.assertNotIn("path", query)
            self.assertTrue(plan["registered"])
            self.assertFalse(plan["complete"])
        for other in [registered + "-旧", registered + "/子目录"]:
            plan = desktop.open_plan(info, other)
            self.assertEqual(plan["command"][-1], "obsidian://choose-vault")
            self.assertEqual(plan["folder_to_select"], other)

    def test_reported_vault_not_found_forces_picker_even_with_cached_registration(self):
        path = "C:/Users/Administrator/Documents/个人知识库"
        info = self.info(path)
        recovery = desktop.open_plan(info, path, recover_vault_not_found=True)
        self.assertEqual(recovery["command"][-1], "obsidian://choose-vault")
        self.assertIsNone(recovery["registered"])
        self.assertFalse(recovery["complete"])
        # After the user/agent selects the existing folder, the normal action can open by ID.
        resumed = desktop.open_plan(info, path)
        self.assertIn("vault=real-vault-id", resumed["command"][-1])

    def test_unreadable_registry_does_not_reuse_untrusted_cached_vault(self):
        path = "C:/Users/Administrator/Documents/个人知识库"
        info = self.info(path)
        info["registry_read_error"] = "Access denied"
        result = desktop.open_plan(info, path)
        self.assertEqual(result["status"], "needs_registry_check")
        self.assertIsNone(result["registered"])
        self.assertEqual(result["command"][-1], "obsidian://choose-vault")

    def test_installed_headless_environment_does_not_launch_gui(self):
        info = self.info("/home/user/知识库")
        info["desktop_session_detected"] = False
        result = desktop.open_plan(info, Path("/home/user/知识库"))
        self.assertEqual(result["status"], "needs_user_desktop")
        self.assertNotIn("command", result)

    def test_doctor_reports_locked_registry_without_changing_it(self):
        with tempfile.TemporaryDirectory() as temporary:
            path = Path(temporary) / "obsidian.json"
            original = b'{"vaults":{}}'
            path.write_bytes(original)
            with mock.patch.object(desktop, "registry_path", return_value=path), \
                 mock.patch.object(desktop, "find_app", return_value=["existing"]), \
                 mock.patch.object(Path, "read_text", side_effect=PermissionError("locked")):
                info = desktop.doctor()
            self.assertEqual(info["vault_registry_path"], str(path))
            self.assertIn("locked", info["registry_read_error"])
            self.assertEqual(path.read_bytes(), original)


class WorkflowTests(unittest.TestCase):
    def setUp(self):
        temporary = tempfile.TemporaryDirectory(prefix="jhs-workflow-")
        self.addCleanup(temporary.cleanup)
        self.base = Path(temporary.name)
        self.vault = self.base / "个人 中文库"
        self.skills = self.base / "真实宿主技能"
        self.info = {"system": "Windows", "installed": True,
                     "launch_command": ["Obsidian.exe"], "desktop_session_detected": True,
                     "registered_vaults": []}
        self.doctor = mock.patch.object(desktop, "doctor", return_value=self.info).start()
        self.dispatch = mock.patch.object(desktop, "dispatch").start()
        self.installer = mock.patch.object(desktop, "install").start()
        self.addCleanup(mock.patch.stopall)

    def test_full_setup_first_registration_and_resume(self):
        first = workflow.setup(self.vault, self.skills)
        self.assertTrue(first["setup_skill"]["files_installed"])
        self.assertEqual(first["files"]["roundtrip"]["retrieval"], "passed")
        self.assertTrue(first["files"]["roundtrip"]["probe_removed"])
        self.assertEqual(first["desktop"]["command"][-1], "obsidian://choose-vault")
        self.assertIn("register_existing_folder_in_gui", [a["action"] for a in first["pending_actions"]])
        self.assertFalse(first["complete"])
        self.assertTrue((self.skills / "jianghushuo-kb-setup/scripts/setup.py").is_file())
        self.assertTrue((self.skills / "personal-kb/SKILL.md").is_file())
        before = contents(self.base)
        self.info["registered_vaults"] = [{"id": "selected-in-real-picker", "path": str(self.vault)}]
        resumed = workflow.setup(self.vault, self.skills)
        self.assertEqual(contents(self.base), before)
        self.assertTrue(resumed["desktop"]["registered"])
        self.assertIn("vault=selected-in-real-picker", resumed["desktop"]["command"][-1])
        self.assertNotIn("register_existing_folder_in_gui", [a["action"] for a in resumed["pending_actions"]])
        self.assertFalse(resumed["complete"])  # It still needs actual host/desktop evidence.
        self.installer.assert_not_called()

    def test_check_is_read_only_even_without_installed_application(self):
        self.info["installed"] = False
        before = contents(self.base)
        checked = workflow.setup(self.vault, self.skills, check=True)
        self.assertEqual(contents(self.base), before)
        self.assertFalse(checked["complete"])
        self.installer.assert_not_called()
        self.dispatch.assert_not_called()

    def test_failed_download_keeps_ready_files_and_returns_recovery_action(self):
        self.info["installed"] = False
        self.installer.side_effect = OSError("download unavailable")
        result = workflow.setup(self.vault, self.skills)
        self.assertEqual(result["files"]["status"], "ok")
        self.assertEqual(result["obsidian"]["status"], "needs_installation_recovery")
        self.assertIn("finish_obsidian_installation", [a["action"] for a in result["pending_actions"]])
        self.assertFalse(result["complete"])
        self.assertNotIn("command", result["desktop"])

    def test_windows_installer_launch_does_not_count_as_installed(self):
        self.info["installed"] = False
        self.installer.return_value = {"status": "installer_launched_finish_in_gui"}
        result = workflow.setup(self.vault, self.skills)
        self.assertEqual(result["desktop"]["status"], "needs_installation")
        self.assertIn("finish_obsidian_installation", [a["action"] for a in result["pending_actions"]])
        self.assertFalse(result["complete"])

    def test_note_conflict_stops_before_copying_skill_or_launching_app(self):
        self.vault.mkdir()
        path = self.vault / "知识资产工作台.md"
        path.write_text("# 用户原有内容", encoding="utf-8")
        before = contents(self.base)
        result = workflow.setup(self.vault, self.skills)
        self.assertEqual(result["status"], "needs_review")
        self.assertEqual(contents(self.base), before)
        self.assertFalse(self.skills.exists())
        self.dispatch.assert_not_called()
        self.installer.assert_not_called()

    def test_authorized_skill_update_backs_up_exact_original_bytes(self):
        workflow.setup(self.vault, self.skills)
        target = self.skills / "jianghushuo-kb-setup/SKILL.md"
        original = target.read_bytes() + b"\nLocal customization\r\n"
        target.write_bytes(original)
        before = contents(self.base)
        with self.assertRaises(ValueError):
            workflow.setup(self.vault, self.skills)
        self.assertEqual(contents(self.base), before)
        workflow.setup(self.vault, self.skills, update_skill=True)
        self.assertEqual(target.read_bytes(), (ROOT / "SKILL.md").read_bytes())
        self.assertEqual(next(target.parent.glob("SKILL.md.jhs-backup-*")).read_bytes(), original)
        self.assertFalse(any(".jhs-backup-" in p.name for p in workflow.package_files(target.parent)))

    def test_missing_or_damaged_package_is_rejected_before_installation(self):
        source = self.base / "下载包"
        source.mkdir()
        (source / "SKILL.md").write_text("incomplete", encoding="utf-8")
        with self.assertRaises(ValueError):
            workflow.package_files(source)
        shutil.rmtree(source)
        shutil.copytree(ROOT, source, ignore=shutil.ignore_patterns("__pycache__", ".git", ".venv"))
        (source / "assets/vault/知识资产工作台.md").write_text("damaged", encoding="utf-8")
        with self.assertRaises(ValueError):
            workflow.package_files(source)
        self.assertFalse(self.vault.exists())


if __name__ == "__main__":
    unittest.main()
