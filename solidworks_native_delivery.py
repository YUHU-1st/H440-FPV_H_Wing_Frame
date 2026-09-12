"""Create and verify native SolidWorks delivery files from H440 B1/B2 STEP masters.

This deliberately uses late-bound IDispatch calls. The local SolidWorks 2024
installation can run normally but PowerShell/.NET type-library binding raises
TYPE_E_ELEMENTNOTFOUND, while raw IDispatch is healthy.

Before running, select valid default part/assembly templates and turn off
3D Interconnect. The local 2024 SP0.1 associated STEP import stalls in LoadFile4;
direct solid import succeeds. Run with H440_B2 to target the B2 delivery folder.
"""
from __future__ import annotations

import json
import os
import shutil
import sys
import tempfile
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parent
REVISION = sys.argv[1] if len(sys.argv) > 1 else "H440_B1"
if REVISION not in ("H440_B1", "H440_B2"):
    raise SystemExit("Expected H440_B1 or H440_B2")
B1 = ROOT / REVISION
PERSIST_DIR = B1 / "SolidWorks_Assembly_Parts"
DEPS = ROOT / ".cad-deps"
sys.path[:0] = [str(DEPS), str(DEPS / "win32"), str(DEPS / "win32" / "lib")]
if (DEPS / "pywin32_system32").is_dir():
    os.add_dll_directory(str(DEPS / "pywin32_system32"))

try:
    import pythoncom
    import pywintypes
    from win32com.client import VARIANT
    from win32com.client.dynamic import DumbDispatch
except Exception as exc:  # pragma: no cover - workstation setup diagnostic
    raise SystemExit(
        "pywin32 is required in .cad-deps for SolidWorks delivery; run with the "
        "same Python used for CAD generation and install pywin32 into .cad-deps"
    ) from exc

SW_DOC_PART = 1
SW_DOC_ASSEMBLY = 2
SW_OPEN_SILENT = 1
SW_SAVE_CURRENT = 0
SW_SAVE_SILENT = 1


def byref_i4(value: int = 0):
    return VARIANT(pythoncom.VT_BYREF | pythoncom.VT_I4, value)


def dispatch(obj, name: str):
    return DumbDispatch(obj, name)


def connect_solidworks():
    try:
        raw = pythoncom.GetActiveObject("SldWorks.Application")
    except Exception:
        clsid = pywintypes.IID("SldWorks.Application")
        raw = pythoncom.CoCreateInstance(
            clsid, None, pythoncom.CLSCTX_LOCAL_SERVER, pythoncom.IID_IDispatch
        )
        for _ in range(60):
            time.sleep(0.5)
            try:
                raw = pythoncom.GetActiveObject("SldWorks.Application")
                break
            except Exception:
                pass
    return dispatch(raw.QueryInterface(pythoncom.IID_IDispatch), "SldWorks.Application")


def close_active(sw):
    active = sw.ActiveDoc
    if active:
        model = dispatch(active, "ModelDoc2")
        sw.CloseDoc(model.GetTitle)


def load_foreign(sw, path: Path):
    import_data = sw.GetImportFileData(str(path))
    if not import_data:
        raise RuntimeError(f"GetImportFileData failed: {path.name}")
    errors = byref_i4()
    model = sw.LoadFile4(str(path), "r", import_data, errors)
    if not model or errors.value:
        raise RuntimeError(f"LoadFile4 failed: {path.name}; errors={errors.value}")
    return dispatch(model, "ModelDoc2"), errors.value


def save_native_part(sw, step: Path):
    model, import_errors = load_foreign(sw, step)
    out = step.with_suffix(".SLDPRT")
    save_result = model.SaveAs3(str(out), SW_SAVE_CURRENT, SW_SAVE_SILENT)
    if not out.is_file() or out.stat().st_size == 0:
        raise RuntimeError(f"SLDPRT was not written: {out.name}; SaveAs3={save_result}")
    sw.CloseDoc(model.GetTitle)

    errors = byref_i4()
    warnings = byref_i4()
    reopened = sw.OpenDoc6(
        str(out), SW_DOC_PART, SW_OPEN_SILENT, "", errors, warnings
    )
    if not reopened or errors.value or warnings.value:
        raise RuntimeError(
            f"Native reopen failed: {out.name}; errors={errors.value}; warnings={warnings.value}"
        )
    verify = dispatch(reopened, "ModelDoc2")
    reopened_path = verify.GetPathName
    sw.CloseDoc(verify.GetTitle)
    if Path(reopened_path).resolve() != out.resolve():
        raise RuntimeError(f"Native reopen path mismatch: {out.name}: {reopened_path}")
    return {
        "step": step.name,
        "sldprt": out.name,
        "size_bytes": out.stat().st_size,
        "import_errors": import_errors,
        "save_result": save_result,
        "reopen_errors": errors.value,
        "reopen_warnings": warnings.value,
    }


def verify_native_part(sw, step: Path):
    out = step.with_suffix(".SLDPRT")
    if not out.is_file() or out.stat().st_size == 0:
        raise RuntimeError(f"Existing SLDPRT is missing or empty: {out.name}")
    errors = byref_i4()
    warnings = byref_i4()
    reopened = sw.OpenDoc6(
        str(out), SW_DOC_PART, SW_OPEN_SILENT, "", errors, warnings
    )
    if not reopened or errors.value:
        raise RuntimeError(
            f"Existing native reopen failed: {out.name}; errors={errors.value}; warnings={warnings.value}"
        )
    verify = dispatch(reopened, "ModelDoc2")
    reopened_path = verify.GetPathName
    sw.CloseDoc(verify.GetTitle)
    if Path(reopened_path).resolve() != out.resolve():
        raise RuntimeError(f"Existing native reopen path mismatch: {out.name}: {reopened_path}")
    return {
        "step": step.name,
        "sldprt": out.name,
        "size_bytes": out.stat().st_size,
        "import_errors": None,
        "save_result": None,
        "reopen_errors": errors.value,
        "reopen_warnings": warnings.value,
        "reused_existing_native": True,
    }


def component_instance_name(component) -> str:
    name = str(component.Name2).split("/")[-1]
    if ".step-" in name.lower():
        name = name[: name.lower().rfind(".step-")]
    return name


def canonical_instance_name(raw_name: str, expected_names: set[str]) -> str:
    candidate = raw_name
    if candidate in expected_names:
        return candidate
    base, separator, suffix = candidate.rpartition("-")
    if separator and suffix.isdigit():
        candidate = base
    if candidate in expected_names:
        return candidate
    base, separator, suffix = candidate.rpartition("_")
    if separator and suffix.isdigit() and base in expected_names:
        return base
    raise RuntimeError(f"Unexpected SolidWorks import instance name: {raw_name}")


def persist_imported_component_tree(sw, model, expected_instances: list[str]):
    assembly = dispatch(model, "AssemblyDoc")
    components = [dispatch(c, "Component2") for c in (assembly.GetComponents(False) or [])]
    expected_leaf_count = len(expected_instances)
    if len(components) not in (expected_leaf_count, expected_leaf_count + 1):
        raise RuntimeError(
            f"Imported assembly node count {len(components)} is not a supported tree shape; "
            f"expected {expected_leaf_count} flattened leaves or "
            f"{expected_leaf_count + 1} nodes with one root wrapper"
        )

    PERSIST_DIR.mkdir(exist_ok=True)
    for old in PERSIST_DIR.glob("*.SLDPRT"):
        old.unlink()
    for old in PERSIST_DIR.glob("*.SLDASM"):
        old.unlink()

    roots = []
    leaves = []
    for component in components:
        raw_doc = component.GetModelDoc2
        if not raw_doc:
            raise RuntimeError(f"Component is unresolved: {component.Name2}")
        doc = dispatch(raw_doc, "ModelDoc2")
        doc_type = int(doc.GetType)
        if doc_type == SW_DOC_ASSEMBLY:
            roots.append((component, doc))
        elif doc_type == SW_DOC_PART:
            leaves.append((component, doc))
        else:
            raise RuntimeError(f"Unexpected component document type {doc_type}: {component.Name2}")

    if len(roots) not in (0, 1) or len(leaves) != len(expected_instances):
        raise RuntimeError(
            f"Imported tree shape mismatch: roots={len(roots)}, leaves={len(leaves)}, "
            f"expected leaves={len(expected_instances)}"
        )

    expected_names = set(expected_instances)
    mapped_leaves = []
    for component, doc in leaves:
        raw_name = component_instance_name(component)
        canonical_name = canonical_instance_name(raw_name, expected_names)
        mapped_leaves.append((canonical_name, raw_name, component, doc))
    canonical_names = [item[0] for item in mapped_leaves]
    if len(set(canonical_names)) != len(canonical_names) or set(canonical_names) != expected_names:
        missing = sorted(expected_names - set(canonical_names))
        duplicates = sorted({name for name in canonical_names if canonical_names.count(name) > 1})
        raise RuntimeError(
            f"Assembly instance mapping mismatch; missing={missing}; duplicates={duplicates}"
        )

    persisted = []
    for canonical_name, raw_name, component, doc in sorted(mapped_leaves, key=lambda item: item[0].lower()):
        out = PERSIST_DIR / f"{canonical_name}.SLDPRT"
        save_result = doc.SaveAs3(str(out), SW_SAVE_CURRENT, SW_SAVE_SILENT)
        current_ref = Path(str(component.GetPathName)).resolve()
        if not out.is_file() or out.stat().st_size == 0 or current_ref != out.resolve():
            raise RuntimeError(
                f"Persistent leaf save failed: {canonical_name}; SaveAs3={save_result}; ref={current_ref}"
            )
        persisted.append({
            "name": canonical_name,
            "solidworks_import_name": raw_name,
            "path": out.relative_to(B1).as_posix(),
            "size_bytes": out.stat().st_size,
        })

    root_out = None
    if roots:
        root_component, root_doc = roots[0]
        root_out = PERSIST_DIR / f"{REVISION}_FRAME_IMPORTED.SLDASM"
        root_save = root_doc.SaveAs3(str(root_out), SW_SAVE_CURRENT, SW_SAVE_SILENT)
        root_ref = Path(str(root_component.GetPathName)).resolve()
        if not root_out.is_file() or root_out.stat().st_size == 0 or root_ref != root_out.resolve():
            raise RuntimeError(
                f"Persistent root wrapper save failed; SaveAs3={root_save}; ref={root_ref}"
            )
    return persisted, root_out


def close_all(sw):
    sw.CloseAllDocuments(True)
    if sw.ActiveDoc:
        raise RuntimeError("SolidWorks still has an active document after CloseAllDocuments")


def save_and_verify_frame_assembly(sw):
    frame_step = B1 / f"{REVISION}_FRAME.step"
    frame_native = B1 / f"{REVISION}_FRAME.SLDASM"
    backup = Path(tempfile.gettempdir()) / f"{REVISION}_FRAME.pre_native.SLDASM"
    if frame_native.exists():
        shutil.copy2(frame_native, backup)

    manifest = json.loads((B1 / "render_manifest.json").read_text(encoding="utf-8"))
    expected_instances = [str(item["name"]) for item in manifest]

    model, import_errors = load_foreign(sw, frame_step)
    imported_type = int(model.GetType)
    if imported_type != SW_DOC_ASSEMBLY:
        sw.CloseDoc(model.GetTitle)
        raise RuntimeError(f"FRAME.step imported as document type {imported_type}, expected assembly")

    persisted, root_out = persist_imported_component_tree(sw, model, expected_instances)
    model.ForceRebuild3(False)
    save_result = model.SaveAs3(str(frame_native), SW_SAVE_CURRENT, SW_SAVE_SILENT)
    if not frame_native.is_file() or frame_native.stat().st_size == 0:
        raise RuntimeError(f"SLDASM was not written; SaveAs3={save_result}")

    close_all(sw)
    errors = byref_i4()
    warnings = byref_i4()
    reopened = sw.OpenDoc6(
        str(frame_native), SW_DOC_ASSEMBLY, SW_OPEN_SILENT, "", errors, warnings
    )
    if not reopened or errors.value:
        raise RuntimeError(
            f"SLDASM reopen failed; errors={errors.value}; warnings={warnings.value}"
        )
    verify_model = dispatch(reopened, "ModelDoc2")
    assembly = dispatch(reopened, "AssemblyDoc")
    components = [dispatch(c, "Component2") for c in (assembly.GetComponents(False) or [])]
    component_count = len(components)
    expected_root_count = 1 if root_out is not None else 0
    expected_node_count = len(expected_instances) + expected_root_count
    if component_count != expected_node_count:
        close_all(sw)
        raise RuntimeError(
            f"SLDASM reopen node count {component_count} != expected {expected_node_count}"
        )

    refs = []
    leaf_names = set()
    root_count = 0
    bad_refs = []
    delivery_root = B1.resolve()
    for component in components:
        path_text = str(component.GetPathName)
        path = Path(path_text).resolve() if path_text else None
        raw_doc = component.GetModelDoc2
        doc_type = int(dispatch(raw_doc, "ModelDoc2").GetType) if raw_doc else 0
        if doc_type == SW_DOC_ASSEMBLY:
            root_count += 1
        elif doc_type == SW_DOC_PART:
            leaf_names.add(canonical_instance_name(component_instance_name(component), set(expected_instances)))
        if (
            path is None
            or not path.is_file()
            or (path != delivery_root and delivery_root not in path.parents)
            or "\\temp\\" in path_text.lower()
            or "ic~~" in path_text.lower()
        ):
            bad_refs.append({"name": str(component.Name2), "path": path_text})
        reported_path = path_text
        if path is not None and (path == delivery_root or delivery_root in path.parents):
            reported_path = path.relative_to(delivery_root).as_posix()
        refs.append({"name": str(component.Name2), "path": reported_path, "doc_type": doc_type})

    if root_count != expected_root_count or leaf_names != set(expected_instances) or bad_refs:
        close_all(sw)
        raise RuntimeError(
            f"Persistent assembly verification failed: roots={root_count}, "
            f"leaf_match={leaf_names == set(expected_instances)}, bad_refs={bad_refs[:5]}"
        )
    if root_out is not None:
        reopened_root = [
            c
            for c in components
            if int(dispatch(c.GetModelDoc2, "ModelDoc2").GetType) == SW_DOC_ASSEMBLY
        ][0]
        if Path(str(reopened_root.GetPathName)).resolve() != root_out.resolve():
            close_all(sw)
            raise RuntimeError("Root imported subassembly path changed after native reopen")

    verify_model.ForceRebuild3(False)
    close_all(sw)
    return {
        "step": frame_step.name,
        "sldasm": frame_native.name,
        "size_bytes": frame_native.stat().st_size,
        "backup": backup.name,
        "import_errors": import_errors,
        "save_result": save_result,
        "reopen_errors": errors.value,
        "reopen_warnings": warnings.value,
        "component_count_including_root_wrapper": component_count,
        "generated_instance_count": len(expected_instances),
        "persistent_leaf_count": len(persisted),
        "import_tree_mode": "wrapper" if root_out is not None else "flattened",
        "persistent_root_subassembly": (
            root_out.relative_to(B1).as_posix() if root_out is not None else None
        ),
        "component_references": refs,
    }


def main():
    sw = connect_solidworks()
    sw.UserControl = True
    print(f"Connected to SolidWorks {sw.RevisionNumber}", flush=True)
    close_active(sw)
    geometry_report = json.loads((B1 / "geometry_report.json").read_text(encoding="utf-8"))
    steps = sorted(
        [(B1 / f"{name}.step").resolve() for name in geometry_report["parts"]],
        key=lambda p: p.name.lower(),
    )
    missing_steps = [p.name for p in steps if not p.is_file()]
    if missing_steps:
        raise SystemExit(f"Missing generated component STEP files: {missing_steps}")

    parts = []
    for index, step in enumerate(steps, 1):
        native = step.with_suffix(".SLDPRT")
        if native.is_file() and native.stat().st_size > 0:
            print(f"[{index:02}/{len(steps):02}] verifying existing {native.name}", flush=True)
            result = verify_native_part(sw, step)
        else:
            print(f"[{index:02}/{len(steps):02}] importing {step.name}", flush=True)
            result = save_native_part(sw, step)
        parts.append(result)
        print(f"[{index:02}/{len(steps):02}] native OK {step.name} -> {result['sldprt']}", flush=True)

    assembly = save_and_verify_frame_assembly(sw)
    report = {
        "generated_at": time.strftime("%Y-%m-%dT%H:%M:%S"),
        "solidworks_revision": str(sw.RevisionNumber),
        "component_sldprt_count": len(parts),
        "parts": parts,
        "assembly": assembly,
    }
    report_path = B1 / "solidworks_native_report.json"
    report_path.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
    print(
        f"ASSEMBLY OK {assembly['generated_instance_count']} generated instances; "
        f"tree={assembly['import_tree_mode']}; "
        f"all references persistent; report={report_path.name}",
        flush=True,
    )


if __name__ == "__main__":
    main()
