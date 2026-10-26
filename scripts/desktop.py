#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Detect, install from the official release, and open Obsidian. Standard library only."""

import argparse
import hashlib
import json
import ntpath
import os
from pathlib import Path
import platform
import re
import shutil
import subprocess
import sys
import tempfile
import urllib.parse
import urllib.request
import uuid

for stream in (sys.stdout, sys.stderr):
    if hasattr(stream, "reconfigure"):
        stream.reconfigure(encoding="utf-8")


RELEASE_API = "https://api.github.com/repos/obsidianmd/obsidian-releases/releases/latest"
DOWNLOAD_PAGE = "https://obsidian.md/download"


def registry_path(system, home):
    if system == "Darwin":
        return home / "Library/Application Support/obsidian/obsidian.json"
    if system == "Windows":
        return Path(os.environ.get("APPDATA", str(home / "AppData/Roaming"))) / "obsidian/obsidian.json"
    return Path(os.environ.get("XDG_CONFIG_HOME", str(home / ".config"))) / "obsidian/obsidian.json"


def find_app(system, home):
    if system == "Darwin":
        for app in (Path("/Applications/Obsidian.app"), home / "Applications/Obsidian.app"):
            if (app / "Contents/MacOS/Obsidian").is_file():
                return ["open", "-a", str(app)]
    elif system == "Windows":
        folders = [Path(os.environ.get("LOCALAPPDATA", str(home / "AppData/Local"))) / "Programs",
                   Path(os.environ.get("PROGRAMFILES", "C:/Program Files")),
                   Path(os.environ.get("PROGRAMFILES(X86)", "C:/Program Files (x86)"))]
        for folder in folders:
            for name in ("Obsidian", "obsidian"):
                app = folder / name / "Obsidian.exe"
                if app.is_file():
                    return [str(app)]
    else:
        app = shutil.which("obsidian")
        if app:
            return [app]
        app = home / ".local/opt/obsidian/Obsidian.AppImage"
        if app.is_file():
            return [str(app)]
        flatpak = shutil.which("flatpak")
        if flatpak:
            result = subprocess.run([flatpak, "info", "md.obsidian.Obsidian"], capture_output=True, timeout=10)
            if result.returncode == 0:
                return [flatpak, "run", "md.obsidian.Obsidian"]
    executable = shutil.which("Obsidian.exe" if system == "Windows" else "obsidian")
    return [executable] if executable else None


def doctor():
    system, home = platform.system(), Path.home()
    registry = registry_path(system, home)
    vaults = []
    error = None
    if registry.is_file():
        try:
            entries = json.loads(registry.read_text(encoding="utf-8-sig")).get("vaults", {})
            for identifier, entry in entries.items():
                if isinstance(entry, dict) and isinstance(entry.get("path"), str):
                    vaults.append({"id": identifier, "path": entry["path"]})
        except (OSError, ValueError, AttributeError) as exc:
            error = str(exc)
    command = find_app(system, home)
    desktop = system in ("Darwin", "Windows") or bool(os.environ.get("DISPLAY") or os.environ.get("WAYLAND_DISPLAY"))
    return {"system": system, "architecture": platform.machine(), "installed": bool(command),
            "launch_command": command, "desktop_session_detected": desktop,
            "default_vault": str(home / "Documents/个人知识库"),
            "vault_registry_path": str(registry),
            "registered_vaults": vaults, "registry_read_error": error,
            "official_download": DOWNLOAD_PAGE}


def select_asset(release, system, machine):
    if system == "Darwin":
        pattern = r"Obsidian-[0-9][^/]*\.dmg"
    elif system == "Windows":
        pattern = r"Obsidian-[0-9][^/]*\.exe"
    elif system == "Linux" and machine.lower() in ("aarch64", "arm64"):
        pattern = r"Obsidian-[0-9][^/]*-arm64\.AppImage"
    elif system == "Linux" and machine.lower() in ("x86_64", "amd64"):
        pattern = r"Obsidian-[0-9][0-9.]*\.AppImage"
    else:
        raise ValueError("Unsupported desktop/architecture; use official download page: " + DOWNLOAD_PAGE)
    matches = [item for item in release.get("assets", []) if re.fullmatch(pattern, item.get("name", ""))]
    if len(matches) != 1:
        raise ValueError("No unique official installer matched; inspect " + DOWNLOAD_PAGE)
    asset = matches[0]
    parsed = urllib.parse.urlparse(asset["browser_download_url"])
    if parsed.scheme != "https" or parsed.netloc != "github.com" or not parsed.path.startswith("/obsidianmd/obsidian-releases/releases/download/"):
        raise ValueError("Unexpected installer source")
    if not re.fullmatch(r"sha256:[0-9a-fA-F]{64}", asset.get("digest") or ""):
        raise ValueError("Official release has no SHA-256 digest; use the official graphical installer instead")
    return asset


def request(url):
    return urllib.request.urlopen(urllib.request.Request(url, headers={"User-Agent": "jianghushuo-kb-setup", "Accept": "application/vnd.github+json"}), timeout=30)


def download(asset, directory):
    directory.mkdir(parents=True, exist_ok=True)
    path = directory / asset["name"]
    wanted = asset["digest"].split(":", 1)[1].lower()
    if path.exists():
        if not path.is_file() or hashlib.sha256(path.read_bytes()).hexdigest() != wanted:
            raise ValueError("Existing download differs; preserve it and use another download directory: " + str(path))
        return path
    partial = path.with_name(path.name + ".part-" + uuid.uuid4().hex)
    digest = hashlib.sha256()
    try:
        with request(asset["browser_download_url"]) as response, partial.open("xb") as output:
            while True:
                chunk = response.read(1024 * 1024)
                if not chunk:
                    break
                digest.update(chunk)
                output.write(chunk)
        if digest.hexdigest() != wanted:
            raise ValueError("Downloaded installer SHA-256 does not match the official release")
        # Do not replace a file that appeared while downloading.
        with path.open("xb") as output, partial.open("rb") as source:
            shutil.copyfileobj(source, output)
    finally:
        if partial.exists():
            partial.unlink()
    return path


def run(command, timeout=120):
    result = subprocess.run(command, capture_output=True, text=True, timeout=timeout)
    if result.returncode:
        raise ValueError("Command failed: " + command[0] + ": " + (result.stderr or result.stdout).strip()[-1000:])


def install(info, directory):
    if info["installed"]:
        return {"status": "already_installed", "downloaded": False, "app": info["launch_command"]}
    if not info["desktop_session_detected"]:
        return {"status": "needs_user_desktop", "official_download": DOWNLOAD_PAGE}
    with request(RELEASE_API) as response:
        release = json.load(response)
    asset = select_asset(release, info["system"], info["architecture"])
    package = download(asset, directory)
    if info["system"] == "Darwin":
        target = Path.home() / "Applications/Obsidian.app"
        if target.exists():
            raise ValueError("Existing app directory is incomplete; preserve it and inspect: " + str(target))
        target.parent.mkdir(parents=True, exist_ok=True)
        with tempfile.TemporaryDirectory(prefix="jhs-obsidian-mount-") as mount:
            run(["hdiutil", "attach", "-readonly", "-nobrowse", "-mountpoint", mount, str(package)])
            try:
                source = Path(mount) / "Obsidian.app"
                if not (source / "Contents/MacOS/Obsidian").is_file():
                    raise ValueError("Official disk image does not contain the expected application")
                run(["codesign", "--verify", "--deep", "--strict", str(source)])
                # Reserve a new destination; never overwrite another application.
                target.mkdir()
                try:
                    run(["ditto", str(source), str(target)])
                except Exception:
                    shutil.rmtree(target)  # Only the incomplete directory created by this operation.
                    raise
            finally:
                run(["hdiutil", "detach", mount])
        status = "installed"
    elif info["system"] == "Windows":
        subprocess.Popen([str(package)], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        status = "installer_launched_finish_in_gui"
    else:
        target = Path.home() / ".local/opt/obsidian/Obsidian.AppImage"
        target.parent.mkdir(parents=True, exist_ok=True)
        with target.open("xb") as output, package.open("rb") as source:
            shutil.copyfileobj(source, output)
        target.chmod(target.stat().st_mode | 0o100)
        status = "installed"
    return {"status": status, "downloaded": str(package), "sha256_verified": True}


def same_vault_path(stored, requested, system):
    """Compare Windows paths using Windows rules, including in cross-platform tests."""
    if system == "Windows":
        if os.name == "nt":
            stored, requested = str(Path(stored).resolve()), str(Path(requested).resolve())
        return ntpath.normcase(ntpath.normpath(str(stored))) == ntpath.normcase(ntpath.normpath(str(requested)))
    return Path(stored).resolve() == Path(requested).resolve()


def open_plan(info, vault, recover_vault_not_found=False):
    if not info["installed"]:
        return {"status": "needs_installation", "complete": False, "official_download": DOWNLOAD_PAGE}
    if not info.get("desktop_session_detected", True):
        return {"status": "needs_user_desktop", "complete": False, "vault": str(vault)}
    registry_error = info.get("registry_read_error")
    matched = None if registry_error else next((item for item in info["registered_vaults"]
        if same_vault_path(item["path"], vault, info.get("system", platform.system()))), None)
    if recover_vault_not_found:
        matched = None  # A previous URI failure invalidates the cached registration assumption.
    if matched:
        uri = "obsidian://open?" + urllib.parse.urlencode({"vault": matched["id"], "file": "知识资产工作台.md"})
        status = "open_dispatched_ui_confirmation_required"
    else:
        uri = "obsidian://choose-vault"
        status = "needs_registry_check" if registry_error else "needs_vault_registration"
    return {"status": status, "command": info["launch_command"] + [uri],
            "complete": False, "workbench_visible": "not_verified",
            "registered": True if matched else (None if registry_error or recover_vault_not_found else False),
            "vault_registry_path": info.get("vault_registry_path"), "registry_read_error": registry_error,
            "recovering_vault_not_found": recover_vault_not_found,
            "vault": str(vault), "folder_to_select": None if matched else str(vault),
            "next": "Confirm the workbench is visible" if matched else "Dismiss any error, choose Open folder as vault / 打开本地仓库, select folder_to_select, then rerun open",
            "registration_method": "existing_vault_id" if matched else "vault_manager_folder_picker"}


def dispatch(info, plan):
    """Dispatch only a planned action; a successful launch never proves GUI completion."""
    if plan.get("command"):
        if info["system"] == "Darwin":
            run(plan["command"], timeout=30)
        else:
            subprocess.Popen(plan["command"], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("action", choices=["doctor", "install", "open"])
    parser.add_argument("--vault")
    parser.add_argument("--download-dir", help="Default: ~/Downloads/Obsidian-knowledge-base-setup")
    parser.add_argument("--dry-run", action="store_true", help="For open: show the exact launch plan without opening the app")
    parser.add_argument("--recover-vault-not-found", action="store_true", help="For open: recover a failed URI by opening the vault manager; never repeat open?path=")
    args = parser.parse_args()
    if args.recover_vault_not_found and args.action != "open":
        raise ValueError("--recover-vault-not-found requires open")
    info = doctor()
    if args.action == "doctor":
        result = info
    elif args.action == "install":
        if args.dry_run:
            raise ValueError("Use doctor for an installation preflight; --dry-run is for open")
        directory = Path(args.download_dir).expanduser().resolve() if args.download_dir else Path.home() / "Downloads/Obsidian-knowledge-base-setup"
        result = install(info, directory)
    else:
        if not args.vault:
            raise ValueError("open requires --vault")
        vault = Path(args.vault).expanduser().resolve()
        if not (vault / "知识资产工作台.md").is_file():
            raise ValueError("Workbench not found in the selected vault")
        result = open_plan(info, vault, args.recover_vault_not_found)
        if not args.dry_run:
            dispatch(info, result)
    print(json.dumps(result, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    try:
        main()
    except (OSError, ValueError, subprocess.SubprocessError) as exc:
        print(json.dumps({"status": "error", "error": str(exc), "official_download": DOWNLOAD_PAGE}, ensure_ascii=False), file=sys.stderr)
        sys.exit(1)
