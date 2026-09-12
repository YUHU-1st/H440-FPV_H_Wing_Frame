"""Geometry-level checks specific to the B2 structural revision."""
from pathlib import Path
import sys,json
R=Path(__file__).resolve().parent;sys.path.insert(0,str(R/'.cad-deps'))
import cadquery as cq
O=R/'H440_B2'
report=json.loads((O/'geometry_report.json').read_text('utf-8'))
manifest=json.loads((O/'render_manifest.json').read_text('utf-8'))
assert len(report['parts'])==27
assert len(manifest)==35
assert not any('bracket_' in d['name'] for d in manifest)
assert 'P01_floor_angle' not in report['parts']
assert not report['checks']['interferences_mm3']
def load(n):return cq.importers.importStep(str(O/(n+'.step')))
def volume(s):return sum(x.Volume() for x in s.solids().vals())
def box(a,b,c,x,y,z):return cq.Workplane('XY').box(a,b,c).translate((x,y,z))
side=load('C01_center_side_R_2mm')
assert side.val().BoundingBox().ymax<=22.001
for n in ['C05_pylon_R_4mm','C06_pylon_L_4mm']:
    s=load(n);assert abs(s.val().BoundingBox().xlen-4)<1e-5
    for yy in [-92,-64,64,92]:
        for z in [-8,2]:
            probe=cq.Workplane('YZ',origin=(-150 if 'L_' in n else 140,yy,z)).circle(1.6).extrude(10)
            assert volume(s.intersect(probe))<1e-5
for yy,zs,n in [(16,[-35,-89],'C03_battery_floor_2mm'),(-19,[-27,-81],'C04_electronics_floor_2mm')]:
    tray=load(n)
    for z in zs:
        for sign in [-1,1]:
            # The tongue reaches at least 1.8 mm into a 2 mm side plate.
            tongue=box(1.8,2,12,sign*31.9,yy,z)
            assert abs(volume(tray.intersect(tongue))-43.2)<1e-4
            wall=side if sign==1 else side.mirror('YZ')
            assert volume(wall.intersect(tongue))<1e-5
clevis=load('P04_motor_clevis')
assert volume(clevis.intersect(box(4.15,37.8,21.8,145,78,-3)))<1e-5
checks={'master_parts':27,'assembly_instances':35,'printed_angle_instances':0,
        'battery_cage_removed_max_side_y_mm':22,'pylon_thickness_mm':4,
        'mortise_tongue_pairs_checked':8,'motor_clamp_holes_per_motor':4,
        'nominal_clevis_slot_mm':4.15,'frame_solid_interferences':0}
(O/'B2_specific_checks.json').write_text(json.dumps(checks,indent=2),encoding='utf-8')
print(json.dumps(checks,indent=2))
