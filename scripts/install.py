#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Offline, additive knowledge-base setup. Python 3.8+, standard library only."""

import argparse
import hashlib
import json
import os
from pathlib import Path
import re
import sys

from setup_support import apply_plan, roundtrip, runtime_plan, settings_plan

for stream in (sys.stdout, sys.stderr):
    if hasattr(stream, "reconfigure"):
        stream.reconfigure(encoding="utf-8")


ASSETS = Path(__file__).resolve().parent.parent / "assets" / "vault"
SKILL_ROOT = ASSETS.parent.parent
START = "<!-- jianghushuo-kb-setup:start -->"
END = "<!-- jianghushuo-kb-setup:end -->"


def absolute(value):
    return Path(os.path.abspath(os.path.expanduser(value)))


def destination(root, relative):
    target = root / relative
    node = target
    while node != root:
        if node.is_symlink():
            raise ValueError("Refusing symlink: " + str(node))
        if node != target and node.exists() and not node.is_dir():
            raise ValueError("Parent is not a directory: " + str(node))
        node = node.parent
    return target


def agent_entry(vault):
    lines = [START, "## 个人知识库", "", "知识库绝对路径："]
    lines.extend("> " + line for line in str(vault).splitlines())
    lines.extend([
        "", "涉及本人经历、项目或可复用方法时，先读取此库的 `AGENTS.md`、",
        "`知识资产工作台.md` 和 `90-系统/维护与AI协作规则.md`，再局部检索。",
        "用户要求记录时按规则写入并回读；普通讨论不自动入库。",
        "默认私密，区分事实、原话、推测和 AI 建议，不把计划写成成果。",
        "当前会话访问和跨会话加载须分别核实。", END, "",
    ])
    return "\n".join(lines).encode("utf-8")


def prepare_agent_file(path, vault):
    for parent in path.parents:
        if parent.exists() and not parent.is_dir():
            raise ValueError("Agent entry parent is not a directory: " + str(parent))
    if path.is_symlink() or (path.exists() and not path.is_file()):
        raise ValueError("Agent entry must be a regular file: " + str(path))
    if path == vault / "AGENTS.md":
        raise ValueError("--agent-file must be the host's external instruction file, not vault/AGENTS.md")
    old = path.read_bytes() if path.exists() else None
    text = (old or b"").decode("utf-8-sig")
    block = agent_entry(vault)
    if START in text or END in text:
        if text.count(START) != 1 or text.count(END) != 1:
            raise ValueError("Ambiguous existing knowledge-base entry: " + str(path))
        begin = text.index(START)
        finish = text.index(END) + len(END)
        existing = text[begin:finish].replace("\r\n", "\n")
        if existing != block.decode("utf-8").strip():
            raise ValueError("Existing entry points elsewhere or was edited; merge it manually: " + str(path))
        return old, old, "already_connected"
    separator = b"" if old is None or old == b"" or old.endswith(b"\n\n") else (b"\n" if old.endswith(b"\n") else b"\n\n")
    return old, (old or b"") + separator + block, "would_connect"


def check_links(vault, relatives):
    """Check bundled static wikilinks against installed paths; do not scan user notes."""
    broken = []
    checked = 0
    for relative in relatives:
        path = destination(vault, relative)
        if path.suffix != ".md" or not path.is_file():
            continue
        content = (ASSETS / relative).read_text(encoding="utf-8-sig")
        for raw in re.findall(r"\[\[([^\]]+)\]\]", content):
            target = raw.split("|", 1)[0].split("#", 1)[0].strip()
            if not target:
                continue
            checked += 1
            candidate = vault / target
            if not candidate.is_file() and not (vault / (target + ".md")).is_file():
                broken.append({"file": relative.as_posix(), "target": target})
    return {"checked": checked, "broken": broken}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--vault", help="Knowledge-base directory; default: ~/Documents/个人知识库")
    parser.add_argument("--agent", choices=["codex", "claude"], help="Known local host; installs a durable personal-kb skill")
    parser.add_argument("--skills-dir", help="Actual supported skills directory; overrides --agent default")
    parser.add_argument("--agent-file", help="An explicitly selected host instruction file (AGENTS.md, CLAUDE.md, etc.)")
    parser.add_argument("--no-obsidian-config", action="store_true", help="Only when the user explicitly wants files without Obsidian settings")
    mode = parser.add_mutually_exclusive_group()
    mode.add_argument("--dry-run", action="store_true", help="Preview without writing")
    mode.add_argument("--check", action="store_true", help="Read-back and link check without writing")
    args = parser.parse_args()
    vault = absolute(args.vault).resolve() if args.vault else Path.home() / "Documents" / "个人知识库"
    if vault.exists() and not vault.is_dir():
        raise ValueError("Vault is not a directory: " + str(vault))
    if not ASSETS.is_dir():
        raise ValueError("Missing assets/vault; copy the entire skill folder")
    assets = sorted(path for path in ASSETS.rglob("*") if path.is_file())
    if not assets:
        raise ValueError("Empty assets/vault")
    legacy_file = SKILL_ROOT / "assets/legacy-v1-sha256.json"
    legacy = json.loads(legacy_file.read_text(encoding="utf-8")) if legacy_file.is_file() else {}
    missing, same, conflicts, plans = [], [], [], []
    for source in assets:
        relative = source.relative_to(ASSETS)
        target = destination(vault, relative)
        if not target.exists():
            missing.append(relative)
            plans.append({"path": target, "old": None, "data": source.read_bytes(), "kind": "vault_file"})
        elif not target.is_file():
            raise ValueError("Expected a file: " + str(target))
        elif target.read_bytes() == source.read_bytes():
            same.append(relative)
        else:
            target.read_text(encoding="utf-8-sig")
            old = target.read_bytes()
            if hashlib.sha256(old).hexdigest() == legacy.get(relative.as_posix()):
                plans.append({"path": target, "old": old, "data": source.read_bytes(), "kind": "template_upgrade"})
            else:
                conflicts.append(relative)
    obsidian_plans = [] if args.no_obsidian_config else settings_plan(vault, destination)
    plans.extend(obsidian_plans)
    skills_dir = absolute(args.skills_dir).resolve() if args.skills_dir else None
    if skills_dir is None and args.agent:
        skills_dir = Path.home() / (".agents" if args.agent == "codex" else ".claude") / "skills"
    runtime = runtime_plan(vault, skills_dir, SKILL_ROOT, destination) if skills_dir is not None else None
    if runtime:
        plans.append(runtime)
    agent_path = absolute(args.agent_file) if args.agent_file else None
    old, new, connection = None, None, "not_configured"
    if agent_path:
        # Avoid collision with a file this installation is about to create.
        if agent_path.resolve() in {(vault / p.relative_to(ASSETS)).resolve() for p in assets}:
            raise ValueError("External agent file overlaps a managed knowledge-base file")
        old, new, connection = prepare_agent_file(agent_path, vault)
        plans.append({"path": agent_path, "old": old, "data": new, "kind": "agent_instruction"})
    # Validate every planned path before creating even the first file.
    for plan in plans:
        for parent in plan["path"].parents:
            if parent.exists() and not parent.is_dir():
                raise ValueError("Parent is not a directory: " + str(parent))
        if plan["path"].is_symlink():
            raise ValueError("Refusing symlink: " + str(plan["path"]))
    report = {
        "vault": str(vault),
        "mode": "check" if args.check else ("dry_run" if args.dry_run else "install"),
        "created": [], "missing": [p.as_posix() for p in missing],
        "unchanged": len(same), "conflicts": [p.as_posix() for p in conflicts],
        "agent_file": str(agent_path) if agent_path else None,
        "agent_connection": connection,
        "runtime_skill": str(runtime["path"]) if runtime else None,
        "planned_changes": [{"path": str(p["path"]), "kind": p["kind"]} for p in plans if p["old"] != p["data"]],
        "updated": [],
        "completion": {"agent_entry": "planned" if agent_path or runtime else "not_configured", "desktop": "not_checked_by_this_script"},
    }
    if not args.dry_run and not args.check:
        for plan in plans:
            applied = apply_plan(plan)
            if applied["action"] == "created":
                try:
                    name = plan["path"].relative_to(vault).as_posix()
                except ValueError:
                    name = str(plan["path"])
                report["created"].append(name)
            elif applied["action"] == "updated":
                report["updated"].append(applied)
        report["missing"] = []
        if agent_path:
            report["agent_connection"] = "connected"
        for name in ("AGENTS.md", "知识资产工作台.md", "90-系统/维护与AI协作规则.md"):
            destination(vault, Path(name)).read_text(encoding="utf-8-sig")
        report["roundtrip"] = roundtrip(vault, destination)
    settings_missing = [str(p["path"]) for p in obsidian_plans if p["old"] != p["data"]] if args.check or args.dry_run else []
    report["obsidian_settings"] = {"status": "skipped" if args.no_obsidian_config else ("needs_configuration" if settings_missing else "configured"), "pending": settings_missing}
    if not args.dry_run:
        report["links"] = check_links(vault, [p.relative_to(ASSETS) for p in assets])
    incomplete = bool(report["missing"] or conflicts or report.get("links", {}).get("broken"))
    if args.check and any(p["old"] != p["data"] for p in plans):
        incomplete = True
    if args.check and agent_path and connection != "already_connected":
        incomplete = True
    if agent_path or runtime:
        entry_ready = (runtime is None or runtime["path"].is_file() and runtime["path"].read_bytes() == runtime["data"])
        entry_ready = entry_ready and (agent_path is None or agent_path.is_file() and agent_path.read_bytes() == new)
        report["completion"]["agent_entry"] = "configured" if entry_ready else "not_configured"
    report["status"] = ("needs_review" if conflicts else "ready_to_install") if args.dry_run else ("needs_review" if incomplete else "ok")
    if not incomplete and not args.dry_run and not (agent_path or runtime):
        report["status"] = "files_ready_agent_entry_missing"
    print(json.dumps(report, ensure_ascii=False, indent=2))
    return 2 if args.check and incomplete else 0


if __name__ == "__main__":
    try:
        sys.exit(main())
    except (OSError, ValueError) as exc:
        print(json.dumps({"status": "error", "error": str(exc)}, ensure_ascii=False), file=sys.stderr)
        sys.exit(1)
