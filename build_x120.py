"""X120 A1 fit prototype. mm. Z = thrust/forward, XY = front view.
Run with CadQuery 2.8; source is the editable parametric master.
"""
from pathlib import Path
import math,json
import cadquery as cq

OUT=Path(__file__).parent/'X120_A1'
OUT.mkdir(exist_ok=True)
P=dict(fc_pitch=25.5,motor_radius=32.5,motor_pcd=6.6,motor_hole=1.5,
       wing_root=20,wing_tip=85,chord=40,skin=0.6,rib_width=0.9,rib_height=1.8)
def box(x,y,z,at):
    return cq.Workplane('XY').box(x,y,z).translate(at)
def turn(s,a):return s.rotate((0,0,0),(0,0,1),a)
def cyl(r,h,x=0,y=0,z=0):return cq.Workplane('XY').circle(r).extrude(h).translate((x,y,z))
R=P['fc_pitch']/math.sqrt(2)
# Open diamond ring: 25.5 mm adjacent mounting positions, NOT diagonal spacing.
hub=cq.Workplane('XY').polyline([(R+1.8,0),(0,R+1.8),(-R-1.8,0),(0,-R-1.8)]).close().extrude(1.6)
inner=cq.Workplane('XY').polyline([(R-1.8,0),(0,R-1.8),(-R+1.8,0),(0,-R+1.8)]).close().extrude(2)
hub=hub.cut(inner)
for a in [0,90,180,270]:
    pad=cyl(2.4,2.8,R,0).cut(cyl(0.65,4,R,0)) # self-tapping pilot, coupon first
    hub=hub.union(turn(pad,a))
for a in [45,135,225,315]:
    arm=box(21,3.2,1.6,(22,0,0.8))
    mount=cyl(5.3,1.6,32.5).cut(cyl(2,2,32.5))
    for b in [180,60,300]:
        t=math.radians(b)
        mount=mount.cut(cyl(P['motor_hole']/2,2,32.5+3.3*math.cos(t),3.3*math.sin(t)))
    # Open-bottom socket. Tongue 0.6 thick, socket 1.0, 0.2 per side.
    socket=box(12,3.2,5,(23,0,-2.5)).cut(box(10.4,1.0,5.1,(23,0,-2.55)))
    hub=hub.union(turn(arm.union(mount).union(socket),a))
hub=hub.clean()

# Wing print coordinates: x radial, y chord aft, z thickness. 0.6 membrane + ribs.
wing=cq.Workplane('XY').polyline([(20,6),(85,6),(85,46),(20,46)]).close().extrude(.6)
wing=wing.union(box(10,.0+5.8,.6,(23,3.1,.3))) # tongue starts y=.2, insertion stops on LE
for y in [6.45,16,45.55]:
    wing=wing.union(box(65,.9,1.2,(52.5,y,1.2)))
for x in [20.45,40,62,84.55]:
    wing=wing.union(box(.9,40,1.2,(x,26,1.2)))
# Tail standing pad beyond trailing edge, four identical feet.
wing=wing.union(box(10,3,1.8,(77,47.5,.9)))
wing=wing.clean()
def wing_inst(a):
    # x radial, -y maps to aft global Z; thickness maps tangentially.
    return turn(wing.translate((0,0,-.3)).rotate((0,0,0),(1,0,0),-90),a)

# Removable battery cage: clear 11.8 x 6.6, 30 mm long, two open strap stations.
# Built upright in local coordinates; assembly axis Z, bonded on hub inner crossrails.
sled=box(.9,8.4,30,(-6.35,0,-20)).union(box(.9,8.4,30,(6.35,0,-20)))
for z in [-32,-8]:
    sled=sled.union(box(13.6,.9,4,(0,-3.75,z))).union(box(13.6,.9,4,(0,3.75,z)))
# End stop prevents battery falling out aft; front is open for insertion before FC.
sled=sled.union(box(13.6,8.4,.8,(0,0,-35.4)))
for x in [-6.35,6.35]:
    sled=sled.union(box(.9,8.4,5,(x,0,-2.5)))
    sled=sled.union(box(5,1.8,.8,(x,0,-.4)))
# hub internal crossrails receive sled bonding tabs, kept below PCB
for x in [-6.35,6.35]:
    hub=hub.union(box(5,23.6,1.6,(x,0,.8)))
hub=hub.clean();sled=sled.clean()
# Drill AFTER unions: arms/ring must not refill the mounting bores.
for a in [0,90,180,270]:hub=hub.cut(turn(cyl(.65,10,R,0,-6),a))
for a in [45,135,225,315]:
    holes=cyl(2,10,32.5,0,-6)
    for b in [180,60,300]:
        t=math.radians(b)
        holes=holes.union(cyl(.75,10,32.5+3.3*math.cos(t),3.3*math.sin(t),-6))
    hub=hub.cut(turn(holes,a))
hub=hub.clean()

parts={'hub':(hub,1),'wing':(wing,4),'battery_cage':(sled,1)}
report={'parameters_mm':P,'parts':{},'checks':{},'status':'FIT / STRUCTURAL PROTOTYPE - NOT FLIGHT VALIDATED'}
assembly=cq.Assembly(name='X120_A1')
assembly.add(hub,name='hub',color=cq.Color(.22,.25,.29))
for i,a in enumerate([45,135,225,315]):assembly.add(wing_inst(a),name=f'wing_{i+1}',color=cq.Color(.1,.6,.75))
assembly.add(sled,name='battery_cage',color=cq.Color(.9,.5,.1))
for name,(s,n) in parts.items():
    shape=s.val();vol=shape.Volume();bb=shape.BoundingBox()
    assert shape.isValid(),name
    assert len(s.solids().vals())==1,(name,'disconnected')
    # Sled printed on its broad side; hub uses socket bottoms on bed (support required under frame).
    printable=s
    if name=='battery_cage':printable=s.rotate((0,0,0),(0,1,0),90)
    b=printable.val().BoundingBox();printable=printable.translate((-b.xmin,-b.ymin,-b.zmin))
    cq.exporters.export(printable,str(OUT/f'{name}_print.stl'),tolerance=.015,angularTolerance=.1)
    cq.exporters.export(s,str(OUT/f'{name}.step'))
    report['parts'][name]=dict(quantity=n,volume_mm3=round(vol,3),PLA_g=round(vol*.00124,3),bounds_mm=[round(bb.xlen,3),round(bb.ylen,3),round(bb.zlen,3)],solid_count=len(s.solids().vals()))
assembly.export(str(OUT/'X120_assembly.step'))
total=sum(v['PLA_g']*v['quantity'] for v in report['parts'].values())
report['PLA_structure_g']=round(total,3)
report['checks']['wing_hub_intersection_mm3']=[round(wing_inst(a).intersect(hub).val().Volume(),8) if wing_inst(a).intersect(hub).vals() else 0 for a in [45,135,225,315]]
report['checks']['adjacent_prop_tip_gap_mm']=round(32.5*math.sqrt(2)-31,3)
report['checks']['front_span_mm']=round(85*math.sqrt(2)+1.5/math.sqrt(2),3)
report['checks']['wing_area_cm2']=104
report['checks']['effective_small_angle_area_cm2']=52
(OUT/'geometry_report.json').write_text(json.dumps(report,indent=2),encoding='utf-8')
(OUT/'parameters.json').write_text(json.dumps(P,indent=2),encoding='utf-8')
print(json.dumps(report,indent=2),flush=True)
