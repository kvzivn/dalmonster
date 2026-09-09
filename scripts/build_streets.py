"""Two receding Malmö street corridors, authored in Blender; no gameplay edits.
Road vectors in Three.js: NW(-.793,-.609), SW(-.643,.766).
"""
import bpy,bmesh,math,random
from pathlib import Path
from collections import defaultdict
from mathutils import Vector
import numpy as np
ROOT=Path(__file__).resolve().parents[1]
bpy.ops.object.select_all(action='SELECT');bpy.ops.object.delete(use_global=False)
parts=defaultdict(lambda:[[],[],[]]);mats={};rng=random.Random(5123);basis=Vector((1,0,0))

def material(name,color,rough=.9,metal=0,emit=0,grain=False):
    m=bpy.data.materials.new(name);m.use_nodes=True;bs=m.node_tree.nodes.get('Principled BSDF');bs.inputs['Base Color'].default_value=(*color,1);bs.inputs['Roughness'].default_value=rough;bs.inputs['Metallic'].default_value=metal
    if emit:bs.inputs['Emission Color'].default_value=(*color,1);bs.inputs['Emission Strength'].default_value=emit
    if grain:
        N=512;gen=np.random.default_rng(sum(map(ord,name)));noise=gen.random((N,N));v=.78+.22*noise
        pix=np.ones((N,N,4),dtype=np.float32)
        for c in range(3):pix[:,:,c]=color[c]*v
        img=bpy.data.images.new(name+' mineral grain',width=N,height=N);img.pixels.foreach_set(pix.ravel());img.pack();tx=m.node_tree.nodes.new('ShaderNodeTexImage');tx.image=img;m.node_tree.links.new(tx.outputs['Color'],bs.inputs['Base Color'])
    mats[name]=m
material('Street_Asphalt',(.073,.081,.080),.79,grain=True)
material('Street_Sidewalk',(.28,.284,.260),.96,grain=True)
material('Street_CurbGranite',(.32,.33,.30),.93,grain=True)
material('Street_CurbDark',(.265,.28,.267),.96,grain=True)
material('Street_FadedPaint',(.38,.395,.36),.98)
material('Street_Iron',(.063,.073,.066),.61,.63)
material('Street_Utility',(.075,.104,.086),.82,.24)
material('Street_ParkingBlue',(.057,.12,.18),.85)
material('Street_BrickFacade',(.235,.139,.10),.97)
material('Street_StoneTrim',(.255,.252,.225),.91,grain=True)
material('Street_Roof',(.075,.105,.12),.71,.18)
material('Street_WindowDark',(.022,.044,.054),.37,.20)
material('Street_WindowWarm',(.60,.325,.125),.77,0,.51)

# Small baked brick atlas for only the distant continuation façades.
N=512;pix=np.ones((N,N,4),dtype=np.float32);pix[:,:,:3]=(.105,.107,.095);gen=np.random.default_rng(718)
for row in range(16):
    hh=32;start=-32 if row%2 else 0
    for col in range(9):
        xa=max(0,start+col*64+2);xb=min(N,start+(col+1)*64-2)
        if xa>=xb:continue
        y0=row*hh+2;y1=(row+1)*hh-2;c=np.array([.235,.139,.10])*gen.uniform(.75,1.25)
        noise=gen.uniform(.88,1.04,(y1-y0,xb-xa,1));pix[y0:y1,xa:xb,:3]=c*noise
img=bpy.data.images.new('Handmade distant brick courses',width=N,height=N);img.pixels.foreach_set(pix.ravel());img.pack();m=mats['Street_BrickFacade'];tx=m.node_tree.nodes.new('ShaderNodeTexImage');tx.image=img;m.node_tree.links.new(tx.outputs['Color'],m.node_tree.nodes.get('Principled BSDF').inputs['Base Color'])

def mesh(mat,verts,faces,group='Street_Corridors',uv=None):
    vs,fs,uvs=parts[(group,mat)];offset=len(vs);vs.extend(verts)
    for f in faces:
        fs.append(tuple(offset+i for i in f))
        for i in f:
            p=verts[i]
            if uv:uvs.append(uv[i])
            elif mat=='Street_BrickFacade':uvs.append(((p[0]*basis.x+p[1]*basis.y)/2.8,p[2]/1.6))
            else:uvs.append((p[0]/.85,p[1]/.85 if abs(p[2])<.3 else p[2]/.85))

def box(mat,loc,size,angle=0,bevel=0,group='Street_Corridors'):
    cs=math.cos(angle);sn=math.sin(angle);x,y,z=loc
    if bevel:
        bm=bmesh.new();bmesh.ops.create_cube(bm,size=1)
        for v in bm.verts:v.co.x*=size[0];v.co.y*=size[1];v.co.z*=size[2]
        bmesh.ops.bevel(bm,geom=list(bm.edges),offset=bevel,segments=1,affect='EDGES');bm.verts.ensure_lookup_table();bm.verts.index_update()
        vv=[(x+v.co.x*cs-v.co.y*sn,y+v.co.x*sn+v.co.y*cs,z+v.co.z) for v in bm.verts];ff=[tuple(v.index for v in f.verts) for f in bm.faces];mesh(mat,vv,ff,group);bm.free();return
    a,b,c=[s*.5 for s in size];vv=[(x+u*cs-v*sn,y+u*sn+v*cs,z+w) for u,v,w in [(-a,-b,-c),(a,-b,-c),(a,b,-c),(-a,b,-c),(-a,-b,c),(a,-b,c),(a,b,c),(-a,b,c)]]
    mesh(mat,vv,[(0,3,2,1),(0,1,5,4),(1,2,6,5),(2,3,7,6),(3,0,4,7),(4,5,6,7)],group)

def tube(mat,pts,radii,n=8,group='Street_Corridors'):
    vs=[]
    for i,p in enumerate(pts):
        p=Vector(p);d=(Vector(pts[min(i+1,len(pts)-1)])-Vector(pts[max(0,i-1)])).normalized();u=d.cross(Vector((0,0,1)))
        if u.length<.01:u=Vector((1,0,0))
        u.normalize();v=d.cross(u).normalized()
        for j in range(n):a=j*math.tau/n;vs.append(tuple(p+radii[i]*(math.cos(a)*u+math.sin(a)*v)))
    fs=[tuple(range(n-1,-1,-1))]
    for i in range(len(pts)-1):
        for j in range(n):fs.append((i*n+j,i*n+(j+1)%n,(i+1)*n+(j+1)%n,(i+1)*n+j))
    fs.append(tuple((len(pts)-1)*n+j for j in range(n)));mesh(mat,vs,fs,group)

building_footprints=[(27,35,39,134),(29,37,151,218),(53,61,241,298)]
def blocked(x,y,margin=.09):
    r=math.hypot(x,y);a=math.degrees(math.atan2(y,x))%360
    return any(lo-margin<r<hi+margin and start-.1<a<end+.1 for lo,hi,start,end in building_footprints)

for street,angle in [('NW',142.5),('SW',230)]:
    a=math.radians(angle);d=Vector((math.cos(a),math.sin(a),0));p=Vector((-math.sin(a),math.cos(a),0))
    def P(t,l,z):return d*t+p*l+Vector((0,0,z))
    # Six-metre segments keep a sensible physical UV scale and a clean shared road.
    for t in range(22,65):
        vs=[tuple(P(t,-4,.008)),tuple(P(t+1,-4,.008)),tuple(P(t+1,4,.008)),tuple(P(t,4,.008))]
        mesh('Street_Asphalt',vs,[(0,1,2,3)])
    # Narrow jointed concrete pavement, clipped against real building footprint
    # returns where the NW entrance is temporarily tighter than a full sidewalk.
    for side in [-1,1]:
        for j in range(57):
            t0=22+j*.755;t1=min(65,t0+.743)
            if t0>=65:continue
            for k in range(6):
                lo=4.13+k*.48;hi=min(7.0,lo+.468)
                corners=[P(t0,side*lo,.163),P(t1,side*lo,.163),P(t1,side*hi,.163),P(t0,side*hi,.163)]
                # Subdivide only boundary cells; full slabs are two triangles.
                if any(blocked(v.x,v.y) for v in corners):
                    for q in range(3):
                        for h in range(3):
                            ta=t0+(t1-t0)*q/3;tb=t0+(t1-t0)*(q+1)/3;la=lo+(hi-lo)*h/3;lb=lo+(hi-lo)*(h+1)/3
                            small=[P(ta,side*la,.163),P(tb,side*la,.163),P(tb,side*lb,.163),P(ta,side*lb,.163)]
                            if any(blocked(v.x,v.y) for v in small):continue
                            mesh('Street_Sidewalk',[tuple(v) for v in small],[(0,1,2,3)] if side==1 else [(3,2,1,0)])
                else:mesh('Street_Sidewalk',[tuple(v) for v in corners],[(0,1,2,3)] if side==1 else [(3,2,1,0)])
        # 40–70cm individual granite curb stones, rounded worn edges and narrow gaps.
        t=22
        while t<65:
            length=min(rng.uniform(.43,.69),65-t);mid=t+length/2;pos=P(mid,side*4.025,.087)
            corners=[P(mid+dt,side*4.025+dl,0) for dt in [-length/2,length/2] for dl in [-.105,.105]]
            if not any(blocked(c.x,c.y,0) for c in corners):box('Street_CurbDark' if rng.random()<.3 else 'Street_CurbGranite',pos,(max(.05,length-.013),.20,.176),a,.009)
            t+=length
        # Restrained worn parking bays only farther down the street.
        for t in [39,45,51,57,63]:
            for lateral in [side*2.08,side*3.43]:
                box('Street_FadedPaint',P(t,lateral,.014),(.055,.61,.004),a)
        for t in [42,48,54,60]:
            box('Street_FadedPaint',P(t,side*1.80,.014),(1.4,.035,.004),a)
        # Real iron storm drain grilles sit beside the curb, not on the sidewalk.
        for t in [27.4,41.7,56.2]:
            pos=P(t,side*3.74,.014);box('Street_Iron',pos,(.58,.32,.018),a,.01)
            for j in range(7):
                box('Street_Asphalt',P(t-.22+j*.073,side*3.74,.025),(.036,.225,.005),a)
    # Two cast covers per corridor, with raised concentric rims and ribs.
    for t,l in [(34.2,-.7),(54.8,.9)]:
        center=P(t,l,.016);tube('Street_Iron',[center-Vector((0,0,.008)),center+Vector((0,0,.003))],[.295,.295],20)
        ring=[center+Vector((math.cos(j*math.tau/24)*.267,math.sin(j*math.tau/24)*.267,.011)) for j in range(25)];tube('Street_Iron',ring,[.009]*25,5)
        for j in range(5):box('Street_CurbDark',center+Vector((0,0,.009))+p*((j-2)*.087),(.38,.013,.004),a)
    # Utility cabinet and a single discreet Swedish parking sign on each pavement.
    pos=P(43.1,6.28,.57);box('Street_Utility',pos,(.66,.34,1.05),a,.018);box('Street_Iron',P(43.1,6.10,.57),(.54,.015,.87),a,.008)
    box('Street_FadedPaint',P(43.1,6.085,.75),(.15,.009,.10),a)
    sign=P(46.8,6.15,0);tube('Street_Iron',[sign+Vector((0,0,.03)),sign+Vector((0,0,2.55))],[.031,.026],8)
    box('Street_ParkingBlue',sign+Vector((0,0,2.29)),(.43,.055,.52),a+math.pi/2,.014)
    # The simple P is physically painted with rectangular strokes and a curved bowl.
    base=sign+Vector((0,0,2.27))-d*.035
    box('Street_FadedPaint',base-p*.105,(.045,.012,.34),a+math.pi/2)
    box('Street_FadedPaint',base+Vector((0,0,.145)),(.21,.012,.045),a+math.pi/2)
    box('Street_FadedPaint',base+Vector((0,0,.0)),(.21,.012,.045),a+math.pi/2)
    box('Street_FadedPaint',base+p*.10+Vector((0,0,.075)),(.045,.012,.17),a+math.pi/2)

    # One distant residential continuation on the free side of each corridor.
    # It starts beyond the existing block depth and never closes the street axis.
    group='Building_North_StreetContinuation' if street=='NW' else 'Building_West_StreetContinuation'
    basis=d;t0=43.0;t1=67.0;front=-9.7;depth=6.5;height=10.5
    def B(mat,t,l,z,w,dep,h):box(mat,P(t,l,z),(w,dep,h),a,group=group)
    mesh('Street_Sidewalk',[tuple(P(t0,-9.7,.163)),tuple(P(t1,-9.7,.163)),tuple(P(t1,-7,.163)),tuple(P(t0,-7,.163))],[(0,1,2,3)])
    for zl,zh in [(0,.76),(2.62,3.21),(5.08,5.67),(7.54,8.13),(10.0,10.5)]:B('Street_BrickFacade',(t0+t1)/2,front-depth/2,(zl+zh)/2,t1-t0,depth,zh-zl)
    B('Street_BrickFacade',(t0+t1)/2,front-depth+.12,5.25,t1-t0,.24,10.5)
    for t in [t0,t1]:B('Street_BrickFacade',t,front-depth/2,5.25,.24,depth,10.5)
    for j in range(10):
        t=t0+j*2.4
        if j<10:B('Street_BrickFacade',t+.34,front-.17,5.35,.68,.35,9.25)
        tc=t+1.50
        for floor,z in enumerate([1.69,4.15,6.61,9.07]):
            lit=(j+floor*3+(0 if street=='NW' else 1))%5 in [0,1]
            B('Street_Iron',tc,front-.21,z,1.35,.06,1.89)
            B('Street_WindowWarm' if lit else 'Street_WindowDark',tc,front-.168,z,1.20,.025,1.76)
            for off in [-.62,.62]:B('Street_Iron',tc+off,front+.012,z,.05,.055,1.85)
            B('Street_Iron',tc,front+.015,z,.044,.055,1.85);B('Street_Iron',tc,front+.015,z+.40,1.25,.055,.044)
            B('Street_StoneTrim',tc,front+.11,z-.98,1.55,.28,.12)
            if lit and j%2==0:B('Street_Iron',tc-.42,front-.11,z,.22,.025,1.72)
    B('Street_StoneTrim',(t0+t1)/2,front+.09,.30,t1-t0,.20,.58)
    B('Street_StoneTrim',(t0+t1)/2,front+.10,10.48,t1-t0,.29,.16)
    B('Street_Roof',(t0+t1)/2,front-depth/2,10.62,t1-t0+.4,depth+.4,.17)
    for t in [46,56,64]:
        B('Street_BrickFacade',t,front-3.5,11.2,.80,.85,1.15);B('Street_StoneTrim',t,front-3.5,11.8,.94,.97,.13)

triangles=0
for (group,mat),(verts,faces,uvs) in parts.items():
    data=bpy.data.meshes.new(group+'_'+mat);data.from_pydata(verts,[],faces);data.materials.append(mats[mat]);data.update();uv=data.uv_layers.new(name='UVMap')
    for l,v in zip(uv.data,uvs):l.uv=v
    ob=bpy.data.objects.new(group+'_'+mat,data);bpy.context.collection.objects.link(ob);triangles+=sum(len(f)-2 for f in faces)
bpy.ops.wm.save_as_mainfile(filepath=str(ROOT/'.dream-loop/streets.blend'))
bpy.ops.export_scene.gltf(filepath=str(ROOT/'public/assets/streets.glb'),export_format='GLB',export_yup=True,export_apply=True,export_cameras=False,export_lights=False)
print('STREETS COMPLETE',len(parts),'meshes',triangles,'triangles. Road r22..65, asphalt width8m, sidewalks nominal3m with footprint clipping.')
