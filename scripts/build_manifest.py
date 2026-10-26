#!/usr/bin/env python3
"""Refresh the manual-install file manifest after editing bundled vault assets."""
import hashlib
import json
from pathlib import Path

root = Path(__file__).resolve().parent.parent
vault = root / "assets/vault"
manifest = [
    {"path": path.relative_to(vault).as_posix(), "sha256": hashlib.sha256(path.read_bytes()).hexdigest()}
    for path in sorted(vault.rglob("*")) if path.is_file()
]
(root / "assets/vault-manifest.json").write_text(json.dumps(manifest, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
print("Updated manifest: " + str(len(manifest)) + " files")
