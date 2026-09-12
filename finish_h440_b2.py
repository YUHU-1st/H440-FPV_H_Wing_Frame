import sys,os,json,math
from pathlib import Path
R=Path(__file__).parent;sys.path.insert(0,str(R/'.cad-deps'))
import cadquery as cq
import ezdxf
import vtk
O=R/'H440_B2';report=json.loads((O/'geometry_report.json').read_text(encoding='utf-8'))
hardware=[
 ('H01','M3×8钢螺钉：碳板到法兰套',16,.65),
 ('H02','M3×12钢螺钉：电机板16＋图传转接4',20,.9),
 ('H03','M3×22钢螺钉：电机U座四孔夹侧板，按垫片实测选长',16,1.3),
 ('H04','M3×10钢螺钉：O4 Pro相机侧板4；中央托板改榫槽胶接',4,.75),
 ('H05','M3×6电机螺钉，长度需按电机复核',16,.5),
 ('H06','M3防松螺母',38,.38),
 ('H07','M3薄平垫片',92,.08),
 ('H08','M3热熔嵌件，外径按Ø4.2试孔匹配',16,.3),
 ('H09','4根飞塔绝缘柱＋配套尼龙螺钉',1,6),
 ('H10','图传M2紧固/胶圈套件',1,2),
 ('H11','图传间隔柱、绝缘薄垫套件',1,3),
 ('H12','20mm宽电池绑带',2,5),
 ('H13','36×78×4mm防滑泡棉垫',1,2),
 ('H14','O4 Pro相机M2侧螺钉/薄垫片＋导线固定件；实际螺纹拧入不得超过2mm',1,3),
 ('H15','管套/翼套/脚套及中央榫槽胶接胶，装机留存量',1,10),
 ('H16','电机夹槽0.05/0.10mm硬质金属配合垫片组，按实测选择',4,.4)]
hw=sum(q*m for _,_,q,m in hardware)
report['hardware_estimate_g']=round(hw,2);report['frame_estimate_g']=round(hw+report['CAD_frame_mass_g'],2)
report['hardware']=[dict(id=i,description=d,qty=q,unit_mass_g=m) for i,d,q,m in hardware]
# Serialisation, DXF units, component and reference envelope checks.
for n,d in report['parts'].items():
    s=cq.importers.importStep(str(O/(n+'.step')))
    assert len(s.solids().vals())==1 and s.val().isValid(),n
    assert abs(s.val().Volume()-d['volume_mm3'])<.02,n
dxfs={}
for f in O.glob('*_cut_mm.dxf'):
    doc=ezdxf.readfile(f);doc.units=4;doc.saveas(f)
    dxfs[f.name]=dict(INSUNITS=4,entity_count=len(doc.modelspace()))
report['checks']['STEP_roundtrip_all_valid']=True
report['checks']['DXF_units']=dxfs
# Check actual frame against assumed battery over +/-30mm usable travel.
frame=cq.importers.importStep(str(O/'H440_B2_FRAME_multibody.step'))
travel=[]
for z in [-105,-75,-45]:
    battery=cq.Workplane('XY').box(48,52,78).translate((0,47,z))
    v=sum(s.Volume() for s in frame.intersect(battery).solids().vals());travel.append(round(v,4))
assert max(travel)<.01,travel
report['checks']['battery_frame_interference_mm3_at_z_minus105_minus75_minus45']=travel
# Validate the complete O4 Pro camera sweep from forward to straight down.
camR=cq.importers.importStep(str(O/'P06R_O4Pro_camera_side.step'))
camL=cq.importers.importStep(str(O/'P06L_O4Pro_camera_side.step'))
camdeck=cq.importers.importStep(str(O/'C04_electronics_floor_2mm.step'))
camera0=cq.Workplane('XY').box(20,23.3,25.55).translate((0,6,13))
camclear=[]
optical_collisions=[]
for i in range(361):
    angle=i*.25
    camera=camera0.rotate((0,10.35,5),(1,10.35,5),angle)
    vmount=sum(s.Volume() for s in camera.intersect(camR).solids().vals())+sum(s.Volume() for s in camera.intersect(camL).solids().vals())
    vdeck=sum(s.Volume() for s in camera.intersect(camdeck).solids().vals())
    assert vmount<1e-6 and vdeck<1e-6,(angle,vmount,vdeck)
    camclear.append(camera.val().BoundingBox().ymin-camdeck.val().BoundingBox().ymax)
    a=math.radians(angle);dy=6-10.35;dz=13-5
    cy0=10.35+dy*math.cos(a)-dz*math.sin(a);cz0=5+dy*math.sin(a)+dz*math.cos(a)
    fy,fz=-math.sin(a),math.cos(a)
    ly,lz=cy0+25.55/2*fy,cz0+25.55/2*fz
    ray=cq.Workplane('XY').newObject([cq.Solid.makeCylinder(.10,200,cq.Vector(0,ly,lz),cq.Vector(0,fy,fz))])
    vray=sum(s.Volume() for s in ray.intersect(camdeck).solids().vals())
    if vray>1e-6:optical_collisions.append((angle,vray))
assert not optical_collisions,optical_collisions[:5]
report['checks']['O4Pro_camera_sweep']={'range_deg':[0,90],'step_deg':.25,'samples':361,'collision_count':0,'optical_axis_collision_count':0,'downward_view_aperture_mm_xz':[24,25],'minimum_deck_clearance_mm':round(min(camclear),3)}
(O/'geometry_report.json').write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding='utf-8')
lines=['# H440 B2 机架 BOM 与重量预算','',f'标准配置：PLA机翼、ABS连接件、2/4mm碳板、两根碳管，O4 Pro安装板。CAD结构净重 **{report["CAD_frame_mass_g"]:.1f} g**；紧固件、绑带、防滑垫与胶估计 **{hw:.1f} g**；机架合计 **{report["frame_estimate_g"]:.1f} g**。建议按 **620 g** 留重量预算，首件称重前合理估计范围约 **550–660 g**。','',
'这是机架重量，包含安装五金但不包含电机、桨、飞塔、图传相机、接收机、电池和完整云台。质量按CAD体积×密度估算，金属/软材料为预算假设，尚未切片或称重。',
'','## 标准装机零件','','|件号|零件/规格|材料|数量|单重 g|合计 g|','|---|---|---|---:|---:|---:|']
for n,d in report['parts'].items():
    if not d['optional']:lines.append(f'|{n}|{d["description"]}|{d["mat"]}|{d["qty"]}|{d["unit_mass_g"]:.2f}|{d["unit_mass_g"]*d["qty"]:.2f}|')
lines+=['','## 五金与装配消耗品','','以下为完整4孔电机板连接方案；不为减轻几克重量擅自删减连接螺钉。螺钉长度按实物复核，尤其电机螺钉不得顶到绕组。','','|件号|规格/用途|数量|单重估计 g|合计 g|','|---|---|---:|---:|---:|']
for i,d,q,m in hardware:lines.append(f'|{i}|{d}|{q}|{m:.2f}|{q*m:.2f}|')
lines+=['','## 替代件，不能重复计入标准装机重量','','|件号|说明|质量 g|','|---|---|---:|']
for n,d in report['parts'].items():
    if d['optional']:lines.append(f'|{n}|{d["description"]}|{d["unit_mass_g"]:.2f}|')
lines+=['','O4/模拟图传板替换P07；P10云台接口板作为独立替代配置使用，不与P06R/P06L O4 Pro相机侧板重复计入。云台预留只包括接口，舵机、转轴和运动支架须另设计并单独计重。P14通用相机座及P11/P12/P13减径衬块按所选非O4 Pro相机配置追加。','',
'## 材料口径与采购下料','',
'- PLA按1.24 g/cm³，ABS按1.04 g/cm³，碳板/碳管统一按1.60 g/cm³预算。实际耗材和碳材的密度、铺层、树脂含量会变化，不能把此处密度当成供应商证书。',
'- 2mm碳板：C01/C02/C03/C04各1；可先按400×250mm毛坯排版，切割厂需用DXF核实刀缝、夹持和余料。',
'- 4mm碳板：C05/C06各1；建议410×210mm毛坯排版。侧板外形约194×173mm，两片并排；无沉头孔，保留厚度。',
'- 4mm碳板：C07×4；100×100mm毛坯可排4片36×36mm电机板。',
'- 两种碳管各买500mm标准料，分别截取420mm；主梁10/8、后梁6/4。用整根管，不在机身中心对接。余料可做胶接和嵌件试验。',
'- 碳板优先采购含0/90及±45铺层的实碳板；碳管优先有环向纤维的卷制管。不能以外观碳纹或单向拉挤细管替代而不重新验证。',
'- 2、4mm两种平板和直管可用常规二维切割及定尺切断，连接件复用相同打印件；成本主要来自小批量碳板切割，不需要5mm全机板或铝合金CNC大件。未取得本地报价，不给出虚构采购总价。','',
'## 整机重量如何估计','',
'完整起飞重量 = 本表机架重量 + 4电机 + 4桨 + 飞塔 + 图传/相机/天线 + 接收机/线材 + 电池 + 可选完整云台。','',
'仅用于预算的例子：四电机合计140g、四桨20g、飞塔35g、O4 Pro全套45g、接收机/线材25g、电池280g，则整机约 **'+f'{report["frame_estimate_g"]+140+20+35+45+25+280:.0f}'+' g**。这些电子/电池质量未经型号确认；不是大黄狗电池的厂家规格。换图传、电池或加云台后必须重新计算。','',
'## 材料参考','',
'- [Polymaker PLA技术数据](https://polymaker.com/wp-content/tech-docs/PolyLite_PLA_PIS_EN_V1.1.pdf)：PLA密度随产品/条件变化。',
'- [Easy Composites碳板](https://www.easycomposites.co.uk/high-strength-carbon-fibre-sheet)：解释准各向同性铺层及不同标称厚度的实际厚度公差。',
'- [卷制碳管的纵向与环向铺层说明](https://www.easycomposites.co.uk/8mm-woven-finish-carbon-fibre-tube)：仅用于材料构造参考，不把该8mm商品当成本BOM的10mm主梁。','']
(O/'BOM与重量预算.md').write_text('\n'.join(lines),encoding='utf-8')

rn=vtk.vtkRenderer();rn.SetBackground(.94,.96,.975)
manifest=json.loads((O/'render_manifest.json').read_text())
for d in manifest:
    rd=vtk.vtkSTLReader();rd.SetFileName(str(O/d['file']))
    norm=vtk.vtkPolyDataNormals();norm.SetInputConnection(rd.GetOutputPort());norm.SetFeatureAngle(60)
    mp=vtk.vtkPolyDataMapper();mp.SetInputConnection(norm.GetOutputPort())
    ac=vtk.vtkActor();ac.SetMapper(mp);ac.GetProperty().SetColor(*d['color']);rn.AddActor(ac)
def shape_actor(s,col):
    vv,tt=s.val().tessellate(.15);p=vtk.vtkPoints();cells=vtk.vtkCellArray()
    for v in vv:p.InsertNextPoint(v.x,v.y,v.z)
    for t in tt:
        cells.InsertNextCell(3)
        for j in t:cells.InsertCellPoint(j)
    pd=vtk.vtkPolyData();pd.SetPoints(p);pd.SetPolys(cells);m=vtk.vtkPolyDataMapper();m.SetInputData(pd)
    a=vtk.vtkActor();a.SetMapper(m);a.GetProperty().SetColor(*col);rn.AddActor(a)
shape_actor(cq.Workplane('XY').box(48,52,78).translate((0,47,-75)),(.85,.73,.12))
for x in [-145,145]:
    for y in [-78,78]:
        shape_actor(cq.Workplane('XY').circle(14).extrude(25).translate((x,y,16)),(.14,.15,.16))
        shape_actor(cq.Workplane('XY').circle(63.5).circle(62.7).extrude(.8).translate((x,y,46)),(.35,.42,.47))
tx=vtk.vtkTextActor();tx.SetInput(f'H440 B2 / HYBRID\nPLA wings + CFRP plates + continuous tube spars\nCAD structure {report["CAD_frame_mass_g"]:.0f} g; assembled frame budget 620 g')
tx.SetPosition(30,25);tx.GetTextProperty().SetFontSize(22);tx.GetTextProperty().SetColor(.18,.23,.28);rn.AddViewProp(tx)
rw=vtk.vtkRenderWindow();rw.SetOffScreenRendering(1);rw.SetSize(1500,1000);rw.AddRenderer(rn)
cam=rn.GetActiveCamera();cam.SetFocalPoint(0,0,-55);cam.SetViewUp(0,1,0);cam.ParallelProjectionOn()
for name,pos,scale in [('H440_B2_isometric.png',(480,340,550),265),('H440_B2_front.png',(0,0,800),240)]:
    cam.SetPosition(*pos);cam.SetParallelScale(scale);rn.ResetCameraClippingRange();rw.Render()
    cap=vtk.vtkWindowToImageFilter();cap.SetInput(rw);cap.Update();wr=vtk.vtkPNGWriter();wr.SetFileName(str(O/name));wr.SetInputConnection(cap.GetOutputPort());wr.Write()
rw.Finalize()
print(json.dumps({'frame_g':report['frame_estimate_g'],'CAD_g':report['CAD_frame_mass_g'],'hardware_g':hw,'battery_interference':travel,'DXF_count':len(dxfs)}),flush=True);os._exit(0)
