# H440 B1 CFRP Supplier Notes

`H440_B1_supplier_DXF_STEP.zip` contains the cutting definition for the H440 B1 flat CFRP parts. Use the seven files in `DXF/` for 2D machining. Same-name solids in `STEP/` are supplied for contour, hole-location and nominal-thickness reference.

| Part | Material | Thickness | Qty |
| --- | --- | ---: | ---: |
| C01_center_side_R_2mm | Solid CFRP sheet | 2 mm | 1 |
| C02_center_side_L_2mm | Solid CFRP sheet | 2 mm | 1 |
| C03_battery_floor_2mm | Solid CFRP sheet | 2 mm | 1 |
| C04_electronics_floor_2mm | Solid CFRP sheet | 2 mm | 1 |
| C05_pylon_R_3mm | Solid CFRP sheet | 3 mm | 1 |
| C06_pylon_L_3mm | Solid CFRP sheet | 3 mm | 1 |
| C07_motor_plate_4mm | Solid CFRP sheet | 4 mm | 4 |

- DXF units are millimetres. Curves describe final contours and exclude tool-radius, kerf and workholding compensation.
- Apply process-specific kerf, lead-ins, minimum radii, nesting clearance and holding tabs. Confirm actual sheet thickness.
- C05/C06 are structural trusses without countersinks. Cut four copies of C07 from its single DXF.
- Prefer solid laminate containing 0/90° and ±45° plies. Report material, layup or thickness deviations before cutting.
- STEP files are inspection references. If a STEP projection differs from its DXF, stop and request clarification.

Use the archive's `SHA256SUMS.txt` to verify transfer integrity.
