"""Verify CRC, SHA-256 manifests and disk/ZIP identity for H440 B1 deliverables."""
from __future__ import annotations

import hashlib
import zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parent
OUT = ROOT / "H440_B1"


def sha(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def verify(archive: Path, expected_steps: int, expected_dxfs: int) -> None:
    with zipfile.ZipFile(archive) as zf:
        if bad := zf.testzip():
            raise RuntimeError(f"{archive.name}: CRC failure in {bad}")
        names = zf.namelist()
        if len([n for n in names if n.startswith("STEP/")]) != expected_steps:
            raise RuntimeError(f"{archive.name}: STEP count mismatch")
        if len([n for n in names if n.startswith("DXF/")]) != expected_dxfs:
            raise RuntimeError(f"{archive.name}: DXF count mismatch")
        manifest = zf.read("SHA256SUMS.txt").decode("utf-8").splitlines()
        for line in manifest:
            expected, name = line.split("  ", 1)
            data = zf.read(name)
            if sha(data) != expected:
                raise RuntimeError(f"{archive.name}: SHA-256 mismatch in {name}")
            disk_name = name.split("/", 1)[-1]
            disk = OUT / disk_name
            if disk.is_file() and disk.read_bytes() != data:
                raise RuntimeError(f"{archive.name}: ZIP differs from disk for {disk_name}")
    print(
        f"OK {archive.name}: entries={len(names)}, sha256={sha(archive.read_bytes())}"
    )


verify(OUT / "H440_B1_supplier_DXF_STEP.zip", expected_steps=7, expected_dxfs=7)
verify(OUT / "H440_B1_printed_parts_STEP.zip", expected_steps=19, expected_dxfs=0)
