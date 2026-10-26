# -*- coding: utf-8 -*-
import contextlib
import hashlib
import io
import json
import re
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import unittest
from unittest import mock

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
import desktop
import install
import setup_support


def digest_tree(root):
    return {p.relative_to(root).as_posix(): hashlib.sha256(p.read_bytes()).hexdigest()
            for p in root.rglob("*") if p.is_file()}


class SetupTests(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory(prefix="jhs-test-")
        self.addCleanup(self.temporary.cleanup)
        self.base = Path(self.temporary.name)
        self.vault = self.base / "用户 空格知识库"
        self.skills = self.base / "Agent 技能"

    def run_install(self, *options, expected=0):
        command = [sys.executable, str(ROOT / "scripts/install.py"), "--vault", str(self.vault), "--skills-dir", str(self.skills)]
        result = subprocess.run(command + list(options), cwd=str(self.base), capture_output=True, encoding="utf-8")
        self.assertEqual(result.returncode, expected, result.stdout + result.stderr)
        return json.loads(result.stdout if result.stdout else result.stderr)

    def test_fresh_setup_repeat_and_readonly_check(self):
        preview = self.run_install("--dry-run")
        self.assertEqual(preview["status"], "ready_to_install")
        self.assertFalse(self.vault.exists())
        self.assertFalse(self.skills.exists())
        self.assertEqual(preview["completion"]["agent_entry"], "not_configured")
        result = self.run_install()
        self.assertEqual(result["status"], "ok")
        self.assertEqual(result["completion"]["agent_entry"], "configured")
        self.assertEqual(result["roundtrip"]["retrieval"], "passed")
        self.assertTrue(result["roundtrip"]["probe_removed"])
        self.assertFalse(list(self.vault.rglob("_安装验收-*")))
        self.assertEqual(result["links"]["broken"], [])
        settings = json.loads((self.vault / ".obsidian/templates.json").read_text(encoding="utf-8"))
        self.assertEqual(settings["folder"], "90-系统/模板")
        daily = json.loads((self.vault / ".obsidian/daily-notes.json").read_text(encoding="utf-8"))
        self.assertTrue((self.vault / daily["folder"]).is_dir())
        runtime = (self.skills / "personal-kb/SKILL.md").read_text(encoding="utf-8")
        self.assertIn(json.dumps(str(self.vault.resolve()), ensure_ascii=False), runtime)
        self.assertNotIn("{{VAULT_PATH_JSON}}", runtime)
        before = digest_tree(self.base)
        repeated = self.run_install()
        self.assertEqual(repeated["created"], [])
        self.assertEqual(repeated["updated"], [])
        self.assertEqual(digest_tree(self.base), before)
        checked = self.run_install("--check")
        self.assertEqual(checked["status"], "ok")
        self.assertEqual(digest_tree(self.base), before)

    def test_existing_settings_merged_and_backed_up(self):
        directory = self.vault / ".obsidian"
        directory.mkdir(parents=True)
        original = b'\xef\xbb\xbf{ "theme": "custom", "alwaysUpdateLinks": false, "newFileFolderPath": "old" }\r\n'
        (directory / "app.json").write_bytes(original)
        (directory / "core-plugins.json").write_text('["graph", "canvas"]', encoding="utf-8")
        result = self.run_install()
        merged = json.loads((directory / "app.json").read_text(encoding="utf-8"))
        self.assertEqual(merged["theme"], "custom")
        self.assertTrue(merged["alwaysUpdateLinks"])
        self.assertEqual(merged["newFileFolderPath"], "00-灵感与收件箱")
        backup = next(directory.glob("app.json.jhs-backup-*"))
        self.assertEqual(backup.read_bytes(), original)
        plugins = json.loads((directory / "core-plugins.json").read_text(encoding="utf-8"))
        self.assertIn("graph", plugins)
        self.assertIn("canvas", plugins)
        self.assertIn("templates", plugins)
        self.assertEqual(len(plugins), len(set(plugins)))
        self.assertTrue(result["updated"])

    def test_dictionary_plugins_preserve_unrelated_choices(self):
        folder = self.vault / ".obsidian"
        folder.mkdir(parents=True)
        (folder / "core-plugins.json").write_text('{"canvas": false, "templates": false}', encoding="utf-8")
        self.run_install()
        plugins = json.loads((folder / "core-plugins.json").read_text(encoding="utf-8"))
        self.assertFalse(plugins["canvas"])
        self.assertTrue(plugins["templates"])

    def test_conflicting_note_preserved_and_reported(self):
        self.vault.mkdir()
        original = "# 本人原有工作台\n\n真实记录保留。\n"
        path = self.vault / "知识资产工作台.md"
        path.write_text(original, encoding="utf-8")
        report = self.run_install()
        self.assertEqual(report["status"], "needs_review")
        self.assertIn("知识资产工作台.md", report["conflicts"])
        self.assertEqual(path.read_text(encoding="utf-8"), original)
        self.run_install("--check", expected=2)

    def test_v1_exact_template_upgrade_with_backup(self):
        legacy = ROOT / "assets/legacy-v1-sha256.json"
        hashes = json.loads(legacy.read_text(encoding="utf-8"))
        # This is the exact public v1 workbench, not user data.
        old = "# 知识资产工作台\n\n先处理眼前的问题，需要什么再找什么。[[开始这里|不知道放哪里？]]\n\n| 现在想做什么 | 入口 |\n| --- | --- |\n| 记下一个新想法 | [[00-灵感与收件箱/00-收件箱入口]] |\n| 推进一个具体任务 | [[01-Projects-当前任务/00-项目入口]] |\n| 找自己的经历或长期判断 | [[02-Areas-长期领域/00-领域入口]] |\n| 找原话或外部参考 | [[03-Resources-参考资料/00-资料入口]] |\n| 调用以前用过的方法 | [[05-Skills-经验复利/00-经验入口]] |\n| 回到历史和暂停材料 | [[04-Archive-归档/00-归档入口]] |\n\n新建笔记参考 [[90-系统/模板使用说明]]；维护参考 [[90-系统/维护与AI协作规则]]。\n\n## 当前项目索引\n\n尚未记录项目。确认具体任务后，在这里链接项目卡。不要把演示或安装验证当成真实项目。\n\n## 可选动态视图\n\n使用支持 Bases 的 Obsidian 时，可打开 [[90-系统/知识库看板.base]]。其他工具直接使用上面的 Markdown 入口，Agent 按文件夹和属性查找笔记。\n"
        self.assertEqual(hashlib.sha256(old.encode()).hexdigest(), hashes["知识资产工作台.md"])
        self.vault.mkdir()
        path = self.vault / "知识资产工作台.md"
        path.write_bytes(old.encode())
        report = self.run_install()
        self.assertEqual(report["conflicts"], [])
        self.assertIn("#项目", path.read_text(encoding="utf-8"))
        self.assertEqual(next(self.vault.glob("知识资产工作台.md.jhs-backup-*")).read_bytes(), old.encode())

    def test_runtime_collision_fails_before_any_vault_write(self):
        path = self.skills / "personal-kb/SKILL.md"
        path.parent.mkdir(parents=True)
        path.write_text("Another existing skill", encoding="utf-8")
        self.run_install(expected=1)
        self.assertFalse(self.vault.exists())
        self.assertEqual(path.read_text(encoding="utf-8"), "Another existing skill")

    def test_invalid_json_fails_before_any_new_file(self):
        folder = self.vault / ".obsidian"
        folder.mkdir(parents=True)
        (folder / "templates.json").write_text("invalid JSON", encoding="utf-8")
        before = digest_tree(self.base)
        self.run_install(expected=1)
        self.assertEqual(digest_tree(self.base), before)

    def test_existing_instruction_bytes_preserved(self):
        path = self.base / "CLAUDE.md"
        original = b'\xef\xbb\xbf# Existing rules\r\nKeep all of this.\r\n'
        path.write_bytes(original)
        self.run_install("--agent-file", str(path))
        first = path.read_bytes()
        self.assertTrue(first.startswith(original))
        self.run_install("--agent-file", str(path))
        self.assertEqual(path.read_bytes(), first)

    def test_probe_collision_does_not_delete_existing_file(self):
        folder = self.vault / "00-灵感与收件箱"
        folder.mkdir(parents=True)
        path = folder / "_安装验收-fixed.md"
        path.write_text("existing", encoding="utf-8")
        with mock.patch.object(setup_support.uuid, "uuid4", return_value=mock.Mock(hex="fixed")):
            with self.assertRaises(FileExistsError):
                setup_support.roundtrip(self.vault, install.destination)
        self.assertEqual(path.read_text(encoding="utf-8"), "existing")

    def test_symlink_conflict_fails_before_installation(self):
        protected = self.base / "protected"
        protected.mkdir()
        self.vault.mkdir()
        try:
            (self.vault / "90-系统").symlink_to(protected, target_is_directory=True)
        except OSError:
            self.skipTest("This machine does not grant symlink creation")
        self.run_install(expected=1)
        self.assertEqual(list(protected.iterdir()), [])
        self.assertFalse(self.skills.exists())

    def test_agent_default_directories(self):
        for agent, directory in (("codex", ".agents"), ("claude", ".claude")):
            vault = self.base / agent
            output = io.StringIO()
            with mock.patch.object(sys, "argv", ["install.py", "--vault", str(vault), "--agent", agent, "--dry-run"]), mock.patch.object(Path, "home", return_value=self.base), contextlib.redirect_stdout(output):
                self.assertEqual(install.main(), 0)
            self.assertEqual(json.loads(output.getvalue())["runtime_skill"], str(self.base / directory / "skills/personal-kb/SKILL.md"))
            self.assertFalse(vault.exists())


class DesktopTests(unittest.TestCase):
    def fixture_release(self):
        names = ["Obsidian-1.2.3.dmg", "Obsidian-1.2.3.exe", "Obsidian-1.2.3.AppImage", "Obsidian-1.2.3-arm64.AppImage"]
        return {"assets": [{"name": name, "digest": "sha256:" + "a" * 64, "browser_download_url": "https://github.com/obsidianmd/obsidian-releases/releases/download/v1.2.3/" + name} for name in names]}

    def test_official_architecture_selection(self):
        release = self.fixture_release()
        cases = [("Darwin", "arm64", ".dmg"), ("Windows", "AMD64", ".exe"), ("Linux", "x86_64", "1.2.3.AppImage"), ("Linux", "aarch64", "-arm64.AppImage")]
        for system, machine, suffix in cases:
            self.assertTrue(desktop.select_asset(release, system, machine)["name"].endswith(suffix))
        with self.assertRaises(ValueError):
            desktop.select_asset(release, "Linux", "unknown")

    def test_unsigned_metadata_or_wrong_host_rejected(self):
        release = self.fixture_release()
        release["assets"][0]["digest"] = None
        with self.assertRaises(ValueError):
            desktop.select_asset(release, "Darwin", "arm64")
        release = self.fixture_release()
        release["assets"][0]["browser_download_url"] = "https://example.invalid/download"
        with self.assertRaises(ValueError):
            desktop.select_asset(release, "Darwin", "arm64")

    def test_existing_application_skips_all_network(self):
        with mock.patch.object(desktop, "request", side_effect=AssertionError("network must not be used")):
            report = desktop.install({"installed": True, "launch_command": ["existing"]}, Path("unused"))
        self.assertEqual(report["status"], "already_installed")

    def test_headless_does_not_install_a_desktop_app(self):
        with mock.patch.object(desktop, "request", side_effect=AssertionError("network must not be used")):
            result = desktop.install({"installed": False, "desktop_session_detected": False}, Path("unused"))
        self.assertEqual(result["status"], "needs_user_desktop")

    def test_download_checks_digest_and_preserves_existing(self):
        with tempfile.TemporaryDirectory() as temporary:
            directory = Path(temporary)
            content = b"official-fixture-only"
            asset = {"name": "test.dmg", "digest": "sha256:" + hashlib.sha256(content).hexdigest(), "browser_download_url": "fixture"}
            with mock.patch.object(desktop, "request", return_value=io.BytesIO(content)):
                path = desktop.download(asset, directory)
            self.assertEqual(path.read_bytes(), content)
            path.write_bytes(b"different-existing-file")
            with self.assertRaises(ValueError):
                desktop.download(asset, directory)
            self.assertEqual(path.read_bytes(), b"different-existing-file")
            asset["name"] = "mismatch.dmg"
            with mock.patch.object(desktop, "request", return_value=io.BytesIO(b"wrong")):
                with self.assertRaises(ValueError):
                    desktop.download(asset, directory)
            self.assertFalse((directory / "mismatch.dmg").exists())
            self.assertEqual(list(directory.glob("*.part-*")), [])

    def test_new_vault_is_not_misreported_as_registered(self):
        with tempfile.TemporaryDirectory() as temporary:
            vault = Path(temporary) / "库 空格"
            info = {"installed": True, "launch_command": ["obsidian"], "registered_vaults": []}
            result = desktop.open_plan(info, vault)
            self.assertEqual(result["status"], "needs_vault_registration")
            self.assertEqual(result["command"][-1], "obsidian://choose-vault")
            info["registered_vaults"] = [{"id": "known-id", "path": str(vault)}]
            result = desktop.open_plan(info, vault)
            self.assertEqual(result["status"], "open_dispatched_ui_confirmation_required")
            self.assertIn("vault=known-id", result["command"][-1])
            self.assertIn("file=", result["command"][-1])
            self.assertNotIn("知识资产工作台", result["command"][-1])


class PackageTests(unittest.TestCase):
    def test_documentation_and_vault_manifest_are_complete(self):
        manifest = json.loads((ROOT / "assets/vault-manifest.json").read_text(encoding="utf-8"))
        actual = digest_tree(ROOT / "assets/vault")
        self.assertEqual({item["path"]: item["sha256"] for item in manifest}, actual)
        for path in [ROOT / "SKILL.md", ROOT / "README.md"] + list((ROOT / "references").glob("*.md")):
            content = path.read_text(encoding="utf-8")
            for target in re.findall(r"\[[^\]]*\]\(([^)]+)\)", content):
                if "://" in target or target.startswith("#"):
                    continue
                self.assertTrue((path.parent / target.split("#", 1)[0]).exists(), str(path) + " -> " + target)


if __name__ == "__main__":
    unittest.main()
