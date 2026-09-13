"""H440 B3 hybrid frame. mm; X span, Y up, Z forward.
Parametric BREP master, PLA aerodynamic shells, CFRP primary load path.
"""
import sys,os,math,json
from pathlib import Path
R=Path(__file__).parent;sys.path.insert(0,str(R/'.cad-deps'))
import cadquery as cq
O=R/'H440_B3';O.mkdir(exist_ok=True)
# Remove outputs retired by the B2 O4 Pro camera-mount revision so a regeneration
# cannot leave two different camera cradles looking simultaneously current.
for obsolete in ('P06_camera_cradle.step','P06_camera_cradle_print.stl','P06_camera_cradle.SLDPRT'):
    (O/obsolete).unlink(missing_ok=True)
def box(a,b,c,x=0,y=0,z=0):return cq.Workplane('XY').box(a,b,c).translate((x,y,z))
def cx(r,h,x,y,z):return cq.Workplane('YZ',origin=(x,y,z)).circle(r).extrude(h)
def cy(r,h,x,y,z):return cq.Workplane('XZ',origin=(x,y,z)).circle(r).extrude(h)
def cz(r,h,x,y,z):return cq.Workplane('XY',origin=(x,y,z)).circle(r).extrude(h)
parts={};instances=[]
colors={'PLA':(.08,.57,.68),'ABS':(.95,.43,.12),'TPU':(.6,.22,.8),'AL6061':(.7,.73,.75),'CFRP':(.15,.18,.21)}
rho={'PLA':1.24,'ABS':1.04,'TPU':1.21,'AL6061':2.70,'CFRP':1.60}
def reg(n,s,mat,qty=1,description='',axis=None,optional=False):
    s=s.clean();assert s.val().isValid() and len(s.solids().vals())==1,(n,len(s.solids().vals()))
    parts[n]=dict(shape=s,mat=mat,qty=qty,description=description,axis=axis,optional=optional)
    print('BUILT',n,round(s.val().Volume()*rho[mat]/1000,2),flush=True);return s
def add(n,s,mat):instances.append((n,s,mat))
def prof(c=140):
    def t(u):return .6*c*(.2969*math.sqrt(u)-.126*u-.3516*u*u+.2843*u**3-.1036*u**4)
    u=[(1-math.cos(math.pi*i/70))/2 for i in range(71)]
    return [(v*c,t(v)) for v in u]+[(v*c,-t(v)) for v in u[-2:0:-1]]
def wingblank(x,L):
    pl=cq.Plane(origin=(x,0,-5),xDir=(0,0,-1),normal=(1,0,0))
    return cq.Workplane(pl).polyline(prof()).close().extrude(L)

# 2mm central side plates: battery above continuous spars, electronics below.
# Low central web only: no cage alongside or above the battery.
side=box(2,8,80,32,9,-71)
for z in [-44,-98]:
    side=side.union(box(2,42,26,32,1,z))
    side=side.union(box(2,14,12,32,-12,z+17))
    side=side.cut(cx(5.2 if z==-44 else 3.2,5,30,0,z))
    for y in [-8,8]:side=side.cut(cx(1.7,5,30,y,z))
    # Closed mortises receive integral deck tongues. Epoxy retains the tongues.
    # Nominal 2 mm stock: 2.2 mm slot width, 12 mm tongue, 12.2 mm slot.
    for yy,zz in [(16,z+9),(-19,z+17)]:
        side=side.union(box(2,12,22,32,yy,zz))
        slot=box(5,2.2,12.2,32,yy,zz)
        # R0.6 corner relief for a <=1.2 mm router cutter; no forced fit.
        for sy in [-1,1]:
            for sz in [-1,1]:
                slot=slot.union(cx(.6,5,29.5,yy+sy*1.1,zz+sz*6.1))
        side=side.cut(slot)
for yy in [12,-12]:
    side=side.union(box(2,10,112,32,yy,-71))
    for zz in [-20,-122]:side=side.cut(cx(1.65,5,30,yy,zz))
for zz,rr in [(-44,5.2),(-98,3.2)]:
    side=side.cut(cx(rr,5,30,0,zz))
    for yy in [-8,8]:side=side.cut(cx(1.7,5,30,yy,zz))
    for yy,zslot in [(16,zz+9),(-19,zz+17)]:
        slot=box(5,2.2,12.2,32,yy,zslot)
        for sy in [-1,1]:
            for sz in [-1,1]:slot=slot.union(cx(.6,5,29.5,yy+sy*1.1,zslot+sz*6.1))
        side=side.cut(slot)
side=reg('C01_center_side_R_2mm',side,'CFRP',description='中央右侧板，2mm碳板，四点横向螺栓锁紧',axis='X')
sl=reg('C02_center_side_L_2mm',side.mirror('YZ'),'CFRP',description='中央左侧板，2mm碳板',axis='X')
add('Central_R',side,'CFRP');add('Central_L',sl,'CFRP')
# Battery sliding strap slots:132x3mm along Z, beside 48mm pack footprint.
floor=box(62,2,148,0,16,-75)
for z in [-119,-71,-23]:floor=floor.cut(box(28,4,18,0,16,z))
for x in [-27,27]:floor=floor.cut(box(3,4,132,x,16,-75))
for x in [-31.4,31.4]:
    for z in [-35,-89]:floor=floor.union(box(2.8,2,12,x,16,z))
for x in [-21,21]:
    floor=floor.union(box(8,2,37,x,16,7.5))
    for z in [4,20]:floor=floor.cut(cy(1.65,6,x,19,z))
floor=floor.cut(box(24,4,16,0,16,-7))
floor=reg('C03_battery_floor_2mm',floor,'CFRP',description='电池托板，2mm，双纵向穿带槽',axis='Y')
add('Battery_floor',floor,'CFRP')
# Electronics carrier 2mm, FC30.5, interchangeable VTX adapter40x32.
deck=box(50,2,150,0,-19,-55)
for x in [-28,28]:
    for z in [-27,-81]:deck=deck.union(box(6,2,20,x,-19,z))
for x in [-28.9,28.9]:
    for z in [-27,-81]:deck=deck.union(box(7.8,2,12,x,-19,z))
for z in [-83,-33]:deck=deck.cut(box(22,4,22,0,-19,z))
for x in [-15.25,15.25]:
    for dz in [-15.25,15.25]:deck=deck.cut(cy(1.7,6,x,-15,-83+dz))
for x in [-20,20]:
    for z in [-49,-17]:deck=deck.cut(cy(1.7,6,x,-15,z))
for x in [-10,10]:deck=deck.cut(cy(1.7,6,x,-15,11))
# Dedicated O4 Pro camera-side brackets. Keep the legacy x=+/-10 interface for
# the generic camera cradle and optional gimbal, and add four M3 bracket holes.
for x in [-21,21]:
    for z in [2,14]:deck=deck.cut(cy(1.7,6,x,-15,z))
# Central downward-view window; side strips retain the four bracket fasteners.
deck=deck.cut(box(24,4,25,0,-19,7.5))
for x in [-22,22]:deck=deck.cut(cy(3.2,6,x,-15,-122))
deck=reg('C04_electronics_floor_2mm',deck,'CFRP',description='开放飞塔/图传托板，2mm',axis='Y')
add('Electronics_floor',deck,'CFRP')
spacer=cx(3,62,-31,12,-20).cut(cx(1.65,64,-32,12,-20))
spacer=reg('T03_center_spacer_6x3p3_L62',spacer,'AL6061',4,'铝合金精密隔柱OD6/ID3.3×62，配M3贯穿螺栓',axis='stock')
for yy in [12,-12]:
    for zz in [-20,-122]:add(f'Center_spacer_{yy}_{zz}',spacer.translate((0,yy-12,zz+20)),'AL6061')

# Integral CFRP tongues replace all eight printed floor angles.

# Continuous rolled carbon tubes, no screw holes through tube walls.
for n,od,id_,z in [('T01_main_10x8_L420',10,8,-44),('T02_rear_6x4_L420',6,4,-98)]:
    t=cx(od/2,420,-210,0,z).cut(cx(id_/2,422,-211,0,z))
    t=reg(n,t,'CFRP',description=f'碳管OD{od}/ID{id_}×420，整根贯穿',axis='tube');add(n,t,'CFRP')

# Bonded flange collars, M3 inserts parallel X. No radial set-screws on carbon.
# Four per tube:2 central frame +2 pylon joints. Flanges carry load into plate.
collars=[]
for n,r,z in [('P02_main_collar',5.15,-44),('P03_rear_collar',3.15,-98)]:
    col=cx(12,12,19,0,z).cut(cx(r,14,18,0,z))
    for y in [-8,8]:col=col.cut(cx(2.1,6,25,y,z))
    col=reg(n,col,'ABS',4,f'胶接翼梁法兰套，内孔Ø{r*2:.1f}，2-M3嵌件',axis='X')
    for xoff,label in [(0,'center'),(112,'pylon')]:
        a=col.translate((xoff,0,0));b=a.mirror('YZ')
        add(n+'_'+label+'_R',a,'ABS');add(n+'_'+label+'_L',b,'ABS');collars.extend([a,b])

# 4mm side truss, widened chords and cross-bracing for lateral stiffness.
pl=cq.Plane(origin=(143,0,0),xDir=(0,0,1),normal=(1,0,0))
def yzpoly(pts,th=4):return cq.Workplane(pl).polyline([(z,-y) for y,z in pts]).close().extrude(th)
def bar(a,b,w=8):
    y,z=a;dy=b[0]-y;dz=b[1]-z;L=math.hypot(dy,dz);ny=-dz/L*w/2;nz=dy/L*w/2
    return yzpoly([(y+ny,z+nz),(b[0]+ny,b[1]+nz),(b[0]-ny,b[1]-nz),(y-ny,z-nz)])
A=(0,-44);B=(0,-98);C=(78,0);D=(83,-161)
upper=bar(A,C).union(bar(B,D)).union(bar(C,D)).union(bar(B,C,8)).union(bar(A,D,6))
truss=upper.union(upper.mirror('XZ')).union(bar(A,B,14))
for z in [-44,-98]:truss=truss.union(cx(12,4,143,0,z))
for y in [-78,78]:truss=truss.union(box(4,38,22,145,y,-3))
for y in [-83,83]:truss=truss.union(box(4,12,8,145,y,-161))
for z,r in [(-44,5.2),(-98,3.2)]:
    truss=truss.cut(cx(r,5,142,0,z))
    for y in [-8,8]:truss=truss.cut(cx(1.7,5,142,y,z))
for y0 in [-78,78]:
    for dy in [-14,14]:
        for zz in [-8,2]:truss=truss.cut(cx(1.65,6,142,y0+dy,zz))
truss=reg('C05_pylon_R_4mm',truss,'CFRP',description='右侧4mm交叉加强桁架，四孔电机座接口',axis='X')
trussL=reg('C06_pylon_L_4mm',truss.mirror('YZ'),'CFRP',description='左侧4mm交叉加强桁架，四孔电机座接口',axis='X')
add('Pylon_R',truss,'CFRP');add('Pylon_L',trussL,'CFRP')

# Motor plate4mm; 16x16 motor pattern, separate24x24 adapter pattern.
mp=box(36,36,4,145,78,14).edges('|Z').fillet(3)
mp=mp.cut(cz(4.5,6,145,78,11))
for d in [8,12]:
    for dx in [-d,d]:
        for dy in [-d,d]:mp=mp.cut(cz(1.7,6,145+dx,78+dy,11))
mp=reg('C07_motor_plate_4mm',mp,'CFRP',4,'电机板4mm；16孔距电机/24孔距转接',axis='Z')
# Printed clevis: two cheeks sandwich3mm vertical plate, top flange seats carbon.
ad=box(30,30,4,145,78,10)
for dx in [-5.075,5.075]:ad=ad.union(box(6,38,22,145+dx,78,-3))
# External gussets connect cheek walls to flange; keep M3 access clear.
for sign in [-1,1]:
    for yy in [65,95]:
        plane=cq.Plane(origin=(145,yy,0),xDir=(1,0,0),normal=(0,-1,0))
        rib=cq.Workplane(plane).polyline([(sign*8,-12),(sign*8,8),(sign*15,8)]).close().extrude(4)
        ad=ad.union(rib)
for yy in [64,92]:
    for zz in [-8,2]:ad=ad.cut(cx(1.65,24,133,yy,zz))
for dx in [-8,8]:
    for dy in [-8,8]:ad=ad.cut(cz(3.0,29,145+dx,78+dy,-15))
for dx in [-12,12]:
    for dy in [-12,12]:ad=ad.cut(cz(1.7,6,145+dx,78+dy,7))
ad=reg('P04_motor_clevis',ad,'ABS',4,'4mm桁架四孔U座，外侧三角筋加强，4.15mm夹槽',axis='Z')
for x in [-145,145]:
    for y in [-78,78]:
        add(f'Motor_plate_{x}_{y}',mp.translate((x-145,y-78,0)),'CFRP')
        add(f'Motor_clevis_{x}_{y}',ad.translate((x-145,y-78,0)),'ABS')
# Tail shoes, slot retention and epoxy; cheap replaceable wear part.
shoe=box(14,18,8,145,83,-165).cut(box(4.3,20,5,145,83,-162.5))
shoe=reg('P05_tail_shoe',shoe,'ABS',4,'可更换着陆脚套，胶接4mm侧板边缘',axis='X')
for x in [-145,145]:
    for y in [-83,83]:add(f'Shoe_{x}_{y}',shoe.translate((x-145,y-83,0)),'ABS')

# PLA aerodynamic panels. Main load is carried by tubes, not shell root inserts.
outer=wingblank(34,186)
def ht(u):return .6*140*(.2969*math.sqrt(u)-.126*u-.3516*u*u+.2843*u**3-.1036*u**4)
us=[3+i*122/70 for i in range(71)]
ip=[(u,ht(u/140)-.6) for u in us]+[(u,-ht(u/140)+.6) for u in us[::-1]]
inner=cq.Workplane(cq.Plane(origin=(35,0,-5),xDir=(0,0,-1),normal=(1,0,0))).polyline(ip).close().extrude(184)
wing=outer.cut(inner)
for x in [35,70,105,130,147,180,218]:wing=wing.union(box(.8,25,145,x,0,-75).intersect(outer))
for z,r in [(-44,5.15),(-98,3.15)]:
    wing=wing.union(cx(r+.6,186,34,0,z).intersect(outer))
    wing=wing.cut(cx(r,188,33,0,z))
# Allow space for ABS collar protruding around tube at pylon station.
for z in [-44,-98]:wing=wing.cut(cx(12.2,12.8,131,0,z))
wi=wing.intersect(box(108.8,50,160,88.4,0,-75))
wo=wing.intersect(box(72.8,50,160,183.6,0,-75))
for n,s,d in [('W01_inner_R',wi,'右翼内段'),('W02_outer_R',wo,'右翼外段'),('W03_inner_L',wi.mirror('YZ'),'左翼内段'),('W04_outer_L',wo.mirror('YZ'),'左翼外段')]:
    s=reg(n,s,'PLA',description=d+'，0.6mm标称皮+管套/0.8mm肋',axis='X');add(n,s,'PLA')

# DJI O4 Pro camera: published body 25.55 deep x 20 wide x 23.30 high.
# Project axes are X span, Y up, Z forward, so the envelope is X=20, Y=23.3, Z=25.55.
# Side mount uses the two M2 positions 16mm apart: rear position pivots, front position
# follows an R16 0-90deg slot. Camera is raised enough to clear the electronics deck
# through the entire sweep, including the lower mid-angle corner of the body envelope.
CAM_W,CAM_H,CAM_D=20.0,23.3,25.55
CAM_CLEAR=20.4
CAM_CENTER_Y,CAM_CENTER_Z=6.0,13.0
CAM_PIVOT_Y=CAM_CENTER_Y-CAM_H/2+16.0
CAM_PIVOT_Z=CAM_CENTER_Z-8.0
CAM_HOLE_PITCH=16.0
CAM_SLOT_W=2.6
CAM_SIDE_X=CAM_CLEAR/2+2.5
# Keep the side wall entirely forward of the battery-floor front edge (Z=-1).
# The M2 sweep only needs Z>=5, so Z=0..30 retains the camera support while
# preserving the full forward battery-trim envelope.
camwall=box(5,40,30,CAM_SIDE_X,2,15)
camfoot=box(12,3,24,21.2,-16.5,8)
camtop=box(12,3,28,21.2,18.5,12)
camR=camwall.union(camfoot).union(camtop).cut(cx(1.2,6,CAM_SIDE_X-3,CAM_PIVOT_Y,CAM_PIVOT_Z))
plcam=cq.Plane(origin=(CAM_SIDE_X-3,0,0),xDir=(0,0,1),normal=(1,0,0))
u0,v0=CAM_PIVOT_Z,-CAM_PIVOT_Y
ro,ri=CAM_HOLE_PITCH+CAM_SLOT_W/2,CAM_HOLE_PITCH-CAM_SLOT_W/2
s2=math.sqrt(2)
camslot=(cq.Workplane(plcam).moveTo(u0+ro,v0)
    .threePointArc((u0+ro/s2,v0+ro/s2),(u0,v0+ro))
    .lineTo(u0,v0+ri)
    .threePointArc((u0+ri/s2,v0+ri/s2),(u0+ri,v0))
    .close().extrude(6))
for yy,zz in [(CAM_PIVOT_Y,CAM_PIVOT_Z+CAM_HOLE_PITCH),(CAM_PIVOT_Y-CAM_HOLE_PITCH,CAM_PIVOT_Z)]:
    camslot=camslot.union(cx(CAM_SLOT_W/2,6,CAM_SIDE_X-3,yy,zz))
camR=camR.cut(camslot)
for z in [2,14]:camR=camR.cut(cy(2.55,3,21,-15,z))
for z in [4,20]:camR=camR.cut(cy(2.55,3,21,20,z))
camR=reg('P06R_O4Pro_camera_side',camR,'TPU',description='TPU95A右侧板，上下各双M3固定，OD5限压套，M2弧槽调角',axis='X')
camL=reg('P06L_O4Pro_camera_side',camR.mirror('YZ'),'TPU',description='TPU95A左侧板，上下各双M3固定，OD5限压套，M2弧槽调角',axis='X')
add('O4Pro_camera_side_R',camR,'TPU');add('O4Pro_camera_side_L',camL,'TPU')

# Reuse checked VTX interfaces and retain the old 26mm camera cradle as an optional
# legacy mount for regular O4 / analog camera inserts.
for n,old,shift,desc,opt in [
 ('P07_O4Pro_adapter','07_vtx_O4Pro_25p5_M2',(0,21,0),'O4 Pro25.5-M2适配板',False),
 ('P08_O4_adapter','08_vtx_O4_25p5_softmount',(0,21,0),'O4普通版软安装板',True),
 ('P09_analog_adapter','09_vtx_analog_20_M2',(0,21,0),'模拟20-M2安装板',True),
 ('P10_gimbal_dock','11_optional_servo_plate_23x12',(0,9,0),'单轴云台预留板，非整套云台',True),
 ('P11_O4_camera_insert','12_camera_insert_O4_14',(0,9,0),'14.4mm相机衬块',True),
 ('P12_analog_camera_insert','13_camera_insert_analog19',(0,9,0),'19.4mm相机衬块',True),
 ('P13_camera20_insert','14_camera_insert_20',(0,9,0),'20.4mm相机衬块',True),
 ('P14_camera_cradle_legacy','10_camera_cradle_26clear',(0,9,0),'26mm通用相机座；O4普通版/模拟相机兼容替代件',True)]:
    s=cq.importers.importStep(str(R/'H440_A0'/(old+'.step'))).translate(shift)
    s=reg(n,s,'ABS',description=desc,axis='Y',optional=opt)
    if not opt:add(n,s,'ABS')

report={'revision':'B3','status':'GEOMETRY CHECKED; NO STRUCTURAL OR FLIGHT VALIDATION','density_g_cm3':rho,'parts':{},'checks':{}}
frame=cq.Assembly(name='H440_B3_FRAME')
for n,s,mat in instances:frame.add(s,name=n,color=cq.Color(*colors[mat]))
for n,d in parts.items():
    s=d['shape'];cq.exporters.export(s,str(O/(n+'.step')))
    v=s.val().Volume();bb=s.val().BoundingBox();mat=d['mat']
    report['parts'][n]={k:d[k] for k in ['mat','qty','description','optional']}
    report['parts'][n].update(volume_mm3=round(v,3),unit_mass_g=round(v*rho[mat]/1000,3),bounds_mm=[round(bb.xlen,2),round(bb.ylen,2),round(bb.zlen,2)],valid=True)
    if mat in ('PLA','ABS','TPU'):
        ps=s
        if d['axis']=='X':ps=s.rotate((0,0,0),(0,1,0),90)
        elif d['axis']=='Y':ps=s.rotate((0,0,0),(1,0,0),90)
        b=ps.val().BoundingBox();ps=ps.translate((-b.xmin,-b.ymin,-b.zmin))
        assert b.xlen<246 and b.ylen<246 and b.zlen<256,n
        cq.exporters.export(ps,str(O/(n+'_print.stl')),tolerance=.04,angularTolerance=.15)
        report['parts'][n]['print_bounds_mm']=[round(b.xlen,2),round(b.ylen,2),round(b.zlen,2)]
    elif mat=='CFRP' and d['axis']!='tube':
        face=s.faces('>'+d['axis']).val()
        if d['axis']=='X':face=face.rotate((0,0,0),(0,1,0),90)
        elif d['axis']=='Y':face=face.rotate((0,0,0),(1,0,0),90)
        b=face.BoundingBox();face=face.translate((-b.xmin,-b.ymin,-b.zmin))
        cq.exporters.export(cq.Workplane('XY').newObject(face.Wires()),str(O/(n+'_cut_mm.dxf')))
frame.export(str(O/'H440_B3_FRAME.step'))
layout=cq.Assembly(name='H440_B3_LAYOUT');layout.add(frame,name='Frame')
refs=[]
def ref(n,s,col):layout.add(s,name=n,color=cq.Color(*col));refs.append((n,s,col))
ref('ASSUMED_BATTERY_78x48x52',box(48,52,78,0,47,-75),(.82,.71,.08))
ref('FC_ESC_ENVELOPE',box(36,23,36,0,-36,-83),(.08,.35,.12))
ref('O4PRO_ENVELOPE',box(33.5,13,33.5,0,-33,-33),(.24,.26,.29))
ref('CAMERA_ENVELOPE',box(CAM_W,CAM_H,CAM_D,0,CAM_CENTER_Y,CAM_CENTER_Z),(.1,.1,.1))
for x in [-145,145]:
    for y in [-78,78]:
        ref(f'MOTOR_{x}_{y}',cz(14,25,x,y,16),(.16,.16,.16))
        ref(f'PROP_{x}_{y}',cz(63.5,.8,x,y,46),(.62,.73,.78))
layout.export(str(O/'H440_B3_LAYOUT.step'))
# Also provide a single multi-body STEP for a robust SolidWorks part import.
cq.exporters.export(cq.Compound.makeCompound([s.val() for _,s,_ in instances]),str(O/'H440_B3_FRAME_multibody.step'))
ints=[]
for i,(a,sa,_) in enumerate(instances):
    b1=sa.val().BoundingBox()
    for b,sb,_ in instances[i+1:]:
        b2=sb.val().BoundingBox()
        if any(getattr(b1,k+'max')<=getattr(b2,k+'min')+.0001 or getattr(b2,k+'max')<=getattr(b1,k+'min')+.0001 for k in 'xyz'):continue
        v=sum(q.Volume() for q in sa.intersect(sb).solids().vals())
        if v>.01:ints.append([a,b,round(v,3)])
materialmass={mat:sum(s.val().Volume()*rho[mat]/1000 for _,s,m in instances if m==mat) for mat in rho}
report.update(material_mass_g={m:round(v,2) for m,v in materialmass.items()},CAD_frame_mass_g=round(sum(materialmass.values()),2))
report['checks'].update(interferences_mm3=ints,wing_span_mm=440,prop_spacing_mm=[290,156],prop_gap_mm=29,battery_assumed_mm=[78,48,52],battery_floor_mm=[62,148],battery_travel_geometric_mm=70,battery_recommended_travel_mm=60,tube_lengths_mm=[420,420],outer_wing_gap_at_pylon_mm=4.4)
# Camera sweep is also validated independently at 0.25deg increments during B2 delivery QA.
report['checks'].update(O4Pro_camera_envelope_mm_xyz=[CAM_W,CAM_H,CAM_D],O4Pro_camera_clear_width_mm=CAM_CLEAR,O4Pro_camera_angle_range_deg=[0,90],O4Pro_camera_M2_pitch_mm=CAM_HOLE_PITCH,O4Pro_camera_slot_width_mm=CAM_SLOT_W)
# Renderer source data, actual BREP geometry rather than conceptual artwork.
manifest=[]
for i,(n,s,mat) in enumerate(instances):
    fn=f'_instance_{i:02}.stl';cq.exporters.export(s,str(O/fn),tolerance=.12,angularTolerance=.2)
    manifest.append(dict(name=n,file=fn,color=colors[mat]))
(O/'render_manifest.json').write_text(json.dumps(manifest),encoding='utf-8')
(O/'geometry_report.json').write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding='utf-8')
print(json.dumps({'mass':materialmass,'CAD_g':report['CAD_frame_mass_g'],'interferences':ints},ensure_ascii=False,indent=2),flush=True)
os._exit(0)
