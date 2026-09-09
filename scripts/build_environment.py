"""Authored Knarkrondellen architecture and furniture, made in Blender.
Run: Blender --background --python scripts/build_environment.py
Coordinates here are x=east, y=north, z=up. glTF converts to game Y-up.
"""
import bpy, bmesh, math, random, json, os
from mathutils import Vector
from collections import defaultdict
from pathlib import Path
random.seed(412)
ROOT=Path(__file__).resolve().parents[1]
bpy.ops.object.select_all(action='SELECT'); bpy.ops.object.delete(use_global=False)
groups=defaultdict(lambda: [[],[],[],[]])
mats={}
collisions=[]

def material(name,col,rough=.7,metal=0,emission=0,texture=False):
    m=bpy.data.materials.new(name); m.use_nodes=True
    bs=m.node_tree.nodes.get('Principled BSDF')
    bs.inputs['Base Color'].default_value=(*col,1)
    bs.inputs['Roughness'].default_value=rough
    bs.inputs['Metallic'].default_value=metal
    if emission:
        bs.inputs['Emission Color'].default_value=(*col,1);bs.inputs['Emission Strength'].default_value=emission
    if texture:
        import numpy as np
        N=256; rng=np.random.default_rng(abs(sum(map(ord,name))))
        a=rng.random((N,N)); coarse=rng.random((16,16))
        coarse=np.repeat(np.repeat(coarse,16,0),16,1)
        # Blend fine mineral grain with broad patinated colour variation.
        for _ in range(18): coarse=(coarse+np.roll(coarse,1,0)+np.roll(coarse,-1,0)+np.roll(coarse,1,1)+np.roll(coarse,-1,1))/5
        v=.77+.20*coarse+.10*a
        pix=np.ones((N,N,4),dtype=np.float32)
        for c in range(3):pix[:,:,c]=np.clip(col[c]*v,0,1)
        img=bpy.data.images.new(name+'_HandmadeSurface',width=N,height=N)
        img.pixels.foreach_set(pix.ravel()); img.pack()
        tx=m.node_tree.nodes.new('ShaderNodeTexImage');tx.image=img
        m.node_tree.links.new(tx.outputs['Color'],bs.inputs['Base Color'])
    mats[name]=m
    return name

material('Plaster_Ochre',(.52,.35,.17),.92,texture=True)
material('Plaster_Sand',(.53,.46,.33),.92,texture=True)
material('Plaster_Rust',(.39,.24,.17),.94,texture=True)
material('Stone_Trim',(.41,.40,.35),.83,texture=True)
material('Stone_Dark',(.18,.185,.17),.9,texture=True)
material('Roof_Slate',(.10,.145,.155),.48,.25,texture=True)
material('Copper_Oxide',(.21,.25,.19),.48,.52,texture=True)
material('Window_Frame',(.105,.125,.125),.52,.2)
material('Window_Dark',(.035,.067,.082),.23,.3)
material('Window_Lit',(.93,.50,.15),.62,0,1.2)
material('Window_Dim',(.45,.27,.12),.72,0,.55)
material('Curtains',(.065,.042,.027),1)
mats['Curtains'].node_tree.nodes.get('Principled BSDF').inputs['Specular IOR Level'].default_value=.08
material('Interior_Amber',(.72,.285,.074),1,0,.48)
material('Interior_Honey',(.65,.405,.16),1,0,.42)
material('Iron',(.063,.085,.08),.48,.7)
material('Bench_Wood',(.235,.13,.064),.84,texture=True)
material('Bench_Wood_Pale',(.275,.155,.079),.87,texture=True)
material('Bark',(.17,.115,.077),.98,texture=True)
if (ROOT/'public/assets/tree-bark.png').exists():
    bark_image=bpy.data.images.load(str(ROOT/'public/assets/tree-bark.png'));bark_image.pack()
    bark_nodes=mats['Bark'].node_tree.nodes;tx=bark_nodes.new('ShaderNodeTexImage');tx.image=bark_image
    bark_bs=bark_nodes.get('Principled BSDF');mats['Bark'].node_tree.links.new(tx.outputs['Color'],bark_bs.inputs['Base Color'])
    bark_bs.inputs['Specular IOR Level'].default_value=.08

material('Brick',(.265,.125,.082),.88,texture=True)
material('Graffiti_Wall',(.19,.20,.185),.97,texture=True)
material('Paint_Cream',(.57,.56,.42),.94)
material('Paint_Silver',(.35,.47,.45),.87)
material('Paint_Pink',(.30,.12,.17),.95)
material('Paint_Olive',(.23,.29,.12),.93)
material('Lamp_Glass',(1,.59,.20),.25,0,3)
material('Facade_Patina',(.16,.13,.09),1)
import numpy as np
N=256;yy,xx=np.mgrid[0:N,0:N].astype(np.float32);xx=(xx+.5)/N;yy=(yy+.5)/N
rng=np.random.default_rng(938);alpha=np.zeros((N,N),dtype=np.float32)
for j in range(12):
    xpos=rng.uniform(.10,.90);width=rng.uniform(.01,.055);bottom=rng.uniform(.05,.70)
    length=np.clip((yy-bottom)/.13,0,1)*np.clip((1-yy)/.08,0,1)
    curve=xpos+.018*np.sin(yy*8+j)
    alpha+=np.exp(-((xx-curve)/width)**2)*length*rng.uniform(.22,.43)
noise=rng.random((N,N));alpha*=.62+.38*noise
alpha*=np.clip(xx/.10,0,1)*np.clip((1-xx)/.10,0,1);alpha=np.clip(alpha,0,.58)
pix=np.ones((N,N,4),dtype=np.float32);pix[:,:,:3]=(.16,.13,.09);pix[:,:,3]=alpha
patina=bpy.data.images.new('Embedded rain staining',width=N,height=N,alpha=True);patina.pixels.foreach_set(pix.ravel());patina.pack()
nodes=mats['Facade_Patina'].node_tree.nodes;tx=nodes.new('ShaderNodeTexImage');tx.image=patina
bs=nodes.get('Principled BSDF');mats['Facade_Patina'].node_tree.links.new(tx.outputs['Color'],bs.inputs['Base Color']);mats['Facade_Patina'].node_tree.links.new(tx.outputs['Alpha'],bs.inputs['Alpha'])
mats['Facade_Patina'].surface_render_method='DITHERED'
material('Facade_BaseWear',(.105,.11,.08),1)
basewear=bpy.data.images.new('Embedded rising damp and street dirt',width=N,height=N,alpha=True)
coarse=rng.random((16,16));coarse=np.repeat(np.repeat(coarse,16,0),16,1)
for _ in range(14):coarse=(coarse+np.roll(coarse,1,0)+np.roll(coarse,-1,0)+np.roll(coarse,1,1)+np.roll(coarse,-1,1))/5
fade=np.clip((.84+.13*np.sin(xx*12)-yy)/.62,0,1)
pix2=np.ones((N,N,4),dtype=np.float32);pix2[:,:,:3]=(.105,.11,.08);pix2[:,:,3]=fade*(.30+.28*coarse)*(.83+.17*noise)
basewear.pixels.foreach_set(pix2.ravel());basewear.pack();m=mats['Facade_BaseWear'];tx=m.node_tree.nodes.new('ShaderNodeTexImage');tx.image=basewear;bs=m.node_tree.nodes.get('Principled BSDF')
m.node_tree.links.new(tx.outputs['Color'],bs.inputs['Base Color']);m.node_tree.links.new(tx.outputs['Alpha'],bs.inputs['Alpha']);m.surface_render_method='DITHERED';bs.inputs['Specular IOR Level'].default_value=.06



def mesh(mat,verts,faces,group='Environment',uv=None):
    key=(group,mat);v,f,uvs,smooth=groups[key]; n=len(v);v.extend(verts)
    for face in faces:
        f.append(tuple(n+i for i in face));smooth.append(False)
        for i in face:
            q=verts[i]
            uvs.append(uv[i] if uv else (q[0]*.4+q[1]*.11,q[2]*.4+q[1]*.27))

def box(mat,loc,size,angle=0,group='Environment'):
    if group=='Benches' and mat.startswith('Bench_Wood'):
        bm=bmesh.new();bmesh.ops.create_cube(bm,size=1)
        for v in bm.verts:v.co.x*=size[0];v.co.y*=size[1];v.co.z*=size[2]
        bmesh.ops.bevel(bm,geom=list(bm.edges),offset=.004,segments=2,affect='EDGES')
        bm.verts.ensure_lookup_table();bm.verts.index_update()
        cs=math.cos(angle);sn=math.sin(angle);x,y,z=loc
        vv=[(x+v.co.x*cs-v.co.y*sn,y+v.co.x*sn+v.co.y*cs,z+v.co.z) for v in bm.verts]
        ff=[tuple(v.index for v in f.verts) for f in bm.faces];mesh(mat,vv,ff,group);bm.free();return
    x,y,z=loc;a,b,c=(s*.5 for s in size);cs=math.cos(angle);sn=math.sin(angle)
    vv=[(x+u*cs-v*sn,y+u*sn+v*cs,z+w) for u,v,w in [(-a,-b,-c),(a,-b,-c),(a,b,-c),(-a,b,-c),(-a,-b,c),(a,-b,c),(a,b,c),(-a,b,c)]]
    mesh(mat,vv,[(0,3,2,1),(0,1,5,4),(1,2,6,5),(2,3,7,6),(3,0,4,7),(4,5,6,7)],group)

def tube(mat,points,radii,n=8,group='Environment'):
    if mat=='Bark':
        bark_tube(points,radii,n,group);return
    vv=[]
    for i,p in enumerate(points):
        p=Vector(p);direction=Vector(points[min(i+1,len(points)-1)])-Vector(points[max(0,i-1)])
        direction.normalize();u=direction.cross(Vector((0,0,1)))
        if u.length<.01:u=Vector((1,0,0))
        u.normalize();v=direction.cross(u).normalized()
        for j in range(n):
            a=j*math.tau/n; q=p+radii[i]*(math.cos(a)*u+math.sin(a)*v);vv.append(tuple(q))
    faces=[tuple(range(n-1,-1,-1))]
    for i in range(len(points)-1):
        for j in range(n):faces.append((i*n+j,i*n+(j+1)%n,(i+1)*n+(j+1)%n,(i+1)*n+j))
    faces.append(tuple((len(points)-1)*n+j for j in range(n)))
    mesh(mat,vv,faces,group)

def bark_tube(points,radii,n,group):
    detailed=group.startswith('Tree_')
    points=[Vector(p) for p in points]
    # Catmull-Rom centreline gives major forks a grown, rounded transition.
    if detailed and max(radii)>.035 and len(points)>2:
        pp=[];rr=[]
        for i in range(len(points)-1):
            p0=points[max(0,i-1)];p1=points[i];p2=points[i+1];p3=points[min(len(points)-1,i+2)]
            for j in range(3):
                t=j/3;pp.append(.5*((2*p1)+(-p0+p2)*t+(2*p0-5*p1+4*p2-p3)*t*t+(-p0+3*p1-3*p2+p3)*t*t*t))
                rr.append(radii[i]*(1-t)+radii[i+1]*t)
        pp.append(points[-1]);rr.append(radii[-1]);points=pp;radii=rr
    n=max(n,32 if detailed and max(radii)>.16 else (16 if detailed and max(radii)>.045 else n))
    vv=[];uv=[];distance=0;around=max(1,math.tau*max(radii)/.65)
    for i,p in enumerate(points):
        if i:distance+=(p-points[i-1]).length
        direction=(points[min(i+1,len(points)-1)]-points[max(0,i-1)]).normalized()
        # Stable longitudinal frame avoids spinning the bark texture at forks.
        u=direction.cross(Vector((0,1,0)))
        if u.length<.05:u=direction.cross(Vector((1,0,0)))
        u.normalize();v=direction.cross(u).normalized()
        for j in range(n+1):
            a=j*math.tau/n;rad=radii[i]
            if detailed:
                variation=.09*math.sin(a*3+.37+distance*.7)+.045*math.cos(a*5-distance*.4)
                relief=min(.006,rad*.06)*math.sin(a*8+distance*.6)
                rad=rad*(1+variation)+relief
            q=p+rad*(math.cos(a)*u+math.sin(a)*v);vv.append(tuple(q));uv.append((j/n*around,distance/1.3))
    fs=[tuple(range(n-1,-1,-1))];stride=n+1
    for i in range(len(points)-1):
        for j in range(n):fs.append((i*stride+j,i*stride+j+1,(i+1)*stride+j+1,(i+1)*stride+j))
    fs.append(tuple((len(points)-1)*stride+j for j in range(n)))
    mesh('Bark',vv,fs,group,uv)

def sphere(mat,loc,r,group='Environment'):
    x,y,z=loc;vv=[];segments=10;rings=6
    for i in range(rings+1):
        lat=math.pi*i/rings
        for j in range(segments):
            a=math.tau*j/segments;vv.append((x+r*math.sin(lat)*math.cos(a),y+r*math.sin(lat)*math.sin(a),z+r*math.cos(lat)))
    faces=[]
    for i in range(rings):
        for j in range(segments):faces.append((i*segments+j,i*segments+(j+1)%segments,(i+1)*segments+(j+1)%segments,(i+1)*segments+j))
    mesh(mat,vv,faces,group)

def polar(r,a,z):return(r*math.cos(a),r*math.sin(a),z)

def band(mat,r1,r2,a1,a2,z1,z2,group,steps=80):
    vv=[]
    for j in range(steps+1):
        a=a1+(a2-a1)*j/steps
        for r,z in [(r1,z1),(r2,z1),(r2,z2),(r1,z2)]:vv.append(polar(r,a,z))
    faces=[(3,2,1,0)]
    for j in range(steps):
        for k in range(4):faces.append((j*4+k,j*4+(k+1)%4,(j+1)*4+(k+1)%4,(j+1)*4+k))
    faces.append(tuple(steps*4+i for i in range(4)));mesh(mat,vv,faces,group)

def fbox(mat,r,a,z,w,d,h,group):box(mat,polar(r,a,z),(w,d,h),a+math.pi/2,group)

def arch(mat,r,a,z,w,h,thickness,group):
    # Classical arched lintel, individually jointed voussoirs.
    for j in range(13):
        t=math.pi*j/12; lx=math.cos(t)*w/2;lz=math.sin(t)*h
        pos=Vector(polar(r,a,z));pos+=Vector((-math.sin(a),math.cos(a),0))*lx;pos.z+=lz
        # Moulding follows arch via tube, next segment below.
        if j<12:
            t2=math.pi*(j+1)/12;p2=Vector(polar(r,a,z));p2+=Vector((-math.sin(a),math.cos(a),0))*(math.cos(t2)*w/2);p2.z+=math.sin(t2)*h
            tube(mat,[pos,p2],[thickness,thickness],6,group)

def balcony(r,a,z,group):
    fbox('Stone_Dark',r-.63,a,z,2.15,1.5,.18,group)
    for x in [-1.02,1.02]:
        for y in [0,-1.35]:
            base=Vector(polar(r+y,a,z+.1))+Vector((-math.sin(a),math.cos(a),0))*x
            tube('Iron',[base,base+Vector((0,0,1))],[.035,.035],6,group)
    for j in range(14):
        x=-1.04+j*2.08/13;base=Vector(polar(r-1.35,a,z+.1))+Vector((-math.sin(a),math.cos(a),0))*x
        tube('Iron',[base,base+Vector((0,0,.95))],[.016,.016],5,group)
    for zz in [.2,.92,1.08]:
        fbox('Iron',r-1.35,a,z+zz,2.15,.045,.04,group)
        for side in [-1,1]:
            p=Vector(polar(r-.68,a,z+zz))+Vector((-math.sin(a),math.cos(a),0))*side*1.04
            box('Iron',p,(.04,1.4,.045),a+math.pi/2,group)
    for side in [-.75,.75]:
        p=Vector(polar(r,a,z-.7))+Vector((-math.sin(a),math.cos(a),0))*side
        q=Vector(polar(r-1.05,a,z-.1))+Vector((-math.sin(a),math.cos(a),0))*side
        tube('Iron',[p,q],[.04,.035],6,group)

def window_interior(group,r,a,z,w,h,lit,floor,index):
    # Independent RNG: architectural decoration never moves existing trees/props.
    rng=random.Random(group+str(floor)+'-'+str(index))
    tangent=Vector((-math.sin(a),math.cos(a),0));radial=Vector((math.cos(a),math.sin(a),0))
    # Actual 45 cm-deep reveals frame the room seen behind the glazing.
    for side in [-1,1]:
        p=Vector(polar(r+.29,a,z))+tangent*side*(w/2-.04)
        box('Stone_Dark',p,(.055,.43,h),a+math.pi/2,group)
    fbox('Stone_Dark',r+.28,a,z-h/2+.027,w,.44,.05,group)
    if not lit and rng.random()<.75:return
    if lit and rng.random()<.67:
        tone=rng.choice(['Interior_Amber','Interior_Honey'])
        fbox(tone,r+.503,a,z,w-.115,.006,h-.13,group)
    # Hanging side curtains are narrow dark fabric, with gentle modeled pleats.
    for side in [-1,1]:
        width=w*rng.uniform(.10,.19);center=side*(w*.45-width*.45)
        vv=[];steps=8
        for j in range(steps+1):
            u=center+(j/steps-.5)*width;fold=math.sin(j/steps*math.pi*4)*.025
            for v in [-h*.46,h*.47]:
                p=Vector(polar(r+.29+fold,a,z+v))+tangent*u
                if v<0:p.z+=.02*math.cos(j*.9)
                vv.append(tuple(p))
        fs=[]
        for j in range(steps):fs.append((j*2,j*2+1,(j+1)*2+1,(j+1)*2))
        mesh('Curtains',vv,fs,group)
    if lit and rng.random()<.48:
        # Sparse bookcase/table silhouettes give believable room scale.
        offset=rng.uniform(-.25,.25)*w
        p=Vector(polar(r+.44,a,z-.52))+tangent*offset
        box('Curtains',p,(w*.46,.035,.065),a+math.pi/2,group)
        for side in [-1,1]:
            q=p+tangent*side*w*.18-Vector((0,0,.22))
            box('Curtains',q,(.029,.035,.40),a+math.pi/2,group)
        if rng.random()<.65:
            q=p+Vector((0,0,.13))+tangent*w*.10
            box('Curtains',q,(.14,.055,.25),a+math.pi/2,group)
    if floor==0 and index%4==0:
        # Shallow open ventilation grille below selected ground-floor windows.
        fbox('Stone_Dark',r-.021,a,.89,.58,.05,.22,group)
        for j in range(7):
            p=Vector(polar(r-.052,a,.89))+tangent*(-.24+j*.08)
            box('Iron',p,(.018,.025,.18),a+math.pi/2,group)

def building(name,r,start,end,mat,height=17.5):
    a1,a2=map(math.radians,(start,end));arc=r*(a2-a1);bays=round(arc/2.85);step=(a2-a1)/bays
    # Curved wall volumes are constructed around real window openings.
    band('Stone_Dark',r,r+8,a1,a2,.02,.65,name)
    for zlo,zhi in [(.65,1.2),(3.1,4.25),(6.15,7.35),(9.25,10.45),(12.35,13.55),(15.45,height)]:
        band(mat,r,r+8,a1,a2,zlo,zhi,name)
    # Rear shell and side return walls keep every rotated view convincing.
    band(mat,r+7.8,r+8,a1,a2,.6,height,name)
    for a in [a1,a2]:fbox(mat,r+4,a,height/2,.3,8,height,name)
    for i in range(bays+1):
        a=a1+i*step
        for zlo,zhi in [(1.2,3.1),(4.25,6.15),(7.35,9.25),(10.45,12.35),(13.55,15.45)]:
            band(mat,r,r+.45,a-step*.30,a+step*.30,zlo,zhi,name,4)
    for floor,z in enumerate([2.15,5.20,8.30,11.40,14.50]):
        for i in range(bays):
            a=a1+(i+.5)*step;w=step*r*.40;h=1.9
            fbox('Window_Frame',r+.62,a,z,w+.10,.15,h+.10,name)
            lit=random.random()<(.38 if floor else .58)
            window='Window_Lit' if lit and random.random()<.67 else ('Window_Dim' if lit else 'Window_Dark')
            fbox(window,r+.525,a,z,w-.09,.022,h-.09,name)
            window_interior(name,r,a,z,w,h,lit,floor,i)
            # Thin projecting wooden mullions, transom and weathered stone sill.
            fbox('Window_Frame',r+.10,a,z,.055,.08,h,name)
            fbox('Window_Frame',r+.10,a,z+.39,w,.085,.052,name)
            for side in [-1,1]:
                p=Vector(polar(r+.11,a,z))+Vector((-math.sin(a),math.cos(a),0))*(w/2-.035)*side
                box('Window_Frame',p,(.065,.09,h),a+math.pi/2,name)
            for zz in [-h/2,h/2]:fbox('Window_Frame',r+.10,a,z+zz,w,.08,.065,name)
            fbox('Stone_Trim',r-.16,a,z-h/2-.11,w+.29,.38,.14,name)
            fbox(mat,r-.03,a,z+h/2+.09,w+.23,.12,.13,name)
            if lit:
                # Asymmetric partially closed curtains break identical luminous grids.
                side=random.choice([-1,1]);p=Vector(polar(r+.40,a,z))+Vector((-math.sin(a),math.cos(a),0))*(w*.39)*side
                box('Curtains',p,(w*.13,.015,h-.08),a+math.pi/2,name)
                if random.random()<.5:fbox('Curtains',r+.40,a,z+.84,w-.08,.015,.13,name)
            if floor in [1,2,3] and i%6==2:balcony(r-.22,a,z-1.05,name)
            if floor==1 and i%3==0:
                fbox('Stone_Trim',r-.055,a,z-1.44,w+.08,.1,.45,name)
                for j in range(3):fbox(mat,r-.13,a,z-1.57+j*.1,w-.12,.055,.025,name)
    for z,w,h in [(.6,.25,.16),(3.5,.21,.14),(6.56,.10,.10),(15.95,.21,.17),(16.18,.36,.14),(17.35,.4,.25)]:
        band('Stone_Trim' if z<4 else mat,r-w,r+.05,a1,a2,z,z+h,name)
    # Traditional segmented slate roof with raised standing seams.
    band('Roof_Slate',r-.35,r+8.3,a1,a2,height,height+.18,name)
    vv=[];ff=[];N=bays*5
    for i in range(N+1):
        a=a1+(a2-a1)*i/N
        for rad,z in [(r-.25,height+.18),(r+2.3,height+3.25),(r+5.6,height+3.25),(r+8.25,height+.18)]:vv.append(polar(rad,a,z))
    for i in range(N):
        for j in range(3):ff.append((i*4+j,i*4+j+1,(i+1)*4+j+1,(i+1)*4+j))
    mesh('Roof_Slate',vv,ff,name)
    for i in range(N+1):
        a=a1+(a2-a1)*i/N
        tube('Copper_Oxide',[polar(r-.25,a,height+.2),polar(r+2.3,a,height+3.28)],[.022,.022],5,name)
    for j in range(4):
        rad=r+.1+j*.6;zz=height+.2+(rad-(r-.25))/2.55*3.05
        band('Copper_Oxide',rad-.025,rad+.025,a1,a2,zz,zz+.025,name)
    for i in range(bays):
        a=a1+(i+.5)*step
        if i%3==0:
            fbox(mat,r+1.1,a,height+1.2,1.35,1.5,1.7,name)
            fbox('Window_Frame',r+.31,a,height+1.25,1.05,.09,1.16,name)
            fbox('Window_Dark',r+.25,a,height+1.25,.88,.035,.98,name)
            fbox('Stone_Trim',r+.18,a,height+1.25,.055,.05,1.02,name)
            fbox('Copper_Oxide',r+1.05,a,height+2.10,1.65,1.85,.16,name)
        if i%5==0:
            fbox('Brick',r+4.5,a,height+3.5,.9,1.2,2,name)
            fbox('Stone_Dark',r+4.5,a,height+4.54,1.06,1.34,.16,name)
        if i%7==0:
            # Drainpipes with discrete collars.
            tube('Copper_Oxide',[polar(r-.13,a,.1),polar(r-.13,a,16.5),polar(r-.5,a,17.5)],[.055,.055,.055],8,name)
            for z in [1,4,7,10,13,16]:fbox('Iron',r-.14,a,z,.18,.14,.08,name)
    # Individual ornamental doorways with carved arch and fanlight.
    for i in range(2,bays,7):
        a=a1+(i+.5)*step
        fbox('Stone_Dark',r-.16,a,1.5,1.8,.18,3,name)
        fbox('Bench_Wood',r-.29,a,1.31,1.42,.07,2.45,name)
        for side in [-1,1]:
            p=Vector(polar(r-.34,a,1.28))+Vector((-math.sin(a),math.cos(a),0))*side*.38
            box('Window_Dim',p,(.54,.026,1.54),a+math.pi/2,name)
        fbox('Window_Frame',r-.365,a,1.3,.06,.045,2.6,name)
        for z in [.5,1.95]:fbox('Stone_Dark',r-.37,a,z,1.44,.07,.1,name)
        for side in [-1,1]:
            p=Vector(polar(r-.42,a,1.3))+Vector((-math.sin(a),math.cos(a),0))*side*.12
            tube('Copper_Oxide',[p,p+Vector((0,0,.25))],[.018,.018],6,name)
        arch('Stone_Trim',r-.32,a,2.45,1.8,.74,.095,name)
        for side in [-1,1]:
            p=Vector(polar(r-.33,a,1.23))+Vector((-math.sin(a),math.cos(a),0))*side*.94
            box('Stone_Trim',p,(.20,.23,2.46),a+math.pi/2,name)
        fbox('Stone_Trim',r-.50,a,.10,2.08,.90,.2,name)
        # Small warm wall lantern adjacent to entrance.
        la=a+.052;fbox('Iron',r-.35,la,2.95,.20,.35,.55,name)
        fbox('Lamp_Glass',r-.51,la,2.95,.14,.15,.34,name)
        fbox('Iron',r-.49,la,3.18,.27,.29,.10,name)
    collisions.append({'type':'arc','radius':r,'start':start,'end':end})

building('Building_North',27,39,134,'Plaster_Ochre')
building('Building_West',29,151,218,'Plaster_Sand')
# Far blocks continue beyond the bounded roundabout, with street gaps.
building('Building_Distant',49,-7,25,'Plaster_Rust')
building('Building_South',53,241,298,'Plaster_Sand')

# Weathered lower masonry: restrained rustication and rain marks under sills.
for group,r,start,end in [('Building_North',27,39,134),('Building_West',29,151,218)]:
    aa,ab=map(math.radians,(start,end));bays=round(r*(ab-aa)/2.85);step=(ab-aa)/bays
    for j in range(bays):
        a=aa+(j+.5)*step;w=step*r*.4
        # Fine joints in the granite base, with subtly offset courses.
        for z0 in [.21,.42]:
            band('Stone_Trim',r-.012,r-.002,a-step*.48,a+step*.48,z0,z0+.012,group,3)
        for offset in [-.42,0,.42]:
            for z0 in [.115,.325,.525]:
                ang=a+step*(offset+(.18 if z0==.325 else 0))
                fbox('Stone_Trim',r-.014,ang,z0,.012,.02,.18,group)
        vv=[];width=step*r*.98
        for u,v in [(-width/2,.015),(width/2,.015),(width/2,.57),(-width/2,.57)]:vv.append(polar(r-.022,a+u/r,v))
        mesh('Facade_BaseWear',vv,[(0,3,2,1)],group,[(0,0),(1,0),(1,1),(0,1)])
        # Soft stained plaster below projecting ground-floor and first-floor sills.
        for height,drop in [(1.1,.28),(4.13,.24),(7.22,.20)]:
            if (j+round(height))%3==0:continue
            z=height-drop/2;width=w+.18;vv=[]
            for u,v in [(-width/2,-drop/2),(width/2,-drop/2),(width/2,drop/2),(-width/2,drop/2)]:
                vv.append(polar(r-.009,a+u/r,z+v))
            mesh('Facade_Patina',vv,[(0,3,2,1)],group,[(0,0),(1,0),(1,1),(0,1)])

# The Jugendstil roof silhouette in the photographs: a curved central gable and
# copper-capped corner bays, individually modeled rather than a flat texture.
def gable(r,a):
    group='Building_North';tangent=Vector((-math.sin(a),math.cos(a),0));normal=Vector((math.cos(a),math.sin(a),0))
    origin=Vector(polar(r,a,0))
    profile=[(-3.1,17.4),(-2.7,17.7),(-2.35,18.2),(-2.05,19.05),(-1.7,19.75),(-1.25,20.30),(-.65,20.64),(0,20.77),(.65,20.64),(1.25,20.30),(1.7,19.75),(2.05,19.05),(2.35,18.2),(2.7,17.7),(3.1,17.4)]
    verts=[]
    for depth in [-.16,1.9]:
        for u,z in profile:verts.append(tuple(origin+tangent*u+normal*depth+Vector((0,0,z))))
    n=len(profile);faces=[tuple(range(n)),tuple(range(2*n-1,n-1,-1))]
    for i in range(n):faces.append((i,(i+1)%n,(i+1)%n+n,i+n))
    mesh('Plaster_Ochre',verts,faces,group)
    pts=[origin+tangent*u-normal*.22+Vector((0,0,z+.07)) for u,z in profile]
    tube('Stone_Trim',pts,[.065]*len(pts),8,group)
    # Oval glazed oculus, dark centre and raised moulding ring.
    c=origin-normal*.235+Vector((0,0,19.27));ring=[]
    for i in range(33):
        t=i*math.tau/32;ring.append(c+tangent*(math.cos(t)*.42)+Vector((0,0,math.sin(t)*.61)))
    tube('Stone_Trim',ring,[.075]*len(ring),7,group)
    mesh('Window_Dark',[tuple(c)]+[tuple(p+normal*.015) for p in ring[:-1]],[(0,(i+1)%32+1,i+1) for i in range(32)],group)
    for j in range(2):
        zz=17.84+j*.30
        arch('Stone_Trim',r-.22,a,zz,2.4,.29,.035,group)

gable(27,math.radians(88))

for ang in [44,129]:
    a=math.radians(ang);cx,cy,_=polar(28,a,0);group='Building_North'
    # Low drum and a hand-shaped copper bell cap above the cornice.
    points=[(cx,cy,z) for z in [16.55,17.1,17.3,17.42,18.1,18.8,19.20,19.40,19.43]]
    radii=[1.62,1.62,1.80,1.75,1.55,1.30,.83,.30,.04]
    tube('Copper_Oxide',points,radii,24,group)
    for j in range(16):
        az=j*math.tau/16
        tube('Roof_Slate',[(cx+rr*math.cos(az),cy+rr*math.sin(az),zz+.012) for (_,_,zz),rr in zip(points[3:],radii[3:])],[.023]*6,5,group)
    for zz,rr in [(17.3,1.80),(18.1,1.55)]:
        ring=[(cx+rr*math.cos(j*math.tau/32),cy+rr*math.sin(j*math.tau/32),zz) for j in range(33)]
        tube('Stone_Dark',ring,[.032]*33,6,group)


def bench(x,y,angle):
    group='Benches';cs=math.cos(angle);sn=math.sin(angle)
    def P(p):u,v,z=p;return (x+u*cs-v*sn,y+u*sn+v*cs,z)
    def B(mat,p,size):box(mat,P(p),size,angle,group)
    for j in range(5):B('Bench_Wood_Pale' if j in [1,4] else 'Bench_Wood',(0,-.28+j*.14,.57),(2.4,.112,.075))
    for j in range(4):B('Bench_Wood_Pale' if j==2 else 'Bench_Wood',(0,.38+j*.032,.79+j*.145),(2.4,.075,.115))
    for side in [-.91,.91]:
        tube('Iron',[P((side,-.32,.07)),P((side,-.25,.55)),P((side,.27,.58)),P((side,.43,1.32))],[.048]*4,8,group)
        tube('Iron',[P((side,.34,.07)),P((side,.27,.55))],[.053,.045],8,group)
        tube('Iron',[P((side,-.23,.58)),P((side,-.29,.81)),P((side,-.16,.88)),P((side,.23,.88)),P((side,.37,.79))],[.037]*5,8,group)
        B('Iron',(side,-.31,.055),(.23,.25,.065));B('Iron',(side,.34,.055),(.23,.25,.065))
    for z,y0 in [(.57,-.3),(.94,.43), (1.23,.48)]:
        for side in [-.98,.98]:sphere('Iron',P((side,y0-.04,z)),.021,group)
    collisions.append({'type':'circle','x':x,'z':-y,'radius':1.15})

bench(-7,4,-1.13);bench(7,3,1.15);bench(-6,-6,-2.2)

def tree(x,y,height,seed,group='Bare_Trees'):
    rng=random.Random(seed);base=Vector((x,y,.03));lean=Vector((rng.uniform(-.4,.4),rng.uniform(-.4,.4),0))
    detailed=group.startswith('Tree_')
    heights=[0,.22,.62,1.15,height*.36,height*.60,height*.8,height] if detailed else [0,.8,height*.36,height*.60,height*.8,height]
    trunk=[base+lean*(t/height)+Vector((0,0,t)) for t in heights]
    if detailed:
        trunk[2]+=Vector((.035,-.025,0));trunk[3]+=Vector((-.025,.019,0));trunk[4]+=Vector((.16,-.13,0));trunk[5]+=Vector((-.08,.12,0))
        trunk_radii=[.37,.305,.245,.203,.15,.10,.051,.008]
    else:
        trunk[2]+=Vector((.16,-.13,0));trunk[3]+=Vector((-.08,.12,0));trunk_radii=[.23,.20,.15,.10,.051,.008]
    tube('Bark',trunk,trunk_radii,10,group)
    for j in range(11):
        az=j*2.399+rng.random()*.5;h=height*(.31+j*.05);origin=base+lean*h/height+Vector((0,0,h));length=height*rng.uniform(.21,.36)*(1-j*.035)
        if detailed:
            # Attach to the true irregular stem centre, so the buried branch end
            # cannot become a disconnected squared stub beside the trunk.
            for ti in range(len(trunk)-1):
                if trunk[ti].z<=base.z+h<=trunk[ti+1].z:
                    t=(base.z+h-trunk[ti].z)/(trunk[ti+1].z-trunk[ti].z)
                    origin=trunk[ti].lerp(trunk[ti+1],t);break
        outward=Vector((math.cos(az),math.sin(az),rng.uniform(.5,.95))).normalized()
        mid=origin+outward*length*.53;tip=origin+outward*length+Vector((0,0,.4))
        if detailed:
            collar=origin-Vector((0,0,.20));shoulder=origin+outward*.20+Vector((0,0,.07))
            tube('Bark',[collar,origin,shoulder,mid,tip],[.105*(1-j*.05),.093*(1-j*.05),.070*(1-j*.04),.039,.009],7,group)
        else:tube('Bark',[origin,mid,tip],[.092*(1-j*.05),.039,.009],7,group)
        for k in range(4):
            start=origin+(tip-origin)*(.35+k*.17);az2=az+(-1 if k%2 else 1)*rng.uniform(.3,1.1)
            end=start+Vector((math.cos(az2),math.sin(az2),rng.uniform(.7,1.7)))*length*.43
            mid2=start.lerp(end,.6)+Vector((0,0,-.10))
            tube('Bark',[start,mid2,end],[.025,.013,.0025],6,group)
            for s in [-1,1]:
                twigstart=start.lerp(end,.65);twig=twigstart+Vector((math.cos(az2+s*.8),math.sin(az2+s*.8),1.4))*length*.20
                tube('Bark',[twigstart,twig],[.009,.0015],5,group)
    # Flared roots bed the tree into the ground rather than floating tubes.
    for j in range(5 if detailed else 6):
        a=j*math.tau/(5 if detailed else 6)
        if detailed:
            a+=.17*math.sin(seed+j*2);length=.65+.18*math.sin(j*1.8+seed)
            foot=base+Vector((math.cos(a)*length,math.sin(a)*length,-.075))
            knee=base+Vector((math.cos(a)*length*.52,math.sin(a)*length*.52,.13))
            shoulder=base+Vector((math.cos(a)*.015,math.sin(a)*.015,.57+.06*math.cos(j)))
            tube('Bark',[shoulder,knee,foot],[.10,.12,.020],10,group)
        else:
            p=base+Vector((math.cos(a)*.55,math.sin(a)*.55,.01));tube('Bark',[base+Vector((0,0,.4)),p],[.095,.015],6,group)
    if group=='Bare_Trees' or group.startswith('Tree_'):collisions.append({'type':'circle','x':x,'z':-y,'radius':.47})

for i,(x,y,h) in enumerate([(-7,8,7.7),(6,9,8.8),(9,-6,7.5),(-8,-6,8.1)]):tree(x,y,h,981+i,group='Tree_'+str(i))
for i in range(18):tree(27+random.random()*22,-30+i*4.3,random.uniform(8,13),i+31,'Park_Trees')

# The eastern park wall has brick piers, capstones and a central wrought iron entrance.
for ylo,yhi in [(-22,3),(9,33)]:
    box('Graffiti_Wall',(23,(ylo+yhi)/2,1.20),(.48,yhi-ylo,2.4),group='Park_Wall')
    box('Stone_Dark',(23,(ylo+yhi)/2,2.44),(.70,yhi-ylo,.18),group='Park_Wall')
    for y in range(ylo,yhi,5):
        box('Brick',(22.94,y,1.32),(.79,.66,2.64),group='Park_Wall')
        box('Stone_Trim',(22.94,y,2.69),(.98,.83,.15),group='Park_Wall')
        for z in range(13):box('Stone_Dark',(22.52,y,z*.19+.12),(.016,.68,.023),group='Park_Wall')
    for z in [.11,.32]:box('Brick',(22.74,(ylo+yhi)/2,z),(.04,yhi-ylo,.14),group='Park_Wall')
for y in [3,9]:
    box('Stone_Dark',(23,y,1.8),(.78,.78,3.6),group='Park_Gate')
    box('Stone_Trim',(23,y,3.64),(.94,.94,.16),group='Park_Gate')
    sphere('Lamp_Glass',(23,y,3.94),.18,'Park_Gate')
for y in [3.25+i*.255 for i in range(23)]:
    tube('Iron',[(23,y,.16),(23,y,2.65)],[.027,.027],6,'Park_Gate')
    # Spear tips are small, distinct silhouettes.
    tube('Iron',[(23,y,2.62),(23,y,2.83)],[.075,.001],6,'Park_Gate')
for z in [.35,1.95,2.50]:box('Iron',(23,6,z),(.08,5.8,.065),group='Park_Gate')
for y in [3.25,6,8.75]:box('Iron',(23,y,1.37),(.10,.09,2.55),group='Park_Gate')
box('Iron',(23,6,3.29),(.11,5.95,.58),group='Park_Gate')

def text_mesh(body,loc,size,mat,rotation,group,extrude=.001):
    curve=bpy.data.curves.new('Handpainted lettering','FONT');curve.body=body;curve.size=size;curve.extrude=extrude;curve.align_x='CENTER';curve.space_character=1.1
    ob=bpy.data.objects.new('lettering',curve);bpy.context.collection.objects.link(ob);ob.location=loc;ob.rotation_euler=rotation
    bpy.context.view_layer.objects.active=ob;ob.select_set(True);bpy.ops.object.convert(target='MESH');ob=bpy.context.object
    verts=[tuple(ob.matrix_world@v.co) for v in ob.data.vertices];faces=[tuple(p.vertices) for p in ob.data.polygons]
    mesh(mat,verts,faces,group);bpy.data.objects.remove(ob,do_unlink=True)

# Text plane local normal becomes west, toward the playable roadway.
text_mesh('FOLKETS PARK',(22.92,6,3.14),.42,'Paint_Cream',(math.pi/2,0,-math.pi/2),'Park_Gate')
text_mesh('FOLKETS PARK',(23.08,6,3.14),.42,'Paint_Cream',(math.pi/2,0,math.pi/2),'Park_Gate')
# The user-supplied visual direction is represented by one authored mural atlas.
material('Graffiti_Mural',(.6,.6,.6),.91)
graffiti_image=bpy.data.images.load(str(ROOT/'public/assets/graffiti-leget-bois.png'));graffiti_image.pack()
graffiti_node=mats['Graffiti_Mural'].node_tree.nodes.new('ShaderNodeTexImage');graffiti_node.image=graffiti_image
mats['Graffiti_Mural'].node_tree.links.new(graffiti_node.outputs['Color'],mats['Graffiti_Mural'].node_tree.nodes.get('Principled BSDF').inputs['Base Color'])
for ya,yb in [(-21.8,-14.6),(-14.5,-7.3),(-7.2,0),(9.5,16.7),(16.8,24),(24.1,31.3)]:
    mesh('Graffiti_Mural',[(22.744,ya,.17),(22.744,yb,.17),(22.744,yb,2.35),(22.744,ya,2.35)],[(0,3,2,1)],'Park_Graffiti',[(0,0),(1,0),(1,1),(0,1)])
    mesh('Graffiti_Mural',[(23.256,ya,.17),(23.256,yb,.17),(23.256,yb,2.35),(23.256,ya,2.35)],[(0,1,2,3)],'Park_Graffiti',[(1,0),(0,0),(0,1),(1,1)])

# Waste bins use real narrow slats and a hollow-looking rim.
for x,y in [(-8.9,1.7),(8.4,-.4)]:
    tube('Iron',[(x,y,.10),(x,y,.91)],[.24,.29],16,'Street_Furniture')
    for i in range(18):
        a=i*math.tau/18;box('Bench_Wood',(x+math.cos(a)*.265,y+math.sin(a)*.265,.54),(.052,.052,.72),a,'Street_Furniture')
    for z in [.20,.83]:
        pts=[(x+.291*math.cos(i*math.tau/24),y+.291*math.sin(i*math.tau/24),z) for i in range(25)]
        tube('Iron',pts,[.025]*25,6,'Street_Furniture')
    collisions.append({'type':'circle','x':x,'z':-y,'radius':.4})

# Low street bollards mark pavement edges and stop vehicles, never invisible barriers.
for a in [20,30,138,145,223,231,302,310]:
    x,y,_=polar(20,math.radians(a),0)
    tube('Iron',[(x,y,.03),(x,y,.76)],[.095,.07],10,'Street_Furniture');sphere('Iron',(x,y,.77),.075,'Street_Furniture')
    collisions.append({'type':'circle','x':x,'z':-y,'radius':.18})

total_tri=0
for (group,mat),(verts,faces,uvs,smooth) in groups.items():
    data=bpy.data.meshes.new(group+'_'+mat);data.from_pydata(verts,[],faces);data.materials.append(mats[mat]);data.update()
    layer=data.uv_layers.new(name='UVMap')
    for loop,uv in zip(layer.data,uvs):loop.uv=uv
    ob=bpy.data.objects.new(group+'_'+mat,data);bpy.context.collection.objects.link(ob)
    total_tri+=sum(len(f)-2 for f in faces)
    # Smooth only rounded organic branches. Architectural corners stay crisp.
    if mat=='Bark':
        for p in data.polygons:p.use_smooth=True

ROOT.joinpath('public/assets').mkdir(parents=True,exist_ok=True)
ROOT.joinpath('.dream-loop').mkdir(exist_ok=True)
bpy.ops.wm.save_as_mainfile(filepath=str(ROOT/'.dream-loop/environment.blend'))
bpy.ops.export_scene.gltf(filepath=str(ROOT/'public/assets/environment.glb'),export_format='GLB',export_yup=True,export_apply=True,export_cameras=False,export_lights=False)
(ROOT/'public/assets/environment-collisions.json').write_text(json.dumps(collisions,indent=2))
print('ENVIRONMENT COMPLETE',len(groups),'meshes',total_tri,'triangles')
