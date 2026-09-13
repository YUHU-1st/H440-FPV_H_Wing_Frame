"""Check B3 tie-bolt paths, TPU fixing sleeves and camera screw clearance."""
import sys,json,math,os
from pathlib import Path
R=Path(__file__).resolve().parent
sys.path.insert(0,str(R/'.cad-deps'))
import cadquery as cq
O=R/'H440_B3'
def part(name):return cq.importers.importStep(str(O/(name+'.step')))
def volume(s):return sum(x.Volume() for x in s.solids().vals())
frame=part('H440_B3_FRAME_multibody')
report=json.loads((O/'geometry_report.json').read_text(encoding='utf-8'))
assert not report['checks']['interferences_mm3']
side_pair=part('C01_center_side_R_2mm').union(part('C02_center_side_L_2mm'))
for name in ['C03_battery_floor_2mm','C04_electronics_floor_2mm']:
    deck=part(name)
    for dx in [-.1,.1]:
        assert volume(deck.translate((dx,0,0)).intersect(side_pair))>.01,(name,dx,'missing shoulder')
for y in [12,-12]:
    for z in [-20,-122]:
        bolt=cq.Workplane('YZ',origin=(-39,y,z)).circle(1.5).extrude(78)
        assert volume(frame.intersect(bolt))<.001,(y,z)
        for sign in [-1,1]:
            head=cq.Workplane('YZ',origin=(sign*33,y,z)).circle(3.3).extrude(sign*4)
            assert volume(frame.intersect(head))<.001,(y,z,sign,'head')
for x in [-21,21]:
    for y,zlist in [(-15,[2,14]),(20,[4,20])]:
        sleeve=cq.Workplane('XZ',origin=(x,y,zlist[0]))
        for z in zlist:
            sleeve=cq.Workplane('XZ',origin=(x,y,z)).circle(2.5).circle(1.6).extrude(3)
            assert volume(frame.intersect(sleeve))<.001,(x,y,z)
            bolt=cq.Workplane('XZ',origin=(x,y+2,z)).circle(1.5).extrude(10)
            assert volume(frame.intersect(bolt))<.001,(x,y,z,'bolt')
camera_support=part('P06R_O4Pro_camera_side').union(part('P06L_O4Pro_camera_side')).union(part('C03_battery_floor_2mm')).union(part('C04_electronics_floor_2mm'))
for i in range(0,91,5):
    a=math.radians(i)
    for y,z in [(10.35,5),(10.35-16*math.sin(a),5+16*math.cos(a))]:
        for sign in [-1,1]:
            head=cq.Workplane('YZ',origin=(sign*15.2,y,z)).circle(2.5).extrude(sign*2)
            assert volume(camera_support.intersect(head))<.001,(i,sign,y,z)
result={'tie_bolt_clear_paths':4,'TPU_crush_sleeve_positions':8,
        'deck_shoulder_stop_tests_at_plus_minus_0p1mm':4,
        'camera_M2_head_sweep_samples':19,'camera_M2_head_step_deg':5,'camera_M2_head_collision_count':0,
        'frame_solid_interferences':0,'masters':len(report['parts']),
        'TPU_side_wall_mm':5,'central_inner_width_mm':62,
        'metal_spacer_pitch_yz_mm':[24,102]}
(O/'B3_specific_checks.json').write_text(json.dumps(result,indent=2)+'\n',encoding='utf-8')
print(json.dumps(result,indent=2),flush=True)
# Match the BREP generator's explicit exit after all assertions and file writes.
os._exit(0)
