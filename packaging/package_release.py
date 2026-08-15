"""Create a versioned ZIP from a completed PyInstaller distribution."""

from __future__ import annotations

import argparse
import sys
import zipfile
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT))
RELEASE_DOCUMENTS = ("README.md", "PRIVACY.md", "CHANGELOG.md", "LICENSE")

from codequest import __version__  # noqa: E402


def add_tree(archive: zipfile.ZipFile, source: Path, archive_root: str) -> None:
    for path in sorted(source.rglob("*")):
        if path.is_file():
            relative = path.relative_to(source)
            archive.write(path, Path(archive_root) / relative)


def package(label: str, output_dir: Path) -> Path:
    dist = PROJECT_ROOT / "dist"
    app_bundle = dist / "CodeQuest.app"
    folder = dist / "CodeQuest"
    if app_bundle.exists():
        source = app_bundle
        archive_root = app_bundle.name
    elif folder.exists():
        source = folder
        archive_root = folder.name
    else:
        raise FileNotFoundError("No dist/CodeQuest or dist/CodeQuest.app build was found")

    output_dir.mkdir(parents=True, exist_ok=True)
    destination = output_dir / f"CodeQuest-{__version__}-{label}.zip"
    with zipfile.ZipFile(destination, "w", zipfile.ZIP_DEFLATED, compresslevel=9) as archive:
        add_tree(archive, source, archive_root)
        for name in RELEASE_DOCUMENTS:
            document = PROJECT_ROOT / name
            if not document.is_file():
                raise FileNotFoundError(document)
            archive.write(document, Path(archive_root) / name)
    return destination


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--label", required=True, help="Release label, e.g. Windows-x64")
    parser.add_argument("--output-dir", type=Path, default=PROJECT_ROOT / "release-assets")
    args = parser.parse_args()
    result = package(args.label, args.output_dir.resolve())
    print(result)


if __name__ == "__main__":
    main()
