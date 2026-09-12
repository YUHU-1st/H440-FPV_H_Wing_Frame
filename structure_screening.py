"""Comparative 3-D beam-network screening, not laminate or joint certification.

Units: N, mm, MPa. Fixed spar nodes; rigid beam junctions; no joint compliance.
Only compares the pylon skeleton. It does NOT model the whole aircraft modes.
"""
import sys, json, math
from pathlib import Path
R=Path(__file__).resolve().parent
sys.path.insert(0,str(R/'.cad-deps'))
import numpy as np

def local_k(L,A,Iy,Iz,J,E=32000,G=12000):
    k=np.zeros((12,12))
    for ids,v in [([0,6],E*A/L),([3,9],G*J/L)]:
        k[np.ix_(ids,ids)]+=v*np.array([[1,-1],[-1,1]])
    b=np.array([[12,6*L,-12,6*L],[6*L,4*L*L,-6*L,2*L*L],
                [-12,-6*L,12,-6*L],[6*L,2*L*L,-6*L,4*L*L]])
    k[np.ix_([1,5,7,11],[1,5,7,11])]+=E*Iz/L**3*b
    d=np.diag([1,-1,1,-1])
    k[np.ix_([2,4,8,10],[2,4,8,10])]+=E*Iy/L**3*(d@b@d)
    return k

# Cantilever sanity checks against closed-form bending, both directions.
k=local_k(100,24,32,128,80)
for axis,I in [(1,128),(2,32)]:
    f=np.zeros(6);f[axis]=10
    u=np.linalg.solve(k[6:,6:],f)
    assert abs(u[axis]-10*100**3/(3*32000*I))<1e-9

def solve(new):
    A=(0,-44); B=(0,-98); C=(78,0); D=(83,-161)
    seg=[(A,C,8 if new else 6),(B,D,8 if new else 6),
         (C,D,8 if new else 6),(B,C,8 if new else 5)]
    if new:seg.append((A,D,6))
    seg += [((-a[0],a[1]),(-b[0],b[1]),w) for a,b,w in seg]
    seg.append((A,B,14))
    nodes=[]; elems=[]
    def node(p):
        p=tuple(round(v,7) for v in p)
        if p not in nodes:nodes.append(p)
        return nodes.index(p)
    def cross(a,b):return a[0]*b[1]-a[1]*b[0]
    for a,b,w in seg:
        a=np.array(a,dtype=float);v=np.array(b)-a;cuts=[0.,1.]
        for c,d,_ in seg:
            c=np.array(c,dtype=float);vv=np.array(d)-c;den=cross(v,vv)
            if abs(den)<1e-10:continue
            s=cross(c-a,vv)/den;tt=cross(c-a,v)/den
            if -1e-9<=s<=1+1e-9 and -1e-9<=tt<=1+1e-9:cuts.append(round(float(s),9))
        cuts=sorted(set(cuts))
        for s,tt in zip(cuts,cuts[1:]):
            if tt-s>1e-8:elems.append((node(a+s*v),node(a+tt*v),w))
    t=4 if new else 3
    K=np.zeros((6*len(nodes),6*len(nodes))); members=[]
    for i,j,w in elems:
        p=np.array([0,*nodes[i]]);q=np.array([0,*nodes[j]])
        L=np.linalg.norm(q-p);ex=(q-p)/L;ez=np.array([1.,0,0]);ey=np.cross(ez,ex)
        rot=np.array([ex,ey,ez]);T=np.zeros((12,12))
        for b in [0,3,6,9]:T[b:b+3,b:b+3]=rot
        J=w*t**3*(1/3-.21*(t/w)*(1-t**4/(12*w**4)))
        ke=T.T@local_k(L,w*t,w*t**3/12,t*w**3/12,J)@T
        ids=list(range(6*i,6*i+6))+list(range(6*j,6*j+6))
        K[np.ix_(ids,ids)]+=ke
        members.append((ids,T,local_k(L,w*t,w*t**3/12,t*w**3/12,J),w))
    fixed=[6*nodes.index(p)+j for p in [A,B] for j in range(6)]
    free=np.array([j for j in range(len(K)) if j not in fixed])
    motor=[nodes.index(C),nodes.index((-78,0))]
    cases={}
    for name,axis,force,opposed in [('thrust_each_15N',2,15,False),
                                   ('differential_thrust_15N',2,15,True),
                                   ('lateral_each_3N',0,3,False),
                                   ('motor_torque_150Nmm',5,150,True)]:
        F=np.zeros(len(K))
        for m,n in enumerate(motor):F[n*6+axis]=force*(-1 if opposed and m else 1)
        u=np.zeros(len(K));u[free]=np.linalg.solve(K[np.ix_(free,free)],F[free])
        residual=K@u-F
        assert np.max(np.abs(residual[free]))<1e-6
        peak=0.
        for ids,T,kl,w in members:
            forces=kl@T@u[ids]
            for end in [0,6]:
                stress=abs(forces[end])/(w*t)+abs(forces[end+4])*(t/2)/(w*t**3/12)+abs(forces[end+5])*(w/2)/(t*w**3/12)
                peak=max(peak,stress)
        cases[name]={'beam_extreme_fiber_stress_MPa_no_hole_concentration':float(peak),
                     'max_motor_translation_mm':float(max(np.linalg.norm(u[n*6:n*6+3]) for n in motor)),
                     'max_motor_rotation_deg':float(max(np.linalg.norm(u[n*6+3:n*6+6]) for n in motor)*180/math.pi)}
    return {'nodes':len(nodes),'elements':len(elems),'cases':cases}

result={'scope':'fixed-root ideal 3D beam pylon screening; not complete-aircraft FEA',
        'assumed_E_MPa':32000,'assumed_G_MPa':12000,
        'loads_are_assumptions_not_measured_motor_data':True,
        'baseline':solve(False),'reinforced':solve(True),
        'section_out_of_plane_EI_ratio_8x4_vs_6x3':8*4**3/(6*3**3),
        'bolt_group_polar_sum_mm2_old':2*7**2,
        'bolt_group_polar_sum_mm2_new':4*(14**2+5**2),
        'cantilever_closed_form_self_check':'passed'}
(R/'H440_B2/structure_screening.json').write_text(json.dumps(result,indent=2),encoding='utf-8')
print(json.dumps(result,indent=2))
