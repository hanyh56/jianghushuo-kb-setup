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


ASSETS = Path(__file__).resolve().parent.parent / "assets" / "vault"
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
    parser.add_argument("--vault", required=True, help="Knowledge-base directory")
    parser.add_argument("--agent-file", help="An explicitly selected host instruction file (AGENTS.md, CLAUDE.md, etc.)")
    mode = parser.add_mutually_exclusive_group()
    mode.add_argument("--dry-run", action="store_true", help="Preview without writing")
    mode.add_argument("--check", action="store_true", help="Read-back and link check without writing")
    args = parser.parse_args()
    vault = absolute(args.vault).resolve()
    if vault.exists() and not vault.is_dir():
        raise ValueError("Vault is not a directory: " + str(vault))
    if not ASSETS.is_dir():
        raise ValueError("Missing assets/vault; copy the entire skill folder")
    assets = sorted(path for path in ASSETS.rglob("*") if path.is_file())
    if not assets:
        raise ValueError("Empty assets/vault")
    missing, same, conflicts = [], [], []
    for source in assets:
        relative = source.relative_to(ASSETS)
        target = destination(vault, relative)
        if not target.exists():
            missing.append(relative)
        elif not target.is_file():
            raise ValueError("Expected a file: " + str(target))
        elif target.read_bytes() == source.read_bytes():
            same.append(relative)
        else:
            target.read_text(encoding="utf-8-sig")
            conflicts.append(relative)
    agent_path = absolute(args.agent_file) if args.agent_file else None
    old, new, connection = None, None, "not_configured"
    if agent_path:
        # Avoid collision with a file this installation is about to create.
        if agent_path.resolve() in {(vault / p.relative_to(ASSETS)).resolve() for p in assets}:
            raise ValueError("External agent file overlaps a managed knowledge-base file")
        old, new, connection = prepare_agent_file(agent_path, vault)
    report = {
        "vault": str(vault),
        "mode": "check" if args.check else ("dry_run" if args.dry_run else "install"),
        "created": [], "missing": [p.as_posix() for p in missing],
        "unchanged": len(same), "conflicts": [p.as_posix() for p in conflicts],
        "agent_file": str(agent_path) if agent_path else None,
        "agent_connection": connection,
    }
    if not args.dry_run and not args.check:
        for relative in missing:
            target = destination(vault, relative)
            target.parent.mkdir(parents=True, exist_ok=True)
            expected = (ASSETS / relative).read_bytes()
            with target.open("xb") as stream:
                stream.write(expected)
            if hashlib.sha256(target.read_bytes()).digest() != hashlib.sha256(expected).digest():
                raise ValueError("Read-back mismatch: " + str(target))
            report["created"].append(relative.as_posix())
        report["missing"] = []
        if agent_path and old != new:
            agent_path.parent.mkdir(parents=True, exist_ok=True)
            if old is None:
                with agent_path.open("xb") as stream:
                    stream.write(new)
            else:
                # Append only, leaving every byte of the existing instructions intact.
                with agent_path.open("r+b") as stream:
                    if stream.read() != old:
                        raise ValueError("Agent file changed during setup; rerun")
                    stream.seek(0, 2)
                    stream.write(new[len(old):])
            if agent_path.read_bytes() != new:
                raise ValueError("Agent entry read-back mismatch")
            report["agent_connection"] = "connected"
        for name in ("AGENTS.md", "知识资产工作台.md", "90-系统/维护与AI协作规则.md"):
            destination(vault, Path(name)).read_text(encoding="utf-8-sig")
    if not args.dry_run:
        report["links"] = check_links(vault, [p.relative_to(ASSETS) for p in assets])
    incomplete = bool(report["missing"] or conflicts or report.get("links", {}).get("broken"))
    if args.check and agent_path and connection != "already_connected":
        incomplete = True
    report["status"] = ("needs_review" if conflicts else "ready_to_install") if args.dry_run else ("needs_review" if incomplete else "ok")
    print(json.dumps(report, ensure_ascii=False, indent=2))
    return 2 if args.check and incomplete else 0


if __name__ == "__main__":
    try:
        sys.exit(main())
    except (OSError, ValueError) as exc:
        print(json.dumps({"status": "error", "error": str(exc)}, ensure_ascii=False), file=sys.stderr)
        sys.exit(1)
