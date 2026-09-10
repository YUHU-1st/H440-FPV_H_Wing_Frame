# H440 B1 Project Overview

[Home](../README.md) · [中文](README_zh-CN.md)

![H440 B1 isometric view](../H440_B1/H440_B1_isometric.png)

## Objective

H440 B1 is a 440 mm-span H-layout tailsitter VTOL frame designed around four 2306.5 1850 KV motors and 5-inch propellers. All attitude control is intended to come from differential motor thrust; the airframe has no servos or aerodynamic control surfaces.

The design prioritizes compact proportions, common FPV electronics and fabrication on a 256 mm-class printer. Its wing is divided into four PLA sections, the structural fittings are ABS, and the primary motor loads pass through 2–4 mm CFRP plates and two continuous carbon-tube spars.

## Structure

- A 10/8 × 420 mm main tube and a 6/4 × 420 mm rear tube run continuously through both wings and the center frame.
- The center sides and floors use 2 mm CFRP; motor trusses use 3 mm CFRP; motor plates use 4 mm CFRP.
- The load path is motor → 4 mm motor plate → ABS clevis → 3 mm truss → bonded collar → continuous tubes → center frame.
- Calculated CAD structure mass is 404.23 g. The assembled-frame budget is 530.15 g; use 550 g as the first-article target.

![H440 B1 front layout](../H440_B1/H440_B1_front.png)

## Electronics and camera

- The FC/ESC stack pattern is 30.5 × 30.5 mm. The stack and video transmitter may remain exposed for passive cooling.
- Interchangeable plates support analog video, DJI O4 and DJI O4 Pro.
- The O4 Pro camera uses independent ABS side brackets. Each side has one M2 pivot and one M2 fastener in an R16 curved slot, giving continuous manual adjustment from forward-facing to straight-down, 0–90°.
- A 361-position sweep at 0.25° increments found no camera, bracket, deck or optical-axis collision; minimum deck clearance was approximately 2.128 mm.
- Nominal bracket clear width is 20.4 mm. With a 20 mm camera body, about 0.2 mm remains per side; make a fit coupon and compensate for measured ABS shrinkage.
- Camera-thread engagement must not exceed 2 mm. Select screw length after accounting for the bracket and washers.
- A 20 mm two-hole interface is reserved for a future single-axis servo gimbal; the complete gimbal is outside the current delivery.

## Battery and CG

Two 132 × 3 mm longitudinal slots let two 20 mm hook-and-loop straps move with the battery. The current CAD check uses a 78 × 48 × 52 mm envelope for the target 6S 1600 mAh pack and found no frame collision at forward, center and rear positions.

Measure the actual pack before production. The 148 mm tray provides 70 mm total travel; approximately ±30 mm is the recommended working range.

## Manufacturing files

- [`H440_B1_supplier_DXF_STEP.zip`](../H440_B1/H440_B1_supplier_DXF_STEP.zip): seven CFRP DXFs, seven matching STEP references, notes and SHA-256 manifest.
- [`H440_B1_printed_parts_STEP.zip`](../H440_B1/H440_B1_printed_parts_STEP.zip): 19 printable STEP masters—15 fittings/mounts and four wing sections.
- [`H440_B1_FRAME.SLDASM`](../H440_B1/H440_B1_FRAME.SLDASM): native SolidWorks 2024 assembly.
- [`H440_B1_FRAME.step`](../H440_B1/H440_B1_FRAME.step): neutral frame assembly with named parts.
- [`H440_B1_LAYOUT.step`](../H440_B1/H440_B1_LAYOUT.step): frame plus equipment envelopes for layout checks only.

Use the DXFs as the CFRP cutting definition. Units are millimetres and cutter compensation is not included. STEP is the printed-part master; STL only supplies a suggested orientation.

## Digital validation

- Every STEP passed a read-back check; all seven DXFs declare millimetre units.
- Frame solid-interference count is zero; the O4 Pro 0–90° sweep reports zero collisions.
- All 28 master SLDPRTs were saved and reopened; 43 assembly-instance SLDPRTs have persistent repository paths.
- Both archives passed CRC, internal SHA-256, expected-count and byte-for-byte disk-master checks.

## First-article sequence

1. Measure the actual battery, motors, stack, video unit and camera.
2. Print wing-skin/tube-sleeve, insert-hole and O4 Pro bracket coupons first.
3. Pull/torsion-test bonded tubes and pull-test heat-set inserts using production materials.
4. Complete propeller-off direction, thrust/current/temperature and vibration checks.
5. Weigh installed components and calculate the three-axis center of gravity.
6. Complete static-load and restrained-hover testing before flight and transition tuning.

This revision is a digitally checked engineering prototype, not a flight-qualified product.
