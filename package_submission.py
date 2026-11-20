"""Build a portable ZIP from the current source tree with a content manifest."""
import hashlib
import json
from pathlib import Path
from tempfile import NamedTemporaryFile
from zipfile import ZIP_DEFLATED, ZipFile, ZipInfo

ROOT = Path(__file__).resolve().parent
OUTPUT = ROOT / "dist" / "Casegraph-submission.zip"


def source_files():
    patterns = ("*.py", "*.md", "*.csv", "requirements.txt", "demo-report.txt", "static/*",
                "lead_cases/*.json", "validation/*.py", "validation/*.json", "tests/*.py",
                "third_party/*.txt", "training/*.py", "training/*.cfg", "training/*.json",
                "training/data/*", "training/run/model-best/**/*")
    return sorted({file for pattern in patterns for file in ROOT.glob(pattern) if file.is_file()
                   and not file.name.startswith(".")})


def build():
    OUTPUT.parent.mkdir(exist_ok=True)
    manifest = {}

    def entry(archive, name, data):
        info = ZipInfo("Casegraph/" + name)
        info.compress_type = ZIP_DEFLATED
        info.external_attr = 0o100644 << 16
        archive.writestr(info, data)

    with NamedTemporaryFile(dir=OUTPUT.parent, delete=False) as handle:
        tmp = Path(handle.name)
    try:
        with ZipFile(tmp, "w") as archive:
            for file in source_files():
                name = file.relative_to(ROOT).as_posix()
                data = file.read_bytes()
                manifest[name] = hashlib.sha256(data).hexdigest()
                entry(archive, name, data)
            entry(archive, "MANIFEST.json", json.dumps(manifest, indent=2).encode())
        tmp.replace(OUTPUT)
    finally:
        tmp.unlink(missing_ok=True)
    return OUTPUT


if __name__ == "__main__":
    print(build())
