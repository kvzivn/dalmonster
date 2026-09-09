"""Late-autumn perennial beds: curved ribbed leaves, grasses and seed heads.
All geometry authored in Blender, no external assets. Z-up authoring to Y-up glTF.
"""
import bpy, math, random, json
from pathlib import Path
from mathutils import Vector
from collections import defaultdict
ROOT=Path(__file__).resolve().parents[1]
random.seed(859)
bpy.ops.object.select_all(action='SELECT');bpy.ops.object.delete(use_global=False)
parts=defaultdict(lambda:[[],[],[]]);materials={}

def material(name,color,roughness=1):
    m=bpy.data.materials.new(name);m.use_nodes=True
    bs=m.node_tree.nodes.get('Principled BSDF');bs.inputs['Base Color'].default_value=(*color,1);bs.inputs['Roughness'].default_value=roughness
    bs.inputs['Specular IOR Level'].default_value=.055
    attr=m.node_tree.nodes.new('ShaderNodeVertexColor');attr.layer_name='Col';m.node_tree.links.new(attr.outputs['Color'],bs.inputs['Base Color'])
    materials[name]=(m,color)

material('Leaf_Olive',(.068,.092,.039),1)
material('Leaf_Tobacco',(.18,.103,.043),1)
material('Grass_Amber',(.39,.265,.108),1)
material('Grass_Umber',(.19,.158,.069),1)
material('Twigs',(.145,.104,.072),1)
material('Seedheads',(.29,.235,.146),1)
material('Stones',(.27,.28,.25),.95)

def mesh(mat,verts,faces,variation=1):
    vs,fs,cols=parts[mat];n=len(vs);vs.extend(verts)
    base=materials[mat][1]
    for f in faces:
        fs.append(tuple(n+i for i in f))
        for i in f:
            # Slight coherent shade modulation, never random per-triangle noise.
            d=variation*(.95+.05*math.sin(verts[i][0]*4+verts[i][2]*5))
            cols.append(tuple(min(.95,c*d) for c in base)+(1,))

def tube(mat,points,radii,n=5,var=1):
    vs=[]
    for i,p in enumerate(points):
        p=Vector(p);direction=(Vector(points[min(i+1,len(points)-1)])-Vector(points[max(0,i-1)])).normalized()
        u=direction.cross(Vector((0,0,1)))
        if u.length<.01:u=Vector((1,0,0))
        u.normalize();v=direction.cross(u).normalized()
        for j in range(n):
            a=j*math.tau/n;vs.append(tuple(p+(math.cos(a)*u+math.sin(a)*v)*radii[i]))
    fs=[]
    for i in range(len(points)-1):
        for j in range(n):fs.append((i*n+j,i*n+(j+1)%n,(i+1)*n+(j+1)%n,(i+1)*n+j))
    fs.append(tuple((len(points)-1)*n+j for j in range(n)))
    mesh(mat,vs,fs,var)

def ellipsoid(mat,p,radii,var=1,segments=7,rings=4):
    vs=[]
    for i in range(rings+1):
        a=math.pi*i/rings
        for j in range(segments):
            t=j*math.tau/segments
            vs.append((p[0]+radii[0]*math.sin(a)*math.cos(t),p[1]+radii[1]*math.sin(a)*math.sin(t),p[2]+radii[2]*math.cos(a)))
    fs=[]
    for i in range(rings):
        for j in range(segments):fs.append((i*segments+j,i*segments+(j+1)%segments,(i+1)*segments+(j+1)%segments,(i+1)*segments+j))
    mesh(mat,vs,fs,var)

def grass(x,y,scale):
    for j in range(random.randint(25,33)):
        a=random.random()*math.tau;h=random.uniform(.36,.65)*scale
        side=Vector((-math.sin(a),math.cos(a),0));forward=Vector((math.cos(a),math.sin(a),0))
        origin=Vector((x+random.uniform(-.055,.055),y+random.uniform(-.055,.055),.185))
        lean=random.uniform(.20,.44)*scale;w=random.uniform(.010,.019)*scale
        vs=[];segments=5
        for k in range(segments+1):
            t=k/segments;p=origin+forward*(lean*t*t)+Vector((0,0,h*(t-.25*t*t*t)))
            width=w*(1-t*.95)
            p+=side*(math.sin(t*4.5+j)*.028*t)
            # A central ridge gives each grass blade a folded cross section.
            vs.extend([tuple(p-side*width),tuple(p+Vector((0,0,.007*(1-t)))),tuple(p+side*width)])
        fs=[]
        for k in range(segments):
            fs.extend([(k*3,k*3+1,(k+1)*3+1,(k+1)*3),(k*3+1,k*3+2,(k+1)*3+2,(k+1)*3+1)])
        mesh('Grass_Amber' if random.random()<.65 else 'Grass_Umber',vs,fs,random.uniform(.75,1.3))

def hosta(x,y,scale):
    count=random.randint(3,5)
    for j in range(count):
        a=j*math.tau/count+random.uniform(-.35,.35);length=random.uniform(.28,.48)*scale;width=random.uniform(.072,.125)*scale
        forward=Vector((math.cos(a),math.sin(a),0));side=Vector((-math.sin(a),math.cos(a),0));origin=Vector((x,y,.19))
        rise=random.uniform(.10,.23)*scale
        vs=[];nx=6;ny=6
        for k in range(nx+1):
            t=k/nx
            center=origin+forward*(length*t)+Vector((0,0,rise*math.sin(t*math.pi*.75)+.035*t))
            breadth=width*math.sin(math.pi*t)**.75 if k not in [0,nx] else .006
            for q in range(ny+1):
                s=(q/ny)*2-1
                # Cupping, a raised midrib, radial secondary ribs, and a curled edge
                # create a continuous organic surface instead of a flat cutout.
                rib=.004*math.cos(s*math.pi*3)*math.sin(math.pi*t)
                edge=.028*s*s*math.sin(math.pi*t)
                z=rib+edge+.015*math.sin(t*7+s*4)*abs(s)
                v=center+side*(s*breadth)+Vector((0,0,z));vs.append(tuple(v))
        fs=[]
        for k in range(nx):
            for q in range(ny):fs.append((k*(ny+1)+q,k*(ny+1)+q+1,(k+1)*(ny+1)+q+1,(k+1)*(ny+1)+q))
        mat='Leaf_Olive' if random.random()<.76 else 'Leaf_Tobacco'
        mesh(mat,vs,fs,random.uniform(.78,1.40))
        # Thin stem and dark midrib extend from the rosette.
        pts=[origin+forward*(length*t)+Vector((0,0,rise*math.sin(t*math.pi*.75)+.035*t+.018*math.sin(math.pi*t))) for t in [0,.25,.5,.75,1]]
        tube('Grass_Umber',pts,[.009,.007,.005,.003,.001],4,random.uniform(.8,1.1))

def shrub(x,y,scale):
    for j in range(random.randint(7,10)):
        a=j*2.399+random.random();h=random.uniform(.30,.61)*scale;r=random.uniform(.19,.38)*scale
        origin=Vector((x,y,.185));tip=origin+Vector((math.cos(a)*r,math.sin(a)*r,h))
        mid=origin.lerp(tip,.5)+Vector((.025,-.02,0))
        tube('Twigs',[origin,mid,tip],[.019,.011,.003],5,random.uniform(.7,1.3))
        for k in [0,1,2]:
            start=origin.lerp(tip,.4+k*.19);az=a+(-1 if k%2 else 1)*.8
            end=start+Vector((math.cos(az)*r*.55,math.sin(az)*r*.55,h*.24))
            tube('Twigs',[start,end],[.005,.001],4)
            if random.random()<.20:ellipsoid('Seedheads',end,(.023,.023,.034),random.uniform(.8,1.1),4,2)

def seedplant(x,y,scale):
    for j in range(random.randint(3,5)):
        a=random.random()*math.tau;h=random.uniform(.36,.65)*scale;r=random.uniform(.02,.17)
        origin=Vector((x,y,.18));tip=origin+Vector((math.cos(a)*r,math.sin(a)*r,h))
        tube('Twigs',[origin,origin.lerp(tip,.5),tip],[.009,.006,.003],4)
        # Dried perennial umbel, several little capsules on delicate radiating stems.
        for k in range(5):
            ang=k*math.tau/5;end=tip+Vector((math.cos(ang)*.042,math.sin(ang)*.042,random.uniform(-.02,.015)))
            tube('Twigs',[tip-Vector((0,0,.08)),end],[.002,.001],3)
            ellipsoid('Seedheads',end,(.034,.029,.034),random.uniform(.8,1.2),4,2)

layout=json.loads((ROOT/'src/layout.json').read_text())
beds=[(b['x'],b['z'],b['rx'],b['rz'],b['angle']) for b in layout['beds']]
counts=defaultdict(int)
for bi,(cx,cz,rx,rz,angle) in enumerate(beds):
    cs=math.cos(angle);sn=math.sin(angle)
    def world(u,v):return cx+u*cs-v*sn,-(cz+u*sn+v*cs)
    # Uneven patch distribution leaves small pockets of visible soil.
    positions=[];target=round(math.pi*rx*rz*1.66)
    for attempt in range(2000):
        if len(positions)>=target:break
        u=random.uniform(-rx*.87,rx*.87);v=random.uniform(-rz*.87,rz*.87)
        if (u/rx)**2+(v/rz)**2>.77:continue
        if any((u-p[0])**2+(v-p[1])**2<.36**2 for p in positions):continue
        if math.sin(u*2+bi)*math.cos(v*1.2)>.58 and random.random()<.78:continue
        positions.append((u,v))
    for i,(u,v) in enumerate(positions):
        x,y=world(u,v);s=random.uniform(.78,1.08);kind=random.random()
        if kind<.115:hosta(x,y,s);counts['hostas']+=1
        elif kind<.66:grass(x,y,s);counts['grass_tufts']+=1
        elif kind<.865:shrub(x,y,s);counts['shrubs']+=1
        else:seedplant(x,y,s);counts['seedplants']+=1
    # Dead leaves are thin curled three-dimensional forms lying on the bed soil.
    # Broad irregular gaps remain between plant clusters, with quiet litter detail.
    for j in range(round(math.pi*rx*rz*2.1)):
        ang=random.random()*math.tau;r=math.sqrt(random.random())*.93
        u=math.cos(ang)*rx*r;v=math.sin(ang)*rz*r;x,y=world(u,v)
        az=random.random()*math.tau;fw=Vector((math.cos(az),math.sin(az),0));side=Vector((-math.sin(az),math.cos(az),0));origin=Vector((x,y,.187))
        length=random.uniform(.085,.19);width=random.uniform(.025,.061);vs=[]
        for k in range(5):
            t=k/4;center=origin+fw*(length*t)+Vector((0,0,.017*math.sin(t*math.pi)+.012*t*t))
            w=width*math.sin(math.pi*t) if k not in [0,4] else .001
            for q in [-1,0,1]:vs.append(tuple(center+side*(w*q)+Vector((0,0,.014*abs(q)*math.sin(t*math.pi)))) )
        fs=[]
        for k in range(4):
            fs.extend([(k*3,k*3+1,(k+1)*3+1,(k+1)*3),(k*3+1,k*3+2,(k+1)*3+2,(k+1)*3+1)])
        mesh('Leaf_Tobacco',vs,fs,random.uniform(.50,1.45))
    for j in range(12):
        ang=random.random()*math.tau;r=random.random()*.9;x,y=world(math.cos(ang)*rx*r,math.sin(ang)*rz*r)
        a=random.random()*math.tau;length=random.uniform(.18,.45);p=Vector((x,y,.194));q=p+Vector((math.cos(a)*length,math.sin(a)*length,.015))
        tube('Twigs',[p,p.lerp(q,.5)+Vector((0,0,.016)),q],[.011,.007,.002],4,random.uniform(.65,1.3))
        if j%2==0:tube('Twigs',[p.lerp(q,.55),p.lerp(q,.55)+Vector((math.cos(a+.75)*length*.4,math.sin(a+.75)*length*.4,.01))],[.005,.001],4)
    for j in range(7):
        a=random.random()*math.tau;r=random.uniform(.15,.85);u=math.cos(a)*rx*r;v=math.sin(a)*rz*r;x,y=world(u,v)
        ellipsoid('Stones',(x,y,.198),(random.uniform(.06,.14),random.uniform(.05,.11),random.uniform(.025,.07)),random.uniform(.65,1.3),7,3)

triangles=0
for mat,(vs,fs,cols) in parts.items():
    data=bpy.data.meshes.new('Planting_'+mat);data.from_pydata(vs,[],fs);data.materials.append(materials[mat][0]);data.update()
    color=data.color_attributes.new(name='Col',type='FLOAT_COLOR',domain='CORNER')
    for loop,col in zip(color.data,cols):loop.color=col
    for p in data.polygons:p.use_smooth=True
    # Vegetation surfaces are thin real leaves, intentionally double-sided.
    materials[mat][0].use_backface_culling=False
    ob=bpy.data.objects.new('Planting_'+mat,data);bpy.context.collection.objects.link(ob)
    triangles+=sum(len(f)-2 for f in fs)
bpy.ops.wm.save_as_mainfile(filepath=str(ROOT/'.dream-loop/planting.blend'))
bpy.ops.export_scene.gltf(filepath=str(ROOT/'public/assets/planting.glb'),export_format='GLB',export_yup=True,export_apply=True,export_cameras=False,export_lights=False)
print('PLANTING COMPLETE',dict(counts),len(parts),'draw meshes',triangles,'triangles')
