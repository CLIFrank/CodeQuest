# CodeQuest release packaging

CodeQuest uses a PyInstaller **onedir** build. This starts faster and produces
fewer antivirus false positives than a self-extracting onefile executable.
The release helper wraps the resulting folder in a versioned ZIP.

## Local Windows build

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt -r requirements-dev.txt
python -m PyInstaller --clean --noconfirm CodeQuest.spec
python packaging\run_frozen_self_test.py --executable .\dist\CodeQuest\CodeQuest.exe
python packaging\package_release.py --label Windows-x64
```

The distributable file will be written to `release-assets/`.

## Automated builds

`.github/workflows/release.yml` builds Windows, Linux, and macOS packages.

- Run it manually from the GitHub Actions page to download test artifacts.
- Push a version tag such as `v1.0.0` to build all platforms and publish a
  GitHub Release automatically.
- PyInstaller must build on each target operating system; the workflow matrix
  provides the correct native runner for every package.

## Release checklist

1. Confirm that `LICENSE` still identifies the intended copyright holder.
2. Update `codequest.__version__`, `packaging/version_info.txt`, and the macOS
   version in `CodeQuest.spec`.
3. Run the unit tests and frozen self-test.
4. Test the ZIP on a separate Windows account or clean virtual machine.
5. Tag the release: `git tag v1.0.0` and `git push origin v1.0.0`.
6. Download the three generated archives from the GitHub Release.
7. Upload the same archives to an itch.io project marked as Downloadable.
8. Mark each itch.io upload with its correct Windows, Linux, or macOS platform.
9. Add screenshots, controls, minimum requirements, and a link to the privacy
   note explaining that progress is stored locally.
10. Publish the SHA-256 checksum beside every download.

Unsigned Windows and macOS applications may show operating-system reputation
warnings. Code signing removes most warnings but is not generally free; the
free release should clearly identify the publisher and include checksums.
