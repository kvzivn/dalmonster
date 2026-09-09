"""CPU BVH hemisphere contact AO, appended to original GLB without re-export drift.
Positions, triangles, UVs, materials, images and scene nodes remain byte-identical.
Run with Blender --background --python scripts/bake_environment_ao.py.
"""
import bpy, json, struct, math, time, ast, random
import numpy as np
from mathutils import Vector
from mathutils.bvhtree import BVHTree
from mathutils.kdtree import KDTree
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];src=ROOT/'public/assets/environment.glb';out=ROOT/'public/assets/environment-ao.glb'
raw=src.read_bytes();jn=struct.unpack_from('<I',raw,12)[0];doc=json.loads(raw[20:20+jn]);bstart=20+jn;bn,bt=struct.unpack_from('<II',raw,bstart);binary=bytearray(raw[bstart+8:bstart+8+bn]);original_binary=bytes(binary)
DT={5126:np.float32,5125:np.uint32,5123:np.uint16,5121:np.uint8};NC={'SCALAR':1,'VEC2':2,'VEC3':3,'VEC4':4}
def accessor(i):
    a=doc['accessors'][i];v=doc['bufferViews'][a['bufferView']];dtype=DT[a['componentType']];nc=NC[a['type']];off=v.get('byteOffset',0)+a.get('byteOffset',0);stride=v.get('byteStride',nc*np.dtype(dtype).itemsize)
    return np.ndarray((a['count'],nc),dtype=dtype,buffer=binary,offset=off,strides=(stride,np.dtype(dtype).itemsize)).copy()
assert all(not any(k in n for k in ['matrix','translation','rotation','scale']) for n in doc['nodes']), 'Original world-space mesh nodes expected'
# Recreate only original band calls in a side-effect-free source namespace.
# Band faces were wound inward; match exact original position/normal corner keys.
band_keys={};band_validation=[]
def capture_band(mat,r1,r2,a1,a2,z1,z2,group,steps=80):
    vv=[]
    for j in range(steps+1):
        a=a1+(a2-a1)*j/steps
        for r,z in [(r1,z1),(r2,z1),(r2,z2),(r1,z2)]:vv.append(Vector((r*math.cos(a),r*math.sin(a),z)))
    ff=[(3,2,1,0)]
    for j in range(steps):
        for k in range(4):ff.append((j*4+k,j*4+(k+1)%4,(j+1)*4+(k+1)%4,(j+1)*4+k))
    ff.append(tuple(steps*4+i for i in range(4)))
    target=band_keys.setdefault(group+'_'+mat,set())
    for face in ff:
        n=(vv[face[1]]-vv[face[0]]).cross(vv[face[2]]-vv[face[0]]).normalized()
        gn=(n.x,n.z,-n.y)
        for i in face:
            q=vv[i];target.add((q.x,q.z,-q.y,*gn))
    mid=(a1+a2)/2
    # Source inner face points radially outward, opposite physical solid boundary.
    j=steps//2;f=ff[1+j*4+3];nn=(vv[f[1]]-vv[f[0]]).cross(vv[f[2]]-vv[f[0]]).normalized();rad=Vector((math.cos(mid),math.sin(mid),0))
    fo=ff[1+j*4+1];no=(vv[fo[1]]-vv[fo[0]]).cross(vv[fo[2]]-vv[fo[0]]).normalized();band_validation.append({'group':group,'rInner':r1,'rOuter':r2,'innerCorrectedRadialDot':round((-nn).dot(rad),5),'outerCorrectedRadialDot':round((-no).dot(rad),5)})
noop=lambda *args,**kwargs:None
ns={'math':math,'random':random.Random(123),'Vector':Vector,'band':capture_band,'polar':lambda r,a,z:(r*math.cos(a),r*math.sin(a),z),'collisions':[]}
for name in ['fbox','box','tube','mesh','window_interior','balcony','arch']:ns[name]=noop
source=ast.parse((ROOT/'scripts/build_environment.py').read_text());building=next(n for n in source.body if isinstance(n,ast.FunctionDef) and n.name=='building');exec(compile(ast.Module(body=[building],type_ignores=[]),'source_band_calls','exec'),ns)
for args in [('Building_North',27,39,134,'Plaster_Ochre'),('Building_West',29,151,218,'Plaster_Sand'),('Building_Distant',49,-7,25,'Plaster_Rust'),('Building_South',53,241,298,'Plaster_Sand')]:ns['building'](*args)
assert all(v['innerCorrectedRadialDot']<-.99 and v['outerCorrectedRadialDot']>.99 for v in band_validation)
normal_corrections={}
def append_accessor(data,component,nctype,count,normalized=False,target=34962):
    while len(binary)%4:binary.append(0)
    off=len(binary);binary.extend(data);view=len(doc['bufferViews']);doc['bufferViews'].append({'buffer':0,'byteOffset':off,'byteLength':len(data),'target':target});ind=len(doc['accessors']);a={'bufferView':view,'componentType':component,'count':count,'type':nctype}
    if normalized:a['normalized']=True
    doc['accessors'].append(a);return ind
for mesh in doc['meshes']:
    keys=band_keys.get(mesh['name'])
    if not keys:continue
    keys=list(keys);kd=KDTree(len(keys))
    for ki,key in enumerate(keys):kd.insert(key[:3],ki)
    kd.balance()
    def is_band(q,n):
        return any(Vector(n).dot(Vector(keys[ki][3:]))>.9999 for _,ki,dist in kd.find_range(Vector(q),.0002))
    for prim in mesh['primitives']:
        pp=accessor(prim['attributes']['POSITION']);nn=accessor(prim['attributes']['NORMAL']);mask=np.array([is_band(q,n) for q,n in zip(pp,nn)])
        idx=accessor(prim['indices']).astype(np.uint32).reshape(-1,3);tri=mask[idx].all(axis=1)
        # Never reverse unrelated geometry: all triangle corners must be band corners.
        used=np.unique(idx[tri]);nn[used]*=-1;idx[tri]=idx[tri][:,[0,2,1]]
        if len(used):
            prim['attributes']['NORMAL']=append_accessor(nn.astype(np.float32).tobytes(),5126,'VEC3',len(nn));prim['indices']=append_accessor(idx.astype(np.uint32).tobytes(),5125,'SCALAR',idx.size,target=34963);normal_corrections[mesh['name']]={'normals':len(used),'triangles':int(tri.sum())}
print('Corrected reversed band faces:',normal_corrections,flush=True)
print('Building architecture BVH...',flush=True);verts=[];faces=[]
for mesh in doc['meshes']:
    if not mesh['name'].startswith(('Building_','Park_Wall','Park_Gate')):continue
    for p in mesh['primitives']:
        mn=doc['materials'][p['material']]['name']
        if mn in ('Facade_Patina','Facade_BaseWear','Graffiti_Mural'):continue
        vs=accessor(p['attributes']['POSITION']);idx=accessor(p['indices']).astype(np.int64).reshape(-1,3);off=len(verts);verts.extend(vs.tolist());faces.extend((idx+off).tolist())
# Ground participates in contact shadow at the plinth, but isn't exported.
off=len(verts);verts.extend([[-100,.005,-100],[100,.005,-100],[100,.005,100],[-100,.005,100]]);faces.extend([(off,off+2,off+1),(off,off+3,off+2)])
bvh=BVHTree.FromPolygons(verts,faces,all_triangles=True,epsilon=0.0);del verts,faces
RAYS=40;RADIUS=1.1;EPS=.008;golden=math.pi*(3-math.sqrt(5));samples=[]
for j in range(RAYS):
    # Cosine-weighted hemisphere: physically plausible ambient diffuse visibility.
    rr=math.sqrt((j+.5)/RAYS);az=j*golden;samples.append((rr*math.cos(az),rr*math.sin(az),math.sqrt(1-rr*rr)))
include={'Plaster_Ochre','Plaster_Sand','Stone_Trim','Stone_Dark','Brick','Window_Frame','Bench_Wood','Iron','Copper_Oxide','Curtains'}
summary={};cache={};started=time.time();count=0
for mesh in doc['meshes']:
    if not mesh['name'].startswith(('Building_North_','Building_West_')):continue
    for prim in mesh['primitives']:
        mn=doc['materials'][prim['material']]['name']
        if mn not in include:continue
        pos=accessor(prim['attributes']['POSITION']);normals=accessor(prim['attributes']['NORMAL']);colors=np.ones((len(pos),4),dtype=np.float32)
        if 'COLOR_0' in prim['attributes']:
            prev=accessor(prim['attributes']['COLOR_0']);prev=prev/255 if prev.dtype==np.uint8 else prev
            colors[:,:prev.shape[1]]=prev
        values=[]
        for i,(p,n) in enumerate(zip(pos,normals)):
            key=tuple(np.round(np.concatenate([p,n]),4))
            val=cache.get(key)
            if val is None:
                normal=Vector(n).normalized()
                # Original band volumes have reversed winding; sample both sides
                # and use the exposed hemisphere without editing original normals.
                hemispheres=[]
                for sign in (1,-1):
                    nn=normal*sign;P=Vector(p)+nn*EPS
                    axis=Vector((0,1,0)) if abs(nn.y)<.92 else Vector((1,0,0));u=nn.cross(axis).normalized();v=nn.cross(u)
                    occluded=0.0
                    for sx,sy,sz in samples:
                        direction=u*sx+v*sy+nn*sz;hit,hn,face,dist=bvh.ray_cast(P,direction,RADIUS)
                        if hit is not None:occluded+=.55+.45*(1-dist/RADIUS)
                    hemispheres.append(occluded)
                val=max(.43,1-.68*min(hemispheres)/RAYS);cache[key]=val
            colors[i,:3]*=val;values.append(val)
        while len(binary)%4:binary.append(0)
        offset=len(binary);data=np.round(np.clip(colors,0,1)*255).astype(np.uint8).tobytes();binary.extend(data);bv=len(doc['bufferViews']);doc['bufferViews'].append({'buffer':0,'byteOffset':offset,'byteLength':len(data),'target':34962});ai=len(doc['accessors']);doc['accessors'].append({'bufferView':bv,'componentType':5121,'normalized':True,'count':len(pos),'type':'VEC4'});prim['attributes']['COLOR_0']=ai
        stats={'vertices':len(pos),'min':round(min(values),3),'median':round(float(np.median(values)),3),'mean':round(float(np.mean(values)),3),'unoccludedFraction':round(float(np.mean(np.asarray(values)>.99)),3)};summary[mesh['name']]=stats;count+=len(pos);print(mesh['name'],stats,'elapsed',round(time.time()-started,1),flush=True)
assert bytes(binary[:len(original_binary)])==original_binary
while len(binary)%4:binary.append(0)
doc['buffers'][0]['byteLength']=len(binary);j=json.dumps(doc,separators=(',',':')).encode();j+=b' '*((-len(j))%4);total=12+8+len(j)+8+len(binary);out.write_bytes(struct.pack('<III',0x46546c67,2,total)+struct.pack('<II',len(j),0x4e4f534a)+j+struct.pack('<II',len(binary),0x004e4942)+binary)
report={'rays':RAYS,'radius':RADIUS,'targetVertices':count,'uniqueSamples':len(cache),'elapsedSeconds':round(time.time()-started,2),'meshes':summary,'originalBufferPreserved':True,'correctedBandMeshes':normal_corrections,'bandNormalValidation':band_validation};(ROOT/'.dream-loop/environment-ao-report.json').write_text(json.dumps(report,indent=2))
print('AO GLB complete',count,'vertices;',round(time.time()-started,1),'seconds; importing derived blend...',flush=True)
bpy.ops.object.select_all(action='SELECT');bpy.ops.object.delete(use_global=False);bpy.ops.import_scene.gltf(filepath=str(out));bpy.ops.wm.save_as_mainfile(filepath=str(ROOT/'.dream-loop/environment-ao.blend'))
print('ENVIRONMENT AO COMPLETE',out,flush=True)
