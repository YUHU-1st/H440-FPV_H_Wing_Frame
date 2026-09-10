import sys,os,json
from pathlib import Path
R=Path(__file__).parent;sys.path.insert(0,str(R/'.cad-deps'))
import cadquery as cq
O=R/'H440_A0';report=json.loads((O/'geometry_report.json').read_text(encoding='utf-8'))
for base,left in [('04_pylon_upper','04L_pylon_upper_left'),('05_pylon_lower','05L_pylon_lower_left')]:
    s=cq.importers.importStep(str(O/(base+'.step'))).mirror('YZ')
    cq.exporters.export(s,str(O/(left+'.step')))
    pr=s.rotate((0,0,0),(0,1,0),90);b=pr.val().BoundingBox();pr=pr.translate((-b.xmin,-b.ymin,-b.zmin))
    cq.exporters.export(pr,str(O/(left+'_print.stl')),tolerance=.04,angularTolerance=.15)
    report['parts'][base]['quantity']=1
    report['parts'][left]=dict(report['parts'][base])
# STEP import roundtrip confirms serialised printable parts remain single valid solids.
checks={}
for n in report['parts']:
    s=cq.importers.importStep(str(O/(n+'.step')))
    assert len(s.solids().vals())==1 and s.val().isValid(),n
    checks[n]=True
report['checks']['STEP_roundtrip_valid']=checks
report['checks']['exposed_wing_area_m2']=.05264
report['checks']['wing_area_m2']=.0616
report['checks']['wing_area_note']='0.0616 reference rectangle includes central open bay; exposed lifting panels 0.05264'
(O/'geometry_report.json').write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding='utf-8')
print('Verified',len(checks),'STEP part roundtrips; all valid single solids.',flush=True)
os._exit(0)
