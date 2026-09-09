"""Handmade architectural and park-edge detail layer for Knarkrondellen.
No environment mutation: exports a separate, tightly batched surroundings.glb.
Blender x=east, y=north, z=up; glTF converts to Three.js Y-up.
"""
import bpy,bmesh,math,random,sys
from pathlib import Path
from collections import defaultdict
from mathutils import Vector
ROOT=Path(__file__).resolve().parents[1]
# --no-gate preserves the park benches, low rails and gravel while removing the entrance.
NO_GATE='--no-gate' in sys.argv
OUTPUT_STEM='surroundings-no-gate' if NO_GATE else 'surroundings'
bpy.ops.object.select_all(action='SELECT');bpy.ops.object.delete(use_global=False)
parts=defaultdict(lambda:[[],[],[]]);mats={};rng=random.Random(801)

def material(name,color,rough=.85,metal=0,emission=0):
    m=bpy.data.materials.new('Surroundings_'+name);m.use_nodes=True
    bs=m.node_tree.nodes.get('Principled BSDF');bs.inputs['Base Color'].default_value=(*color,1);bs.inputs['Roughness'].default_value=rough;bs.inputs['Metallic'].default_value=metal
    if emission:bs.inputs['Emission Color'].default_value=(*color,1);bs.inputs['Emission Strength'].default_value=emission
    mats[name]=m
material('Iron',(.047,.063,.056),.58,.67)
material('AgedBrass',(.30,.225,.106),.47,.62)
material('Timber',(.115,.061,.029),.88)
material('TimberLight',(.17,.093,.040),.90)
material('Granite',(.29,.29,.255),.95)
material('Enamel',(.060,.088,.078),.69,.17)
material('Letters',(.69,.54,.30),.85,0,.12)
material('Paper',(.43,.40,.32),1)
material('AwningDark',(.085,.102,.085),1)
material('AwningLight',(.25,.231,.187),1)
material('WarmInterior',(.69,.385,.155),.96,0,.82)
material('WarmGlass',(1,.59,.21),.38,0,1.15)
material('Gravel',(.12,.124,.105),1)

# Embedded grain keeps door panels and bench slats from reading as flat plastic.
import numpy as np
for name in ['Timber','TimberLight']:
    N=256;rr=np.random.default_rng(76);yy,xx=np.mgrid[0:N,0:N].astype(np.float32)
    grain=.82+.09*np.sin(xx*.4+np.sin(yy*.028)*1.4)+.055*np.sin(xx*1.9+yy*.014)+rr.random((N,N))*.06
    base=mats[name].node_tree.nodes.get('Principled BSDF').inputs['Base Color'].default_value[:3]
    pix=np.ones((N,N,4),dtype=np.float32)
    for k in range(3):pix[:,:,k]=grain*base[k]
    img=bpy.data.images.new(name+' handworked grain',width=N,height=N);img.pixels.foreach_set(pix.ravel());img.pack()
    tx=mats[name].node_tree.nodes.new('ShaderNodeTexImage');tx.image=img;mats[name].node_tree.links.new(tx.outputs['Color'],mats[name].node_tree.nodes.get('Principled BSDF').inputs['Base Color'])

# Quiet back-wall light falloff: warm upper room, darker lower display/counter.
N=256;yy,xx=np.mgrid[0:N,0:N].astype(np.float32);xx/=N;yy/=N
light=(.47+.45*yy)*(.81+.19*np.sin(xx*math.pi))+.035*np.sin(xx*8+yy*3)
pix=np.ones((N,N,4),dtype=np.float32)
for k,c in enumerate([.69,.385,.155]):pix[:,:,k]=c*light
img=bpy.data.images.new('Shop interior soft light',width=N,height=N);img.pixels.foreach_set(pix.ravel());img.pack()
nodes=mats['WarmInterior'].node_tree.nodes;tx=nodes.new('ShaderNodeTexImage');tx.image=img;bs=nodes.get('Principled BSDF')
mats['WarmInterior'].node_tree.links.new(tx.outputs['Color'],bs.inputs['Base Color']);mats['WarmInterior'].node_tree.links.new(tx.outputs['Color'],bs.inputs['Emission Color'])

def mesh(mat,verts,faces,uv=None):
    # Classify faces by ground-plane centroid so additions share their building's
    # camera-occlusion fade, while park details remain independently visible.
    by_zone=defaultdict(list)
    for face in faces:
        cx=sum(verts[i][0] for i in face)/len(face);cy=sum(verts[i][1] for i in face)/len(face)
        radius=math.hypot(cx,cy);angle=math.degrees(math.atan2(cy,cx))%360
        if 25<=radius<=34 and 39<=angle<=134:zone='Building_North_Additions'
        elif 25<=radius<=35 and 151<=angle<=218:zone='Building_West_Additions'
        else:zone='Surroundings_Park'
        by_zone[zone].append(face)
    for zone,zone_faces in by_zone.items():
        vs,fs,uvs=parts[(zone,mat)];offset=len(vs);vs.extend(verts)
        for face in zone_faces:
            fs.append(tuple(offset+i for i in face))
            for i in face:
                p=verts[i];uvs.append(uv[i] if uv else(p[0]*.4+p[1]*.15,p[2]*.4+p[1]*.22))

def box(mat,loc,size,angle=0,bevel=0):
    cs=math.cos(angle);sn=math.sin(angle);x,y,z=loc
    if bevel:
        bm=bmesh.new();bmesh.ops.create_cube(bm,size=1)
        for v in bm.verts:v.co.x*=size[0];v.co.y*=size[1];v.co.z*=size[2]
        bmesh.ops.bevel(bm,geom=list(bm.edges),offset=bevel,segments=2,affect='EDGES');bm.verts.ensure_lookup_table();bm.verts.index_update()
        vv=[(x+v.co.x*cs-v.co.y*sn,y+v.co.x*sn+v.co.y*cs,z+v.co.z) for v in bm.verts];ff=[tuple(v.index for v in f.verts) for f in bm.faces]
        mesh(mat,vv,ff);bm.free();return
    a,b,c=[s/2 for s in size]
    vv=[(x+u*cs-v*sn,y+u*sn+v*cs,z+w) for u,v,w in [(-a,-b,-c),(a,-b,-c),(a,b,-c),(-a,b,-c),(-a,-b,c),(a,-b,c),(a,b,c),(-a,b,c)]]
    mesh(mat,vv,[(0,3,2,1),(0,1,5,4),(1,2,6,5),(2,3,7,6),(3,0,4,7),(4,5,6,7)])

def tube(mat,points,radii,n=8):
    vv=[]
    for i,p in enumerate(points):
        p=Vector(p);d=(Vector(points[min(i+1,len(points)-1)])-Vector(points[max(0,i-1)])).normalized();u=d.cross(Vector((0,0,1)))
        if u.length<.01:u=Vector((1,0,0))
        u.normalize();v=d.cross(u).normalized()
        for j in range(n):
            a=j*math.tau/n;vv.append(tuple(p+radii[i]*(math.cos(a)*u+math.sin(a)*v)))
    fs=[tuple(range(n-1,-1,-1))]
    for i in range(len(points)-1):
        for j in range(n):fs.append((i*n+j,i*n+(j+1)%n,(i+1)*n+(j+1)%n,(i+1)*n+j))
    fs.append(tuple((len(points)-1)*n+j for j in range(n)));mesh(mat,vv,fs)

def sphere(mat,p,r,n=16,rings=9):
    vs=[]
    for i in range(rings+1):
        a=math.pi*i/rings
        for j in range(n):
            t=j*math.tau/n;vs.append((p[0]+r*math.sin(a)*math.cos(t),p[1]+r*math.sin(a)*math.sin(t),p[2]+r*math.cos(a)))
    fs=[]
    for i in range(rings):
        for j in range(n):fs.append((i*n+j,i*n+(j+1)%n,(i+1)*n+(j+1)%n,(i+1)*n+j))
    mesh(mat,vs,fs)

def polar(r,a,z):return Vector((r*math.cos(a),r*math.sin(a),z))
def fbox(mat,r,a,z,w,d,h,bevel=0):box(mat,polar(r,a,z),(w,d,h),a+math.pi/2,bevel)
def text(body,loc,size,mat,rotation,width=None):
    curve=bpy.data.curves.new('Crafted lettering','FONT');curve.body=body;curve.align_x='CENTER';curve.size=size;curve.extrude=0;curve.bevel_depth=0;curve.resolution_u=3
    serif=Path('/System/Library/Fonts/Supplemental/Georgia.ttf')
    if serif.exists():curve.font=bpy.data.fonts.load(str(serif))
    ob=bpy.data.objects.new('Lettering',curve);bpy.context.collection.objects.link(ob);ob.location=loc;ob.rotation_euler=rotation;bpy.context.view_layer.update()
    if width:
        # Font-space dimensions, before world rotation.
        natural=max(v[0] for v in ob.bound_box)-min(v[0] for v in ob.bound_box)
        if natural>.0001:ob.scale.x=width/natural
    bpy.ops.object.select_all(action='DESELECT');ob.select_set(True);bpy.context.view_layer.objects.active=ob;bpy.ops.object.convert(target='MESH')
    ob=bpy.context.object;mesh(mat,[tuple(ob.matrix_world@v.co) for v in ob.data.vertices],[tuple(p.vertices) for p in ob.data.polygons]);bpy.data.objects.remove(ob,do_unlink=True)
def ftext(body,r,a,z,size,mat='Letters',width=None,offset=0):
    p=polar(r,a,z)+Vector((-math.sin(a),math.cos(a),0))*offset
    text(body,p,size,mat,(math.pi/2,0,a-math.pi/2),width)

# Door fittings align with the existing arched entrances, without replacing them.
for r,start,end,numbers in [(27,39,134,['20','22','24']),(29,151,218,['19 B','19 A','21'])]:
    a1,a2=map(math.radians,(start,end));bays=round(r*(a2-a1)/2.85);step=(a2-a1)/bays
    for no,i in enumerate(range(2,bays,7)):
        a=a1+(i+.5)*step;tangent=Vector((-math.sin(a),math.cos(a),0));normal=Vector((math.cos(a),math.sin(a),0))
        # Carved lower panels with beveled stiles and a worn threshold edge.
        for side in [-1,1]:
            p=polar(r-.375,a,.29)+tangent*side*.36
            box('TimberLight',p,(.55,.035,.31),a+math.pi/2,.006)
            box('Timber',p-normal*.024,(.44,.023,.20),a+math.pi/2,.005)
            for zz in [.56,2.06]:
                p=polar(r-.376,a,zz)+tangent*side*.36;box('TimberLight',p,(.65,.035,.058),a+math.pi/2,.004)
            p=polar(r-.40,a,1.28)+tangent*side*.14
            tube('AgedBrass',[p+Vector((0,0,-.11)),p-normal*.055+Vector((0,0,-.09)),p-normal*.06+Vector((0,0,.09)),p+Vector((0,0,.11))],[.013]*4,8)
            for zz in [-.12,.12]:sphere('AgedBrass',p+Vector((0,0,zz)),.022,8,4)
        fbox('AgedBrass',r-.38,a,.085,1.41,.07,.027)
        fbox('Granite',r-.56,a,.047,1.87,.37,.095,.012)
        # Four-button engraved brass bell plate beside the stone door jamb.
        pa=a-.044;fbox('AgedBrass',r-.027,pa,1.47,.14,.022,.33,.006)
        for j in range(4):
            fbox('Enamel',r-.045,pa,1.59-j*.079,.108,.012,.041,.003)
            p=polar(r-.057,pa,1.59-j*.079)+tangent*.032;sphere('AgedBrass',p,.013,7,4)
        fbox('Enamel',r-.03,pa,2.24,.37,.022,.23,.012)
        ftext(numbers[no%len(numbers)],r-.050,pa,2.165,.15,'Paper',width=.285)
        # Small mail slot and finger plate on the right door leaf.
        p=polar(r-.41,a,.69)+tangent*.35;box('AgedBrass',p,(.26,.023,.05),a+math.pi/2,.005)
        p=polar(r-.424,a,.69)+tangent*.35;box('Iron',p,(.21,.006,.014),a+math.pi/2)
    # Semi-circular copper gutter and discrete pipe elbows at original downpipes.
    vv=[];ff=[];segments=96
    for j in range(segments+1):
        a=a1+(a2-a1)*j/segments
        for k in range(7):
            t=math.pi*k/6;vv.append(tuple(polar(r-.35+.075*math.cos(t),a,17.24-.075*math.sin(t))))
    for j in range(segments):
        for k in range(6):ff.append((j*7+k,j*7+k+1,(j+1)*7+k+1,(j+1)*7+k))
    mesh('Iron',vv,ff)
    for i in range(0,bays,7):
        a=a1+(i+.5)*step
        tube('Iron',[polar(r-.13,a,.44),polar(r-.13,a,.24),polar(r-.29,a,.12)],[.062,.062,.055],10)
        # Protective iron pipe shoe and wall attachment cover.
        fbox('Iron',r-.15,a,.31,.20,.16,.34,.007)

# Exactly one small local shop. It occupies two ground-floor bays of the west arc.
shop_a=math.radians(190);shop_r=28.70;uvec=Vector((-math.sin(shop_a),math.cos(shop_a),0));nvec=Vector((math.cos(shop_a),math.sin(shop_a),0))
def SP(u,d,z):return polar(shop_r+d,shop_a,z)+uvec*u
def SB(mat,u,d,z,w,depth,h,bevel=0):
    if mat=='WarmInterior':
        vs=[tuple(SP(u+du,d,z+dz)) for du,dz in [(-w/2,-h/2),(w/2,-h/2),(w/2,h/2),(-w/2,h/2)]]
        mesh(mat,vs,[(0,3,2,1)],[(0,0),(1,0),(1,1),(0,1)])
    else:box(mat,SP(u,d,z),(w,depth,h),shop_a+math.pi/2,bevel)
SB('Timber',0,-.18,1.66,5.55,.26,3.15,.018)
# Lit displays are recessed behind chunky, weathered timber joinery.
for side in [-1,1]:
    u=side*1.68;SB('WarmInterior',u,-.345,1.70,1.76,.018,1.92)
    for off in [-.93,.93]:SB('TimberLight',u+off,-.41,1.68,.105,.13,2.14,.006)
    for z in [.60,2.74]:SB('TimberLight',u,-.415,z,1.95,.14,.11,.006)
    SB('Timber',u,-.438,1.86,1.76,.045,.052,.003)
    # Two shelves with a few muted bottles, packets and handwritten labels.
    for shelf,z in enumerate([.92,1.39]):
        SB('Timber',u,-.383,z,1.60,.025,.045)
        for j in range(6):
            px=u-.65+j*.25;h=.15+.07*((j+shelf)%3)
            if j%3==0:
                tube('Enamel',[SP(px,-.376,z+.025),SP(px,-.376,z+h),SP(px,-.376,z+h+.08)],[.045,.042,.018],8)
            else:SB('TimberLight' if j%2 else 'Paper',px,-.380,z+h/2+.02,.14,.027,h,.005)
    # Deep pane borders create visible glazing recesses without a reflection pass.
    for off in [-.875,.875]:SB('Iron',u+off,-.419,1.68,.021,.025,1.96)
SB('TimberLight',0,-.37,1.38,1.28,.08,2.66,.008)
SB('WarmInterior',0,-.426,1.70,1.04,.013,1.72)
for u in [-.52,0,.52]:SB('Timber',u,-.455,1.72,.042,.042,1.76)
for z in [.84,1.96,2.59]:SB('Timber',0,-.459,z,1.08,.04,.05)
SB('Timber',0,-.444,.46,1.07,.032,.56,.006)
SB('TimberLight',0,-.462,.45,.84,.018,.36,.008)
tube('AgedBrass',[SP(.39,-.49,1.14),SP(.39,-.54,1.17),SP(.39,-.54,1.40),SP(.39,-.49,1.43)],[.016]*4,8)
SB('Granite',0,-.64,.065,1.45,.56,.13,.009)
# A modest painted sign, with a thin aged brass inner border.
SB('Enamel',0,-.27,3.29,5.49,.16,.48,.012)
for z in [3.10,3.49]:SB('AgedBrass',0,-.365,z,5.22,.015,.012)
ftext('NATTLIVS',shop_r-.366,shop_a,3.17,.32,'Letters',width=2.86)
ftext('KAFFE  ·  SNACKS  ·  SENT',shop_r-.487,shop_a,.276,.105,'Paper',width=1.02)
# Softly sagging muted striped canvas, with a sewn scalloped valance.
stripes=16;width=5.8
for j in range(stripes):
    u0=-width/2+j*width/stripes;u1=u0+width/stripes;vv=[]
    for k in range(7):
        t=k/6;d=-.28-1.08*t;z=3.03-.29*t-.035*math.sin(math.pi*t)
        vv.extend([tuple(SP(u0,d,z)),tuple(SP(u1,d,z))])
    fs=[(k*2,k*2+1,(k+1)*2+1,(k+1)*2) for k in range(6)]
    mat='AwningDark' if j%2 else 'AwningLight';mesh(mat,vv,fs)
    vv=[]
    for k in range(5):
        u=u0+(u1-u0)*k/4;low=2.62-.035*math.sin(k/4*math.pi);vv.extend([tuple(SP(u,-1.36,2.745)),tuple(SP(u,-1.36,low))])
    mesh(mat,vv,[(k*2,k*2+1,(k+1)*2+1,(k+1)*2) for k in range(4)])
for side in [-1,1]:
    tube('Iron',[SP(side*2.68,-.35,2.68),SP(side*2.68,-.80,2.47),SP(side*2.68,-1.30,2.72)],[.020]*3,7)
    tube('Iron',[SP(side*2.68,-.30,3.05),SP(side*2.68,-1.35,2.74)],[.018,.018],7)
# Small A-board positioned against the storefront rather than in a walking route.
u=3.20;SB('TimberLight',u,-.80,.64,.71,.07,1.11,.006);SB('Enamel',u,-.847,.67,.59,.028,.91,.004)
for side in [-1,1]:
    tube('Timber',[SP(u+side*.30,-.79,.12),SP(u+side*.30,-.69,1.22),SP(u+side*.30,-.19,.12)],[.027,.027,.027],6)
ftext('ÖPPET\nSENT',shop_r-.865,shop_a,.83,.16,'Paper',width=.48,offset=u)
ftext('Kaffe\n& något gott',shop_r-.865,shop_a,.39,.089,'Paper',width=.46,offset=u)

if not NO_GATE:
    # Crafted park entrance header replaces the plain existing plate by covering it.
    segments=32;vv=[]
    for x in [22.875,23.125]:
        for j in range(segments+1):
            t=j/segments;y=2.97+6.06*t;vv.extend([(x,y,3.02),(x,y,3.68+.32*math.sin(math.pi*t))])
    stride=(segments+1)*2;ff=[]
    for j in range(segments):
        ff.extend([(j*2,j*2+1,(j+1)*2+1,(j+1)*2),(stride+j*2,stride+(j+1)*2,stride+(j+1)*2+1,stride+j*2+1),(j*2+1,stride+j*2+1,stride+(j+1)*2+1,(j+1)*2+1)])
    mesh('Enamel',vv,ff)
    for x in [22.860,23.140]:
        pts=[(x,3.04+5.92*j/32,3.66+.32*math.sin(math.pi*j/32)) for j in range(33)]
        tube('AgedBrass',pts,[.025]*len(pts),7)
        tube('AgedBrass',[(x,3.05,3.075),(x,8.95,3.075)],[.018,.018],7)
    text('FOLKETS PARK',(22.845,6,3.29),.44,'Letters',(math.pi/2,0,-math.pi/2),width=4.55)
    text('FOLKETS PARK',(23.155,6,3.29),.44,'Letters',(math.pi/2,0,math.pi/2),width=4.55)
    for y in [3,9]:
        sphere('WarmGlass',(23,y,3.94),.208,20,12)
        tube('AgedBrass',[(23,y,3.69),(23,y,3.78)],[.18,.14],16)
        for j in range(4):
            a=j*math.pi/2;pts=[]
            for k in range(13):
                t=math.pi*k/12;pts.append((23+.214*math.sin(t)*math.cos(a),y+.214*math.sin(t)*math.sin(a),3.94+.214*math.cos(t)))
            tube('Iron',pts,[.007]*13,5)


# Two park benches and low rails continue the scene beyond the playable ring.
def bench(x,y,angle):
    cs=math.cos(angle);sn=math.sin(angle)
    def P(u,v,z):return(x+u*cs-v*sn,y+u*sn+v*cs,z)
    for j in range(5):box('TimberLight' if j==1 else 'Timber',P(0,-.28+j*.14,.55),(2.20,.113,.072),angle,.004)
    for j in range(4):box('TimberLight' if j==2 else 'Timber',P(0,.36+j*.034,.77+j*.145),(2.20,.074,.11),angle,.004)
    for side in [-.84,.84]:
        tube('Iron',[P(side,-.30,.05),P(side,-.23,.53),P(side,.25,.55),P(side,.44,1.27)],[.043]*4,8)
        tube('Iron',[P(side,.36,.05),P(side,.25,.53)],[.047,.042],8)
        tube('Iron',[P(side,-.21,.55),P(side,-.28,.80),P(side,-.12,.87),P(side,.22,.87),P(side,.36,.76)],[.032]*5,7)
        for v in [-.30,.36]:box('Iron',P(side,v,.04),(.20,.20,.06),angle,.006)
bench(28.2,10.7,0);bench(35.7,1.4,math.pi)
for side in [-1,1]:
    y=6+side*1.8
    for x in [25.4,28.0,30.6,33.2,35.8,38.4,41.0]:
        tube('Iron',[(x,y,.03),(x,y,.75)],[.040,.029],8);sphere('Iron',(x,y,.76),.045,9,5)
    for z in [.30,.67]:tube('Iron',[(25.4,y,z),(41.0,y,z)],[.021,.021],7)
# Narrow subdued gravel ribbon gives the rails a readable destination in the park.
mesh('Gravel',[(23.25,4.25,.010),(44.8,4.25,.010),(48.5,5.3,.010),(48.5,8.8,.010),(44.8,7.75,.010),(23.25,7.75,.010)],[(0,1,4,5),(1,2,3,4)])

triangles=0
for (zone,name),(verts,faces,uvs) in parts.items():
    data=bpy.data.meshes.new(zone+'_'+name);data.from_pydata(verts,[],faces);data.materials.append(mats[name]);data.update();layer=data.uv_layers.new(name='UVMap')
    for l,uv in zip(layer.data,uvs):l.uv=uv
    ob=bpy.data.objects.new(zone+'_'+name,data);bpy.context.collection.objects.link(ob);triangles+=sum(len(f)-2 for f in faces)
bpy.ops.wm.save_as_mainfile(filepath=str(ROOT/f'.dream-loop/{OUTPUT_STEM}.blend'))
bpy.ops.export_scene.gltf(filepath=str(ROOT/f'public/assets/{OUTPUT_STEM}.glb'),export_format='GLB',export_yup=True,export_apply=True,export_cameras=False,export_lights=False)
shop_center=SP(0,-.345,0)
print('SURROUNDINGS COMPLETE:',len(parts),'meshes,',triangles,'triangles; shop Three x,z',(round(shop_center.x,3),round(-shop_center.y,3)))
