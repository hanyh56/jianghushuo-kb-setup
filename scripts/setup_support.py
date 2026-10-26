# -*- coding: utf-8 -*-
"""Local settings, durable Agent entry, and a reversible installation probe."""

import hashlib
import json
from pathlib import Path
import uuid


SETTINGS = {
    "app.json": {"alwaysUpdateLinks": True, "newFileLocation": "folder", "newFileFolderPath": "00-灵感与收件箱"},
    "templates.json": {"folder": "90-系统/模板", "dateFormat": "YYYY-MM-DD", "timeFormat": "HH:mm"},
    "daily-notes.json": {"folder": "02-Areas-长期领域/每日记录", "format": "YYYY-MM-DD", "template": "90-系统/模板/模板-每日进度"},
}
CORE = ["file-explorer", "global-search", "switcher", "command-palette", "backlink", "properties", "templates", "daily-notes", "bases"]


def encoded_json(value):
    return (json.dumps(value, ensure_ascii=False, indent=2) + "\n").encode("utf-8")


def settings_plan(vault, destination):
    plans = []
    for name, wanted in SETTINGS.items():
        path = destination(vault, Path(".obsidian") / name)
        old = path.read_bytes() if path.exists() else None
        existing = json.loads(old.decode("utf-8-sig")) if old is not None else {}
        if not isinstance(existing, dict):
            raise ValueError("Invalid Obsidian settings object: " + str(path))
        new = dict(existing)
        new.update(wanted)
        # Preserve formatting, BOM and every byte when desired values already match.
        data = old if old is not None and existing == new else encoded_json(new)
        plans.append({"path": path, "old": old, "data": data, "kind": "obsidian_setting"})
    path = destination(vault, Path(".obsidian/core-plugins.json"))
    old = path.read_bytes() if path.exists() else None
    existing = json.loads(old.decode("utf-8-sig")) if old is not None else {}
    if isinstance(existing, list) and all(isinstance(item, str) for item in existing):
        new = existing + [item for item in CORE if item not in existing]
    elif isinstance(existing, dict):
        new = dict(existing)
        new.update({item: True for item in CORE})
    else:
        raise ValueError("Invalid core-plugins.json; expected string list or object")
    data = old if old is not None and new == existing else encoded_json(new)
    plans.append({"path": path, "old": old, "data": data, "kind": "obsidian_setting"})
    return plans


def runtime_plan(vault, skills_dir, skill_root, destination):
    path = destination(skills_dir, Path("personal-kb/SKILL.md"))
    template = (skill_root / "assets/runtime-skill.md").read_text(encoding="utf-8")
    data = template.replace("{{VAULT_PATH_JSON}}", json.dumps(str(vault), ensure_ascii=False)).encode("utf-8")
    old = path.read_bytes() if path.exists() else None
    if old is not None and old != data:
        raise ValueError("personal-kb already exists with different content; preserve it and reconcile its vault path: " + str(path))
    return {"path": path, "old": old, "data": data, "kind": "runtime_skill"}


def apply_plan(plan):
    path, old, data = plan["path"], plan["old"], plan["data"]
    if old == data:
        return {"path": str(path), "action": "unchanged"}
    path.parent.mkdir(parents=True, exist_ok=True)
    current = path.read_bytes() if path.exists() else None
    if current != old:
        raise ValueError("File changed during installation; retry after inspection: " + str(path))
    backup = None
    if old is not None:
        backup = path.with_name(path.name + ".jhs-backup-" + hashlib.sha256(old).hexdigest()[:12])
        if backup.is_symlink():
            raise ValueError("Refusing symlink backup: " + str(backup))
        if backup.exists():
            if backup.read_bytes() != old:
                raise ValueError("Backup collision: " + str(backup))
        else:
            with backup.open("xb") as stream:
                stream.write(old)
        # Replace atomically after preserving the old bytes.
        temporary = path.with_name(path.name + ".jhs-tmp-" + uuid.uuid4().hex)
        try:
            with temporary.open("xb") as stream:
                stream.write(data)
            temporary.replace(path)
        finally:
            if temporary.exists():
                temporary.unlink()
    else:
        with path.open("xb") as stream:
            stream.write(data)
    if path.read_bytes() != data:
        raise ValueError("Read-back mismatch: " + str(path))
    return {"path": str(path), "action": "created" if old is None else "updated", "backup": str(backup) if backup else None}


def roundtrip(vault, destination):
    identifier = uuid.uuid4().hex
    path = destination(vault, Path("00-灵感与收件箱") / ("_安装验收-" + identifier + ".md"))
    content = "# 临时安装验收\n\n这是安装器生成的测试数据，不是本人的经历或项目。\n\n检索标记：" + identifier + "\n"
    created = False
    try:
        with path.open("x", encoding="utf-8") as stream:
            created = True
            stream.write(content)
        readback = path.read_text(encoding="utf-8")
        if readback != content or identifier not in readback:
            raise ValueError("Knowledge-base write/read/search probe failed")
    finally:
        if created and path.exists():
            path.unlink()
    return {"write": "passed", "read": "passed", "retrieval": "passed", "probe_removed": not path.exists()}
