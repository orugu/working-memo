from __future__ import annotations

import platform
import subprocess
import sys
import tempfile
import urllib.request
import json
from pathlib import Path

from PySide6.QtCore import QObject, QRunnable, QThreadPool, Signal, Slot

from memo_app import __version__

GITHUB_OWNER = "orugu"
GITHUB_REPO  = "working-memo"
_API_URL     = f"https://api.github.com/repos/{GITHUB_OWNER}/{GITHUB_REPO}/releases/latest"
_HEADERS     = {"Accept": "application/vnd.github.v3+json", "User-Agent": "WorkingMemo"}


def _version_tuple(v: str) -> tuple[int, ...]:
    try:
        return tuple(int(x) for x in v.lstrip("v").split("."))
    except ValueError:
        return (0,)


def _is_newer(remote: str, local: str) -> bool:
    return _version_tuple(remote) > _version_tuple(local)


def _asset_url(assets: list[dict]) -> str | None:
    system = platform.system()
    for asset in assets:
        name: str = asset["name"].lower()
        if system == "Windows" and name.endswith("-windows.exe"):
            return asset["browser_download_url"]
        if system == "Darwin" and name.endswith("-macos.tar.gz"):
            return asset["browser_download_url"]
    return None


# ── Checker ───────────────────────────────────────────────────────────────────

class UpdateChecker(QObject):
    """GitHub Releases에서 최신 버전을 확인한다. 결과는 Qt Signal로 반환."""

    update_available = Signal(str, str)  # (new_version, download_url)
    up_to_date       = Signal()
    check_failed     = Signal(str)

    download_progress = Signal(int, int)  # (downloaded_bytes, total_bytes)
    download_done     = Signal(str)       # temp file path
    download_failed   = Signal(str)

    def check_async(self):
        QThreadPool.globalInstance().start(_CheckWorker(self))

    def download_async(self, url: str):
        QThreadPool.globalInstance().start(_DownloadWorker(self, url))

    def apply_update(self, file_path: str):
        if platform.system() == "Windows":
            _apply_windows(file_path)
        elif platform.system() == "Darwin":
            _apply_macos(file_path)


class _CheckWorker(QRunnable):
    def __init__(self, checker: UpdateChecker):
        super().__init__()
        self._c = checker
        self.setAutoDelete(True)

    @Slot()
    def run(self):
        try:
            req = urllib.request.Request(_API_URL, headers=_HEADERS)
            with urllib.request.urlopen(req, timeout=10) as resp:
                data: dict = json.loads(resp.read())

            latest  = data["tag_name"].lstrip("v")
            assets  = data.get("assets", [])
            url     = _asset_url(assets)

            if _is_newer(latest, __version__) and url:
                self._c.update_available.emit(latest, url)
            else:
                self._c.up_to_date.emit()
        except Exception as e:
            self._c.check_failed.emit(str(e))


class _DownloadWorker(QRunnable):
    def __init__(self, checker: UpdateChecker, url: str):
        super().__init__()
        self._c   = checker
        self._url = url
        self.setAutoDelete(True)

    @Slot()
    def run(self):
        try:
            suffix = ".exe" if platform.system() == "Windows" else ".tar.gz"
            tmp = tempfile.mktemp(suffix=suffix, prefix="WorkingMemo_update_")

            def _hook(blocks, block_size, total):
                downloaded = min(blocks * block_size, total if total > 0 else blocks * block_size)
                self._c.download_progress.emit(downloaded, max(total, 0))

            urllib.request.urlretrieve(self._url, tmp, reporthook=_hook)
            self._c.download_done.emit(tmp)
        except Exception as e:
            self._c.download_failed.emit(str(e))


# ── Apply helpers ─────────────────────────────────────────────────────────────

def _current_exe() -> Path:
    """실행 중인 exe/app 경로를 반환 (frozen 여부 무관)."""
    if getattr(sys, "frozen", False):
        return Path(sys.executable).resolve()
    return Path(sys.argv[0]).resolve()


def _apply_windows(file_path: str):
    current = _current_exe()
    new_exe = Path(file_path)

    bat = Path(tempfile.mktemp(suffix=".bat", prefix="wm_update_"))
    bat.write_text(
        f"@echo off\n"
        f"ping -n 3 127.0.0.1 >nul\n"
        f"move /y \"{new_exe}\" \"{current}\"\n"
        f"start \"\" \"{current}\"\n"
        f"del \"%~f0\"\n",
        encoding="utf-8",
    )
    subprocess.Popen(
        ["cmd", "/c", str(bat)],
        creationflags=subprocess.CREATE_NO_WINDOW | subprocess.DETACHED_PROCESS,
    )
    sys.exit(0)


def _apply_macos(file_path: str):
    current = _current_exe()
    if getattr(sys, "frozen", False):
        # sys.executable = WorkingMemo.app/Contents/MacOS/WorkingMemo
        app_path = current.parent.parent.parent  # .app bundle root
    else:
        app_path = Path("/Applications/WorkingMemo.app")

    dest_dir = str(app_path.parent)
    sh = Path(tempfile.mktemp(suffix=".sh", prefix="wm_update_"))
    sh.write_text(
        f"#!/bin/bash\n"
        f"sleep 2\n"
        f"tar -xzf \"{file_path}\" -C \"{dest_dir}/\"\n"
        f"open \"{app_path}\"\n"
        f"rm -f \"{file_path}\" \"$0\"\n",
    )
    sh.chmod(0o755)
    subprocess.Popen(["/bin/bash", str(sh)])
    sys.exit(0)
