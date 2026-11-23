# -*- coding: utf-8 -*-
"""Protect personal notes/progress and verify safe upgrades of the entry they use.

Conversation wording and question selection are checked with scenario walkthroughs,
not claimed to be proven by these filesystem tests.
"""
import hashlib
import json
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import unittest
from unittest import mock

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
import install
import setup as workflow
import setup_support


class InterviewIntegrationTests(unittest.TestCase):
    def setUp(self):
        temporary = tempfile.TemporaryDirectory(prefix="jhs-interview-")
        self.addCleanup(temporary.cleanup)
        self.base = Path(temporary.name)
        self.vault = self.base / "测试使用者知识库"
        self.skills = self.base / "宿主技能"

    def run_install(self, *args):
        result = subprocess.run(
            [sys.executable, str(ROOT / "scripts/install.py"), "--vault", str(self.vault),
             "--skills-dir", str(self.skills)] + list(args),
            capture_output=True, encoding="utf-8")
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        return json.loads(result.stdout)

    def test_install_does_not_seed_user_facts_or_managed_profile(self):
        self.run_install()
        manifest = json.loads((ROOT / "assets/vault-manifest.json").read_text(encoding="utf-8"))
        managed = {item["path"] for item in manifest}
        self.assertFalse((self.vault / "02-Areas-长期领域/我是谁.md").exists())
        self.assertFalse((self.vault / "90-系统/个人说明入口.md").exists())
        self.assertNotIn("02-Areas-长期领域/我是谁.md", managed)
        self.assertTrue((self.vault / "90-系统/我是谁访谈规则.md").is_file())

    def test_reinstall_preserves_profile_and_progress_in_all_states(self):
        self.run_install()
        # Use a non-default location, as required for pre-existing user notes.
        profile = self.vault / "02-Areas-长期领域/已有个人介绍.md"
        entry = self.vault / "90-系统/个人说明入口.md"
        for state in ("待开始访谈", "访谈中", "已暂停", "已跳过", "初版可用"):
            with self.subTest(state=state):
                original = ("---\nstatus: " + state + "\nprivacy: 私密\n---\n"
                            "# 隔离测试资料\n本人明确的话：我最近在学陶艺。\n"
                            "待答问题：你希望 AI 先帮哪一步？\n跳过项：时间安排。\n").encode("utf-8")
                profile.write_bytes(original)
                pointer = "# 个人说明入口\n\n[[02-Areas-长期领域/已有个人介绍]]\n".encode("utf-8")
                entry.write_bytes(pointer)
                self.run_install()
                self.run_install("--check")
                self.assertEqual(profile.read_bytes(), original)
                self.assertEqual(entry.read_bytes(), pointer)
                self.assertFalse((self.vault / "02-Areas-长期领域/我是谁.md").exists())

    def test_exact_prior_runtime_same_vault_upgrades_with_original_byte_backup(self):
        path = self.skills / "personal-kb/SKILL.md"
        path.parent.mkdir(parents=True)
        template = '---\nname: personal-kb\n---\n{{VAULT_PATH_JSON}}\nOld bundled rules.\n'
        original = template.replace("{{VAULT_PATH_JSON}}", json.dumps(str(self.vault), ensure_ascii=False)).encode("utf-8")
        path.write_bytes(original)
        known = {"runtime_skill": [hashlib.sha256(template.encode("utf-8")).hexdigest()]}
        with mock.patch.object(setup_support, "previous_revisions", return_value=known):
            plan = setup_support.runtime_plan(self.vault, self.skills, ROOT, install.destination)
        applied = setup_support.apply_plan(plan)
        self.assertEqual(Path(applied["backup"]).read_bytes(), original)
        self.assertEqual(path.read_bytes(), plan["data"])

    def test_known_runtime_for_other_vault_or_customized_entry_is_preserved(self):
        path = self.skills / "personal-kb/SKILL.md"
        path.parent.mkdir(parents=True)
        template = '{{VAULT_PATH_JSON}}\nOld bundled rules.\n'
        known = {"runtime_skill": [hashlib.sha256(template.encode("utf-8")).hexdigest()]}
        for content in (
                template.replace("{{VAULT_PATH_JSON}}", json.dumps(str(self.base / "另一个库"), ensure_ascii=False)),
                template.replace("{{VAULT_PATH_JSON}}", json.dumps(str(self.vault), ensure_ascii=False)) + "Custom instruction\n"):
            with self.subTest(content=content):
                original = content.encode("utf-8")
                path.write_bytes(original)
                with mock.patch.object(setup_support, "previous_revisions", return_value=known):
                    with self.assertRaises(ValueError):
                        setup_support.runtime_plan(self.vault, self.skills, ROOT, install.destination)
                self.assertEqual(path.read_bytes(), original)

    def test_roundtrip_read_failure_cleans_probe_and_does_not_report_pass(self):
        (self.vault / "00-灵感与收件箱").mkdir(parents=True)
        with mock.patch.object(Path, "read_text", side_effect=PermissionError("fixture: read blocked")):
            with self.assertRaises(PermissionError):
                setup_support.roundtrip(self.vault, install.destination)
        self.assertEqual(list(self.vault.rglob("_安装验收-*")), [])

    def test_roundtrip_write_failure_is_not_success(self):
        (self.vault / "00-灵感与收件箱").mkdir(parents=True)
        with mock.patch.object(Path, "open", side_effect=PermissionError("fixture: write blocked")):
            with self.assertRaises(PermissionError):
                setup_support.roundtrip(self.vault, install.destination)
        self.assertEqual(list(self.vault.rglob("_安装验收-*")), [])

    def test_setup_file_failure_stops_before_desktop_or_interview_action(self):
        with mock.patch.object(workflow, "run_files", side_effect=ValueError("fixture: write/read failed")), \
                mock.patch.object(workflow.desktop, "dispatch") as dispatch:
            with self.assertRaisesRegex(ValueError, "write/read failed"):
                workflow.setup(self.vault, self.skills)
        dispatch.assert_not_called()
        self.assertFalse(self.vault.exists())
        self.assertFalse(self.skills.exists())

    def test_skill_backups_are_neither_installed_into_vault_nor_manifested(self):
        source = self.base / "技能包副本"
        shutil.copytree(ROOT, source, ignore=shutil.ignore_patterns(".git", "__pycache__", "*.pyc", "*.jhs-backup-*"))
        backup = source / "assets/vault/AGENTS.md.jhs-backup-fixture"
        original = b"old bundled instruction backup; not a vault asset"
        backup.write_bytes(original)
        result = subprocess.run(
            [sys.executable, str(source / "scripts/install.py"), "--vault", str(self.vault),
             "--skills-dir", str(self.skills)], capture_output=True, encoding="utf-8")
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        self.assertEqual(list(self.vault.rglob("*.jhs-backup-*")), [])
        rebuilt = subprocess.run([sys.executable, str(source / "scripts/build_manifest.py")],
                                 capture_output=True, encoding="utf-8")
        self.assertEqual(rebuilt.returncode, 0, rebuilt.stdout + rebuilt.stderr)
        manifest = json.loads((source / "assets/vault-manifest.json").read_text(encoding="utf-8"))
        self.assertNotIn("AGENTS.md.jhs-backup-fixture", {item["path"] for item in manifest})
        self.assertEqual(backup.read_bytes(), original)


if __name__ == "__main__":
    unittest.main()
