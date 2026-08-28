#!/usr/bin/env python3

import base64
import csv
import hashlib
import importlib.metadata
import subprocess
import sys
from pathlib import Path


REQUIREMENTS = Path(__file__).resolve().parents[1] / "requirements.txt"
MAIN_LOG = Path(__file__).resolve().parents[1] / "ramdisk" / "main.log"


def write_log(message: str = "") -> None:
    MAIN_LOG.parent.mkdir(parents=True, exist_ok=True)
    with MAIN_LOG.open("a", encoding="utf-8") as log_file:
        log_file.write(f"{message}\n")


def check_packages() -> dict[str, list[str]]:
    """Check installed package files against their RECORD hashes."""
    broken = {}

    for dist in importlib.metadata.distributions():
        package = f"{dist.metadata['Name']}=={dist.version}"
        record = dist.read_text("RECORD")

        if not record:
            continue

        for row in csv.reader(record.splitlines()):
            if len(row) < 3 or not row[1] or not row[2]:
                continue

            path = Path(dist.locate_file(row[0]))

            if not path.is_file():
                broken.setdefault(package, []).append(str(path))
                continue

            try:
                algorithm, expected_hash = row[1].split("=", 1)
                digest = hashlib.new(algorithm, path.read_bytes()).digest()
            except ValueError:
                broken.setdefault(package, []).append(str(path))
                continue
            actual_hash = (
                base64.urlsafe_b64encode(digest)
                .rstrip(b"=")
                .decode()
            )

            if actual_hash != expected_hash:
                broken.setdefault(package, []).append(str(path))

    return broken


def install_requirements() -> None:
    subprocess.run(
        [
            sys.executable,
            "-m",
            "pip3",
            "install",
            "--only-binary",
            ":all:",
            "-r",
            str(REQUIREMENTS),
        ],
        check=True,
    )


def reinstall(packages: set[str]) -> None:
    if not packages:
        return

    subprocess.run(
        [
            sys.executable,
            "-m",
            "pip3",
            "install",
            "--only-binary",
            ":all:",
            "--force-reinstall",
            *sorted(packages),
        ],
        check=True,
    )


def print_broken(broken: dict[str, list[str]]) -> None:
    for package, files in sorted(broken.items()):
        write_log(f"CORRUPT: {package}")
        for path in files:
            write_log(f"  {path}")


def main() -> int:
    write_log("Installing Python packages...")
    install_requirements()

    write_log("Checking package integrity...")
    broken = check_packages()

    if not broken:
        write_log("All packages are intact.")
        return 0

    write_log("\nCorrupted packages:")
    print_broken(broken)

    write_log("\nReinstalling corrupted packages...")
    reinstall(set(broken))

    write_log("\nChecking package integrity after reinstall...")
    broken = check_packages()

    if broken:
        write_log("\nERROR: The following packages are still corrupted:")
        print_broken(broken)
        return 1

    write_log("All packages are intact after reinstall.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
