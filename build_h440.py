"""H440 A0: dimensional / structural prototype, mm. X span,Y up,Z forward.
Offline BREP master; imported and saved using the SolidWorks UI.
"""
import sys, os, json, math
from pathlib import Path
sys.path.insert(0,str(Path(__file__).parent/'.cad-deps'))
import cadquery as cq
OUT=Path(__file__).parent/'H440_A0'
OUT.mkdir(exist_ok=True)
def box(a,b,c,x=0,y=0,z=0): return cq.Workplane('XY').box(a,b,c).translate((x,y,z))
def cyl(r,h,x=0,y=0,z=0):return cq.Workplane('XY').circle(r).extrude(h).translate((x,y,z))
def bore_y(r,h,x,y,z):return cq.Workplane('XZ',origin=(x,y,z)).circle(r).extrude(h)
def bore_x(r,h,x,y,z):return cq.Workplane('YZ',origin=(x,y,z)).circle(r).extrude(h)
def union_all(ss):
    a=ss[0]
    for s in ss[1:]:a=a.union(s)
    return a.clean()
parts={}; inst=[]
def part(n,s,qty=1,color=(.25,.3,.35),print_axis=None):
    s=s.clean(); assert s.val().isValid(),n
    assert len(s.solids().vals())==1,(n,len(s.solids().vals()))
    parts[n]=(s,qty,color,print_axis)
    print('BUILT',n,round(s.val().Volume()),flush=True)
    return s
def add(n,s,color):inst.append((n,s,color))

# Central open battery cradle. Clear width54, height60, axial length148.
# Side rails are full-depth at wing roots; windows elsewhere reduce weight.
side=box(5,66,160,29.5,0,-75)
side=side.cut(box(7,52,146,29.5,0,-75))
side=side.union(box(5,16,156,29.5,0,-75))
for z in [-45,-95]:side=side.union(box(5,62,6,29.5,0,z))
for z in [-45,-95]:side=side.cut(bore_x(1.7,9,25,0,z))
center=side.union(side.mirror('YZ'))
for z in [-153,3]:center=center.union(box(64,5,5,0,-30.5,z))
for x in [-23.5,23.5]:center=center.union(box(7,4,150,x,-31,-75))
# Continuous raised floor: sliding straps can move with the battery.
for z in [-146,-4]:
    for x in [-24,24]:center=center.union(box(6,4,8,x,-27,z))
center=center.union(box(54,3,148,0,-23.5,-75))
center=center.cut(box(55,2.4,132,0,-27.3,-75))
# Electronics floor underneath cradle, ribs prevent stack bolts touching battery.
for z in [-101,-24]:center=center.union(box(64,4,6,0,-35,z))
for x in [-25,25]:center=center.union(box(7,4,110,x,-35,-62.5))
for z in [-85,-40]:
    for x in [-22,22]:center=center.cut(bore_y(1.7,14,x,-27,z))
# Forward camera/gimbal docking pad, transverse 20mm M3 pitch.
center=center.union(box(38,4,20,0,-30,9))
for x in [-10,10]:center=center.cut(bore_y(1.7,8,x,-26,11))
center=part('01_center_cradle',center,color=(.19,.22,.26))
add('Center_cradle',center,(.19,.22,.26))

# NACA0012 closed trailing edge, 140mm chord. LE Z=-5, TE=-145.
def profile(c=140,t=.12):
    us=[(1-math.cos(math.pi*i/60))/2 for i in range(61)]
    def thick(u):return 5*t*c*(.2969*math.sqrt(u)-.126*u-.3516*u*u+.2843*u**3-.1036*u**4)
    return [(u*c,thick(u)) for u in us]+[(u*c,-thick(u)) for u in us[-2:0:-1]]
plane=cq.Plane(origin=(32,0,-5),xDir=(0,0,-1),normal=(1,0,0))
outer=cq.Workplane(plane).polyline(profile()).close().extrude(188)
innerpts=[(1.5+u*137/140,v*.90) for u,v in profile()]
inner=cq.Workplane(cq.Plane(origin=(43,0,-5),xDir=(0,0,-1),normal=(1,0,0))).polyline(innerpts).close().extrude(175)
wing=outer.cut(inner)
for x in [70,100,130,145,170,195,218]:
    rib=box(1.2,30,150,x,0,-75).intersect(outer)
    wing=wing.union(rib)
for x in [138,152]:
    for z in [-48,-88]:wing=wing.union(bore_y(4.5,30,x,15,z).intersect(outer))
# Closed fore spar and rear spar, fully bonded to both skins.
for z in [-43,-98]:wing=wing.union(box(188,24,1.6,126,0,z).intersect(outer))
# Two blind insert bores, 4.2mm nominal; inserts and pull-out testing required.
for z in [-45,-95]:wing=wing.cut(bore_x(2.1,8,32,0,z))
# Four through bolts clamp upper/lower pylons around reinforced rib.
for x in [138,152]:
    for z in [-48,-88]:wing=wing.cut(bore_y(1.7,30,x,15,z))
wing=part('02_wing_right',wing,color=(.08,.57,.68),print_axis='span')
left=part('03_wing_left',wing.mirror('YZ'),color=(.08,.57,.68),print_axis='span')
add('Wing_right',wing,(.08,.57,.68));add('Wing_left',left,(.08,.57,.68))

# Pylon is a side truss, bonded triangular webs and motor flange.
# Positive Y local upper pylon at X145; mirrored for other corners.
pl=cq.Plane(origin=(141,0,0),xDir=(0,0,1),normal=(1,0,0))
# local x=Z, local y=-Y, use explicit poly with negated Y
def yzpoly(pts,th=5):return cq.Workplane(pl).polyline([(z,-y) for y,z in pts]).close().extrude(th)
pylon=yzpoly([(9,-100),(9,-37),(70,12),(89,12),(89,-165),(77,-165)])
opening=yzpoly([(18,-90),(18,-43),(75,0),(81,0),(81,-153)],12).translate((-2,0,0))
pylon=pylon.cut(opening)
# Triangular diagonal web across the window.
pylon=pylon.union(yzpoly([(18,-83),(23,-86),(80,-15),(75,-11)]))
# Motor barrel support and top plate, rotor flange Z=12..17.
pylon=pylon.union(box(18,18,30,145,78,-3))
pylon=pylon.union(cyl(18,5,145,78,12))
pylon=pylon.cut(cyl(4.5,39,145,78,-18))
for dx in [-8,8]:
    for dy in [-8,8]:pylon=pylon.cut(cyl(1.7,38,145+dx,78+dy,-18))
# Wing saddle has airfoil underside; both screw faces have planar washer lands.
saddle=box(30,11,58,145,10,-68).cut(outer)
saddle=saddle.cut(box(16,20,26,145,12,-68))
pylon=pylon.union(saddle)
for x in [138,152]:
    for z in [-48,-88]:pylon=pylon.cut(bore_y(1.7,22,x,23,z))
# Tail landing shoe, sacrificial thick edge, all four at Z=-169.
pylon=pylon.union(box(22,16,5,145,83,-166.5))
pylon=part('04_pylon_upper',pylon,1,(.95,.43,.12),'side')
lower=part('05_pylon_lower',pylon.mirror('XZ'),1,(.95,.43,.12),'side')
part('04L_pylon_upper_left',pylon.mirror('YZ'),1,(.95,.43,.12),'side')
part('05L_pylon_lower_left',lower.mirror('YZ'),1,(.95,.43,.12),'side')
for lr in [1,-1]:
    for ud,s in [('upper',pylon),('lower',lower)]:add(f'Pylon_{lr}_{ud}',s if lr==1 else s.mirror('YZ'),(.95,.43,.12))

# Removable electronics cassette: stack at Z=-83, VTX at Z=-33.
# Install plates on bottom of frame; stand-offs mount towards negative Y.
deck=box(50,3,104,0,-39.5,-62)
deck=deck.union(box(50,3,16,0,-39.5,-120))
for x in [-19,19]:deck=deck.cut(bore_y(3.2,8,x,-35,-121))
for z in [-83,-33]:deck=deck.cut(box(23,5,23,0,-39.5,z))
for z in [-85,-40]:
    for x in [-22,22]:deck=deck.cut(bore_y(1.7,8,x,-35,z))
for dx in [-15.25,15.25]:
    for dz in [-15.25,15.25]:deck=deck.cut(bore_y(1.7,8,dx,-35,-83+dz))
# Adapter docking 40 x32, separate from stack30.5 and VTX25.5
for x in [-20,20]:
    for z in [-49,-17]:deck=deck.cut(bore_y(1.7,8,x,-35,z))
deck=part('06_electronics_deck',deck,color=(.28,.31,.36))
add('Electronics_deck',deck,(.28,.31,.36))

def adapter(name,pitch,hole):
    a=box(46,2.4,40,0,-44.2,-33).cut(box(18,4,18,0,-44.2,-33))
    for x in [-20,20]:
        for z in [-49,-17]:a=a.cut(bore_y(1.7,6,x,-41,z))
    for x in [-pitch/2,pitch/2]:
        for z in [-33-pitch/2,-33+pitch/2]:a=a.cut(bore_y(hole/2,6,x,-41,z))
    return part(name,a,color=(.52,.55,.57))
opro=adapter('07_vtx_O4Pro_25p5_M2',25.5,2.3)
olite=adapter('08_vtx_O4_25p5_softmount',25.5,2.8)
analog=adapter('09_vtx_analog_20_M2',20,2.3)
add('VTX_adapter_O4Pro',opro,(.52,.55,.57))

# Camera cradle, modules retained on swappable shoes; no guessed side screw pattern.
# 26mm clear envelope; O4 and analog use separate reducing shoes + narrow tie straps.
cam=box(34,3,28,0,-25.5,13)
for x in [-15,15]:cam=cam.union(box(4,26,28,x,-11,13))
for x in [-10,10]:cam=cam.cut(bore_y(1.7,9,x,-20,11))
for x in [-15,15]:
    for z in [5,21]:cam=cam.cut(box(6,3,4,x,-8,z))
cam=part('10_camera_cradle_26clear',cam,color=(.95,.43,.12))
add('Camera_cradle',cam,(.95,.43,.12))
# Replace whole cradle with servo gimbal module on same20 pitch interface.
gimbal=box(44,4,50,0,-25,20)
gimbal=gimbal.cut(box(24,8,13,0,-25,30))
for x in [-10,10]:gimbal=gimbal.cut(bore_y(1.7,8,x,-20,11))
for x in [-16,16]:gimbal=gimbal.cut(bore_y(1.2,8,x,-20,30))
part('11_optional_servo_plate_23x12',gimbal,color=(.95,.43,.12))
for name,w in [('12_camera_insert_O4_14',14.4),('13_camera_insert_analog19',19.4),('14_camera_insert_20',20.4)]:
    insert=box(25.8,2,16,0,-23,13)
    for sign in [-1,1]:insert=insert.union(box((25.8-w)/2,12,16,sign*(w/2+(25.8-w)/4),-18,13))
    part(name,insert,color=(.45,.45,.45))

# Configuration envelope references, excluded from printable assembly.
assembly=cq.Assembly(name='H440_A0_FRAME')
for n,s,c in inst:assembly.add(s,name=n,color=cq.Color(*c))
report={'status':'A0 FIT AND STRUCTURAL PROTOTYPE - NOT FLIGHT VALIDATED','axes':'X span,Y up,Z forward; mm','parts':{},'checks':{}}
for n,(s,q,c,ori) in parts.items():
    cq.exporters.export(s,str(OUT/(n+'.step')))
    ps=s
    if ori=='span':ps=s.rotate((0,0,0),(0,1,0),90)
    elif ori=='side':ps=s.rotate((0,0,0),(0,1,0),90)
    else:ps=s.rotate((0,0,0),(1,0,0),90)
    bb=ps.val().BoundingBox();ps=ps.translate((-bb.xmin,-bb.ymin,-bb.zmin))
    cq.exporters.export(ps,str(OUT/(n+'_print.stl')),tolerance=.04,angularTolerance=.15)
    dims=[bb.xlen,bb.ylen,bb.zlen]
    assert dims[0]<=246 and dims[1]<=246,(n,dims)
    report['parts'][n]={'quantity':q,'print_bounds_mm':[round(v,2) for v in dims],'volume_mm3':round(s.val().Volume(),2),'PLA_solid_g':round(s.val().Volume()*.00124,2),'valid':s.val().isValid(),'solids':len(s.solids().vals())}
assembly.export(str(OUT/'H440_A0_FRAME.step'))
layout=cq.Assembly(name='H440_A0_LAYOUT')
layout.add(assembly,name='Printed_frame')
layout.add(box(48,52,78,0,4,-63),name='ASSUMED_BATTERY_78x48x52',color=cq.Color(.82,.71,.08))
layout.add(box(36,23,36,0,-55,-83),name='FC_ESC_30p5_ENVELOPE',color=cq.Color(.05,.35,.1))
layout.add(box(33.5,13,33.5,0,-54,-33),name='O4PRO_ENVELOPE',color=cq.Color(.25,.25,.25))
layout.add(box(25.55,20,23.3,0,-10,13),name='O4PRO_CAMERA_ENVELOPE',color=cq.Color(.1,.1,.1))
for x in [-145,145]:
    for y in [-78,78]:
        layout.add(cyl(14,25,x,y,17),name=f'MOTOR_ENVELOPE_{x}_{y}',color=cq.Color(.16,.16,.16))
        layout.add(cyl(63.5,1,x,y,46),name=f'PROP_DISK_127_{x}_{y}',color=cq.Color(.65,.78,.83,.22))
layout.export(str(OUT/'H440_A0_LAYOUT.step'))
report['checks'].update(wing_span_mm=440,motor_spacing_mm=[290,156],prop_diameter_mm=127,prop_min_tip_gap_mm=29,frame_length_mm=196,with_prop_length_mm=216,battery_assumed_mm=[78,48,52],battery_clear_width_mm=54,battery_usable_length_mm=148,battery_nominal_travel_mm=70,wing_area_m2=.0616,material_note='CAD solid volume; actual slicer toolpaths and inserts excluded')
# Exact BREP interference test of all printed instances. Shared tangent faces allowed.
interferences=[]
for i,(a,sa,_) in enumerate(inst):
    for b,sb,_ in inst[i+1:]:
        bb1=sa.val().BoundingBox();bb2=sb.val().BoundingBox()
        if any(getattr(bb1,ax+'max')<=getattr(bb2,ax+'min')+1e-6 or getattr(bb2,ax+'max')<=getattr(bb1,ax+'min')+1e-6 for ax in 'xyz'):continue
        inter=sa.intersect(sb)
        v=sum(x.Volume() for x in inter.solids().vals())
        if v>.01:interferences.append([a,b,round(v,3)])
report['checks']['printed_part_interferences_mm3']=interferences
report['installed_PLA_solid_mass_g']=round(sum(s.val().Volume()*.00124 for _,s,_ in inst),1)
(OUT/'geometry_report.json').write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding='utf-8')
print(json.dumps(report,ensure_ascii=False,indent=2),flush=True)
os._exit(0)
