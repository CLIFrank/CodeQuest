# -*- mode: python ; coding: utf-8 -*-
"""Cross-platform, onedir PyInstaller build for CodeQuest."""

from pathlib import Path
import sys

from PyInstaller.utils.hooks import collect_submodules


project_root = Path(SPECPATH)
version_file = project_root / "packaging" / "version_info.txt"

a = Analysis(
    [str(project_root / "main.py")],
    pathex=[str(project_root)],
    binaries=[],
    datas=[],
    hiddenimports=collect_submodules("codequest"),
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=["tkinter", "unittest"],
    noarchive=False,
    optimize=1,
)

pyz = PYZ(a.pure)

exe_options = {
    "name": "CodeQuest",
    "debug": False,
    "bootloader_ignore_signals": False,
    "strip": False,
    "upx": True,
    "console": False,
    "disable_windowed_traceback": False,
    "argv_emulation": False,
    "target_arch": None,
    "codesign_identity": None,
    "entitlements_file": None,
}
if sys.platform == "win32":
    exe_options["version"] = str(version_file)

exe = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,
    **exe_options,
)

collection = COLLECT(
    exe,
    a.binaries,
    a.datas,
    strip=False,
    upx=True,
    upx_exclude=[],
    name="CodeQuest",
)

if sys.platform == "darwin":
    app = BUNDLE(
        collection,
        name="CodeQuest.app",
        bundle_identifier="io.codequest.learn",
        info_plist={
            "CFBundleDisplayName": "CodeQuest",
            "CFBundleShortVersionString": "1.0.0",
            "NSHighResolutionCapable": True,
        },
    )
