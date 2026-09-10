# H440 FPV H-Wing Tailsitter Frame

H440 is an experimental H-layout tailsitter VTOL / fixed-wing FPV airframe. The current design target is a compact 440 mm-span aircraft using four 2306.5 1850 KV motors with 5-inch propellers and differential motor control only, without aerodynamic control surfaces.

> **Status:** engineering prototype. B1 geometry, manufacturing exports, native SolidWorks reopen checks and assembly references have been digitally verified. Structural load, vibration, propulsion, transition-control and flight performance have not been validated on a physical aircraft.

![H440 B1 isometric](H440_B1/H440_B1_isometric.png)

## Current revision

`H440_B1` is the active revision. `H440_A0` is retained as design history, and `X120_A1` is a separate small-scale experiment.

| Item | B1 target |
| --- | --- |
| Configuration | H-layout tailsitter VTOL / fixed wing |
| Wing span | 440 mm |
| Chord | 140 mm |
| Motors | 4 × 2306.5 1850 KV (target; verify actual motor dimensions) |
| Propellers | 5 in |
| Flight stack | 30.5 × 30.5 mm |
| Battery | 6S 1600 mAh target, sliding fore/aft for CG trim |
| Video | Analog / DJI O4 / DJI O4 Pro adapters |
| Camera | DJI O4 Pro dedicated 0–90° adjustable side mount; legacy cradle for other cameras |
| Print envelope | Each printable part fits a 256 mm-class build plate |

## B1 construction

B1 uses printed aerodynamic shells and connectors together with carbon-fibre primary structure:

- PLA wing shells, split into four printable sections.
- ABS structural connectors, camera mounts, collars and replaceable tail shoes.
- 2 mm CFRP center side plates, battery floor and electronics floor.
- 3 mm CFRP left/right motor-support trusses.
- 4 mm CFRP motor plates.
- Continuous 10/8 × 420 mm main carbon tube and 6/4 × 420 mm rear carbon tube.

The intended motor load path is motor → 4 mm motor plate → printed clevis → 3 mm truss → bonded spar collars → continuous carbon tubes → center structure. The printed wing skin is not the primary motor-load path.

## O4 Pro camera mount

B1 uses the O4 Pro camera's side M2 mounting pattern. The camera body is modeled from DJI's published 25.55 × 20 × 23.30 mm envelope, with 20 mm body width and 16 mm spacing between the two side mounting positions.

The dedicated left/right ABS side brackets provide:

- 20.4 mm nominal clear width between brackets;
- one M2 pivot hole per side;
- one M2 curved locking slot per side;
- continuous manual pitch adjustment from forward-facing to straight-down (0–90°);
- four M3 fasteners total to the electronics floor;
- a 24 × 25 mm center aperture in the electronics floor so the camera's optical axis remains clear at steep downward angles;
- clearance checked against the camera envelope and center optical axis through the full adjustment sweep.

DJI specifies M2 camera mounting threads with a maximum 2 mm thread engagement. Select screw length and washers so actual engagement does not exceed that limit.

## Repository layout

```text
H440_B1/                 Current manufacturing revision
  C*.step / *_cut_mm.dxf  CFRP parts and supplier-ready 2D cut profiles
  P*.step / *_print.stl   Printed connectors and equipment mounts
  W*.step / *_print.stl   Printed wing sections
  T*.step                 Carbon tubes
  H440_B1_FRAME.step      Named-parts frame assembly
  H440_B1_FRAME.SLDASM    Verified native SolidWorks assembly
  SolidWorks_Assembly_Parts/  Persisted assembly-instance SLDPRT files + imported root SLDASM
  H440_B1_LAYOUT.step     Frame plus equipment reference envelopes
  solidworks_native_report.json  Native save/reopen/reference audit
  H440_B1_supplier_DXF_STEP.zip  CFRP supplier DXF/STEP package
  geometry_report.json    Generated geometry / mass / clearance checks
  设计与装配说明.md           Detailed assembly and engineering notes
  BOM与重量预算.md            Parts and weight budget
  供应商交付说明.md             CFRP cutting quantities and machining notes
H440_A0/                 Historical revision
X120_A1/                 Separate small-scale experiment
build_h440_b1.py         Parametric B1 geometry source
finish_h440_b1.py        Round-trip checks, DXF units, BOM and renders
```

## Regenerating B1

The editable source of truth is `build_h440_b1.py`. SolidWorks files are downstream manufacturing / inspection deliverables rather than a fully native parametric feature tree.

Typical regeneration flow:

```bash
python build_h440_b1.py
python finish_h440_b1.py
```

The scripts generate STEP/STL/DXF outputs and geometry reports. The local environment must provide CadQuery; `finish_h440_b1.py` also uses `ezdxf` and `vtk`.

On the Windows workstation with SolidWorks 2024 and pywin32 available, run `python solidworks_native_delivery.py` after regeneration to recreate and audit the native SolidWorks deliverables.

## Manufacturing notes

- DXF units are millimetres and represent final part contours without cutter-radius compensation. Confirm kerf, minimum internal radius, nominal sheet thickness and holding tabs with the carbon supplier.
- Printable STEP files are the CAD master for printed parts; `_print.stl` files are convenience exports with print orientation applied.
- Carbon plate is electrically conductive. Keep exposed solder joints, battery terminals and power connectors insulated from CFRP.
- The current battery envelope remains an assumed 78 × 48 × 52 mm because a trustworthy published dimension set for the target DAI WONG GAU 6S 1600 mAh pack has not been confirmed. Measure the actual pack before ordering the full set of parts.
- Verify actual motor, FC/ESC and other equipment dimensions before ordering the full set of parts.
- Do not infer structural or flight safety from successful CAD interference checks.

## SolidWorks delivery

The B1 native delivery was regenerated and audited in SOLIDWORKS Premium 2024 SP5.0 (revision 32.5.0). All 28 current component STEP masters were saved as native `SLDPRT` files, closed, and reopened silently with zero reported open errors or warnings.

`H440_B1_FRAME.SLDASM` was rebuilt from the current frame STEP. SolidWorks represents this import as one root wrapper subassembly containing 43 generated component instances. The delivery script persists the wrapper and all 43 instance documents under `H440_B1/SolidWorks_Assembly_Parts/`, then closes every document and reopens the top-level SLDASM. The final audit found 44/44 component references on persistent repository paths, with no remaining SolidWorks temporary `IC~~` references. See `H440_B1/solidworks_native_report.json` for the recorded audit.

These files contain imported SolidWorks bodies rather than a hand-rebuilt native parametric feature tree. Geometry edits remain sourced from `build_h440_b1.py`.

## Validation still required

Before flight, the project still needs physical fit checks, printed-part and bonded-joint tests, actual mass/CG measurement, motor/prop thrust-current-temperature tests, vibration testing, constrained hover tests, flight-controller mixer/transition work and real flight validation.
