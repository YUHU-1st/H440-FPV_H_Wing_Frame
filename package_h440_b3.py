"""Create deterministic current-file manufacturing archives for H440 B3."""
from __future__ import annotations

import hashlib
import zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parent
OUT = ROOT / "H440_B3"
PRINT_ARCHIVE = OUT / "H440_B3_printed_parts_STEP.zip"
PRINT_README = OUT / "打印件STEP交付说明.md"
PRINT_README_EN = OUT / "PRINTED_STEP_NOTES_EN.md"
SUPPLIER_ARCHIVE = OUT / "H440_B3_supplier_DXF_STEP.zip"
SUPPLIER_README = OUT / "供应商交付说明.md"
SUPPLIER_README_EN = OUT / "CFRP_SUPPLIER_NOTES_EN.md"
FIXED_TIME = (2026, 9, 12, 0, 0, 0)


def digest(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def write_archive(archive: Path, payloads: list[tuple[str, bytes]]) -> None:
    manifest = "".join(
        f"{digest(data)}  {name}\n" for name, data in payloads
    ).encode("utf-8")
    payloads = payloads + [("SHA256SUMS.txt", manifest)]
    with zipfile.ZipFile(archive, "w", compression=zipfile.ZIP_DEFLATED, compresslevel=9) as zf:
        for name, data in payloads:
            info = zipfile.ZipInfo(name, FIXED_TIME)
            info.compress_type = zipfile.ZIP_DEFLATED
            info.external_attr = 0o100644 << 16
            zf.writestr(info, data)
    with zipfile.ZipFile(archive, "r") as zf:
        if bad := zf.testzip():
            raise RuntimeError(f"CRC failure: {bad}")
    print(f"{archive.name}: {archive.stat().st_size} bytes, sha256={digest(archive.read_bytes())}")


print_files = sorted(OUT.glob("P*.step")) + sorted(OUT.glob("W*.step"))
if len(print_files) != 18:
    raise RuntimeError(f"expected 18 printed-part STEP files, found {len(print_files)}")
for note in (PRINT_README, PRINT_README_EN):
    if not note.is_file():
        raise FileNotFoundError(note)
print_payloads = [(f"STEP/{p.name}", p.read_bytes()) for p in print_files]
print_payloads.append((PRINT_README.name, PRINT_README.read_bytes()))
print_payloads.append((PRINT_README_EN.name, PRINT_README_EN.read_bytes()))
write_archive(PRINT_ARCHIVE, print_payloads)

carbon_steps = sorted(OUT.glob("C*.step"))
carbon_dxfs = sorted(OUT.glob("C*_cut_mm.dxf"))
if len(carbon_steps) != 7 or len(carbon_dxfs) != 7:
    raise RuntimeError(
        f"expected 7 carbon STEP and 7 DXF files, found {len(carbon_steps)} and {len(carbon_dxfs)}"
    )
for note in (SUPPLIER_README, SUPPLIER_README_EN):
    if not note.is_file():
        raise FileNotFoundError(note)
supplier_payloads = [(f"DXF/{p.name}", p.read_bytes()) for p in carbon_dxfs]
supplier_payloads += [(f"STEP/{p.name}", p.read_bytes()) for p in carbon_steps]
supplier_payloads.append((SUPPLIER_README.name, SUPPLIER_README.read_bytes()))
supplier_payloads.append((SUPPLIER_README_EN.name, SUPPLIER_README_EN.read_bytes()))
write_archive(SUPPLIER_ARCHIVE, supplier_payloads)
