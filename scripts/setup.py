#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Run the complete setup and return the remaining desktop actions, not a false success."""

import argparse
import hashlib
import json
from pathlib import Path
import subprocess
import sys

import desktop
import install
from setup_support import apply_plan

ROOT = Path(__file__).resolve().parents[1]
SKILL_NAME = "jianghushuo-kb-setup"
SOURCE_URL = "https://github.com/hanyh56/jianghushuo-kb-setup"


def package_files(root):
    required = ["SKILL.md", "INSTALL.md", "scripts/setup.py", "scripts/install.py",
                "scripts/desktop.py", "scripts/setup_support.py", "assets/runtime-skill.md",
                "assets/legacy-v1-sha256.json", "assets/vault-manifest.json",
                "references/agent-hosts.md", "references/obsidian-desktop.md", "references/no-python.md"]
    for relative in required:
        if not (root / relative).is_file():
            raise ValueError("Incomplete skill package; download the complete ZIP from " + SOURCE_URL + ": missing " + relative)
    manifest = json.loads((root / "assets/vault-manifest.json").read_text(encoding="utf-8"))
    for item in manifest:
        relative = Path(item["path"])
        if relative.is_absolute() or ".." in relative.parts:
            raise ValueError("Invalid vault manifest path")
        path = root / "assets/vault" / relative
        if not path.is_file() or hashlib.sha256(path.read_bytes()).hexdigest() != item["sha256"]:
            raise ValueError("Missing or damaged bundled vault file: " + str(relative))
    files = []
    for path in sorted(root.rglob("*")):
        relative = path.relative_to(root)
        if any(part in {".git", "__pycache__", ".DS_Store", ".venv"} or ".jhs-backup-" in part for part in relative.parts) or path.suffix == ".pyc":
            continue
        if path.is_symlink():
            raise ValueError("Unexpected symlink in downloaded skill: " + str(path))
        if path.is_file():
            files.append(path)
    return files


def skill_plans(root, skills_dir, files, update=False):
    if skills_dir is None:
        return None, []
    target = skills_dir / SKILL_NAME
    if target.resolve() == root.resolve():
        return target, []
    if root.resolve() in target.resolve().parents or target.resolve() in root.resolve().parents:
        raise ValueError("Skill destination overlaps the downloaded source")
    if target.is_symlink() or (target.exists() and not target.is_dir()):
        raise ValueError("Skill destination must be a real directory: " + str(target))
    entry = target / "SKILL.md"
    if target.exists() and (not entry.is_file() or "name: " + SKILL_NAME not in entry.read_text(encoding="utf-8-sig").splitlines()):
        raise ValueError("Existing destination is not this skill; preserve it: " + str(target))
    plans = []
    for source in files:
        path = install.destination(target, source.relative_to(root))
        if path.exists() and not path.is_file():
            raise ValueError("Expected a skill file: " + str(path))
        old = path.read_bytes() if path.exists() else None
        data = source.read_bytes()
        if old is not None and old != data and not update:
            raise ValueError("Existing skill differs; use --update-skill only for an authorized update. Original bytes will be backed up: " + str(path))
        plans.append({"path": path, "old": old, "data": data, "kind": "setup_skill"})
    for plan in plans:
        for parent in plan["path"].parents:
            if parent.exists() and not parent.is_dir():
                raise ValueError("Skill parent is not a directory: " + str(parent))
    return target, plans


def run_files(vault, skills_dir, agent_file, check=False, dry_run=False):
    command = [sys.executable, str(ROOT / "scripts/install.py"), "--vault", str(vault)]
    if skills_dir is not None:
        command += ["--skills-dir", str(skills_dir)]
    if agent_file:
        command += ["--agent-file", str(agent_file)]
    if check:
        command.append("--check")
    elif dry_run:
        command.append("--dry-run")
    result = subprocess.run(command, capture_output=True, encoding="utf-8", timeout=120)
    try:
        report = json.loads(result.stdout or result.stderr)
    except ValueError:
        raise ValueError("File setup did not return a valid report: " + (result.stderr or result.stdout)[-1000:])
    if result.returncode not in (0, 2) or report.get("status") == "error":
        raise ValueError(report.get("error", "File setup failed"))
    return report


def setup(vault, skills_dir=None, agent_file=None, download_dir=None, check=False,
          recover_vault_not_found=False, update_skill=False):
    files = package_files(ROOT)
    target, plans = skill_plans(ROOT, skills_dir, files, update=update_skill)
    # Preflight both destinations before writing either the skill or the vault.
    preview = run_files(vault, skills_dir, agent_file, check=check, dry_run=not check)
    if preview.get("conflicts"):
        return {"status": "needs_review", "complete": False, "files": preview,
                "next": "Read and merge the reported user file conflicts; do not overwrite them"}
    if not check:
        for plan in plans:
            apply_plan(plan)
    result = preview if check else run_files(vault, skills_dir, agent_file)
    pending = []
    skill_ready = target is not None and all((target / p.relative_to(ROOT)).is_file()
        and (target / p.relative_to(ROOT)).read_bytes() == p.read_bytes() for p in files)
    if not skill_ready:
        pending.append({"action": "install_setup_skill_in_host", "source": str(ROOT),
                        "detail": "Use the actual host skill directory or upload the complete package; verify it is enabled"})
    if result.get("status") != "ok":
        pending.append({"action": "finish_files_or_agent_entry", "detail": "Inspect files report; retain existing notes"})
    info = desktop.doctor()
    app = {"status": "already_installed" if info["installed"] else "not_installed"}
    if not check and not info["installed"]:
        try:
            app = desktop.install(info, download_dir or Path.home() / "Downloads/Obsidian-knowledge-base-setup")
        except (OSError, ValueError, subprocess.SubprocessError) as exc:
            app = {"status": "needs_installation_recovery", "error": str(exc), "official_download": desktop.DOWNLOAD_PAGE}
        info = desktop.doctor()
    plan = desktop.open_plan(info, vault, recover_vault_not_found)
    if not check:
        try:
            desktop.dispatch(info, plan)
        except (OSError, ValueError, subprocess.SubprocessError) as exc:
            plan["dispatch_error"] = str(exc)
            pending.append({"action": "open_application_with_desktop_tool", "detail": str(exc)})
    if not info["installed"]:
        pending.append({"action": "finish_obsidian_installation", "detail": app})
    elif plan["status"] == "needs_user_desktop":
        pending.append({"action": "continue_on_user_desktop", "vault": str(vault)})
    elif plan.get("folder_to_select"):
        pending.append({"action": "register_existing_folder_in_gui", "folder": str(vault),
                        "detail": "Dismiss Vault not found if present. Open folder as vault / 打开本地仓库. Select this exact folder, then rerun setup without --recover-vault-not-found"})
    pending.append({"action": "verify_host_and_workbench_in_ui", "vault": str(vault),
                    "detail": "Verify the skill is enabled, the correct vault/workbench, folders, templates and Bases. Record actual UI evidence; command dispatch is insufficient"})
    return {"status": "needs_actions", "complete": False, "source": SOURCE_URL,
            "setup_skill": {"path": str(target) if target else None, "files_installed": skill_ready,
                            "host_enabled": "requires_host_verification"},
            "vault": str(vault), "files": result, "obsidian": app,
            "desktop": plan, "pending_actions": pending,
            "next": "The agent must perform pending_actions, rerun checks after GUI changes, and only then report observed completion"}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--vault", help="Default: ~/Documents/个人知识库; reuse a known existing matching vault")
    parser.add_argument("--agent", choices=["codex", "claude"])
    parser.add_argument("--skills-dir", help="Actual skill directory of this host, overrides --agent")
    parser.add_argument("--agent-file", help="Actual external persistent host instruction file")
    parser.add_argument("--download-dir")
    parser.add_argument("--check", action="store_true", help="Read-only verification; no downloads, writes, or app launch")
    parser.add_argument("--recover-vault-not-found", action="store_true")
    parser.add_argument("--update-skill", action="store_true", help="Authorized setup-skill update, with byte-for-byte backups")
    args = parser.parse_args()
    vault = install.absolute(args.vault).resolve() if args.vault else Path.home() / "Documents/个人知识库"
    skills_dir = install.absolute(args.skills_dir).resolve() if args.skills_dir else None
    if skills_dir is None and args.agent:
        skills_dir = Path.home() / (".agents" if args.agent == "codex" else ".claude") / "skills"
    if skills_dir is not None and (skills_dir == vault or vault in skills_dir.parents or skills_dir in vault.parents):
        raise ValueError("Knowledge base and host skills directory must be separate")
    report = setup(vault, skills_dir, args.agent_file,
                   install.absolute(args.download_dir) if args.download_dir else None,
                   args.check, args.recover_vault_not_found, args.update_skill)
    print(json.dumps(report, ensure_ascii=False, indent=2))
    return 2 if report.get("status") == "needs_review" else 0


if __name__ == "__main__":
    try:
        sys.exit(main())
    except (OSError, ValueError, subprocess.SubprocessError) as exc:
        print(json.dumps({"status": "error", "complete": False, "error": str(exc)}, ensure_ascii=False), file=sys.stderr)
        sys.exit(1)
