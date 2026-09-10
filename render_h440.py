import sys,os
from pathlib import Path
ROOT=Path(__file__).parent
sys.path.insert(0,str(ROOT/'.cad-deps'))
import cadquery as cq
import vtk
O=ROOT/'H440_A0'
rn=vtk.vtkRenderer();rn.SetBackground(.94,.955,.965)
def actor(s,c,opacity=1):
    vv,tt=s.val().tessellate(.12)
    pts=vtk.vtkPoints();cells=vtk.vtkCellArray()
    for v in vv:pts.InsertNextPoint(v.x,v.y,v.z)
    for t in tt:
        cells.InsertNextCell(3)
        for i in t:cells.InsertCellPoint(i)
    pd=vtk.vtkPolyData();pd.SetPoints(pts);pd.SetPolys(cells)
    normals=vtk.vtkPolyDataNormals();normals.SetInputData(pd);normals.SetFeatureAngle(50)
    mp=vtk.vtkPolyDataMapper();mp.SetInputConnection(normals.GetOutputPort())
    ac=vtk.vtkActor();ac.SetMapper(mp);ac.GetProperty().SetColor(*c);ac.GetProperty().SetOpacity(opacity)
    ac.GetProperty().SetSpecular(.25);ac.GetProperty().SetSpecularPower(30);rn.AddActor(ac)
for name,c in [('01_center_cradle',(.19,.22,.26)),('02_wing_right',(.08,.57,.68)),('03_wing_left',(.08,.57,.68)),('06_electronics_deck',(.28,.31,.36)),('07_vtx_O4Pro_25p5_M2',(.5,.53,.55)),('10_camera_cradle_26clear',(.95,.43,.12))]:actor(cq.importers.importStep(str(O/(name+'.step'))),c)
for name in ['04_pylon_upper','05_pylon_lower']:
    s=cq.importers.importStep(str(O/(name+'.step')))
    actor(s,(.95,.43,.12));actor(s.mirror('YZ'),(.95,.43,.12))
for x in [-145,145]:
    for y in [-78,78]:
        actor(cq.Workplane('XY').circle(14).extrude(25).translate((x,y,17)),(.12,.13,.15))
        actor(cq.Workplane('XY').circle(63.5).circle(62.5).extrude(.8).translate((x,y,46)),(.4,.49,.54))
actor(cq.Workplane('XY').box(48,52,78).translate((0,4,-63)),(.86,.72,.1))
actor(cq.Workplane('XY').box(36,23,36).translate((0,-55,-83)),(.12,.4,.18))
actor(cq.Workplane('XY').box(33.5,13,33.5).translate((0,-54,-33)),(.18,.2,.23))
actor(cq.Workplane('XY').box(25.55,20,23.3).translate((0,-10,13)),(.12,.13,.15))
tx=vtk.vtkTextActor();tx.SetInput('H440 / A0\n440 mm span | 127 mm prop disks\nDimensional prototype - hardware envelopes are references')
tx.SetPosition(35,30);tx.GetTextProperty().SetFontSize(22);tx.GetTextProperty().SetColor(.18,.23,.29);rn.AddActor2D(tx)
rw=vtk.vtkRenderWindow();rw.SetOffScreenRendering(1);rw.SetSize(1500,1000);rw.AddRenderer(rn)
cam=rn.GetActiveCamera();cam.SetFocalPoint(0,0,-55);cam.SetViewUp(0,1,0);cam.ParallelProjectionOn()
for name,pos,scale in [('H440_isometric.png',(480,320,550),265),('H440_front.png',(0,0,800),245)]:
    cam.SetPosition(*pos);cam.SetParallelScale(scale);rn.ResetCameraClippingRange();rw.Render()
    capture=vtk.vtkWindowToImageFilter();capture.SetInput(rw);capture.Update()
    writer=vtk.vtkPNGWriter();writer.SetFileName(str(O/name));writer.SetInputConnection(capture.GetOutputPort());writer.Write()
rw.Finalize();print('Rendered',flush=True);os._exit(0)
