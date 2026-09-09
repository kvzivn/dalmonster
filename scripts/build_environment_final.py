"""Widen one existing pleated curtain in one third of lit windows, no new geometry."""
import bpy,json,struct,math
import numpy as np
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];raw=(ROOT/'public/assets/environment-finish.glb').read_bytes();jn=struct.unpack_from('<I',raw,12)[0];g=json.loads(raw[20:20+jn]);o=20+jn;bn=struct.unpack_from('<I',raw,o)[0];buf=bytearray(raw[o+8:o+8+bn]);report={}
def acc(i):
 a=g['accessors'][i];v=g['bufferViews'][a['bufferView']];dt={5126:np.float32,5125:np.uint32,5123:np.uint16,5121:np.uint8}[a['componentType']];n={'VEC3':3,'VEC4':4,'VEC2':2,'SCALAR':1}[a['type']];sz=np.dtype(dt).itemsize;return np.ndarray((a['count'],n),dtype=dt,buffer=buf,offset=v.get('byteOffset',0)+a.get('byteOffset',0),strides=(v.get('byteStride',n*sz),sz)).copy()
def append(data,old):
 while len(buf)%4:buf.append(0)
 off=len(buf);b=np.asarray(data,dtype=np.float32).tobytes();buf.extend(b);vi=len(g['bufferViews']);g['bufferViews'].append({'buffer':0,'byteOffset':off,'byteLength':len(b),'target':34962});a=dict(g['accessors'][old]);a['bufferView']=vi;a.pop('byteOffset',None)
 if 'min' in a:a['min']=np.min(data,axis=0).tolist();a['max']=np.max(data,axis=0).tolist()
 ai=len(g['accessors']);g['accessors'].append(a);return ai
heights=np.array([2.15,5.20,8.30,11.40,14.50])
for group,r,start,end in [('North',27,39,134),('West',29,151,218),('Distant',49,-7,25),('South',53,241,298)]:
 prefix='Building_'+group+'_';aa=math.radians(start);endrad=math.radians(end);bays=round(r*(endrad-aa)/2.85);step=(endrad-aa)/bays;w=step*r*.4
 def classify(p):
  x,y,z=map(float,p);ang=math.atan2(-z,x)
  if start>180 and ang<0:ang+=math.tau
  if group=='West' and ang<0:ang+=math.tau
  bay=int(math.floor((ang-aa)/step));floor=int(np.argmin(abs(heights-y)));return bay,floor
 lit=set()
 for m in g['meshes']:
  if not m['name'].startswith(prefix):continue
  for p in m['primitives']:
   if g['materials'][p['material']]['name'] not in ['Window_Lit','Window_Dim']:continue
   for v in acc(p['attributes']['POSITION']):
    bay,floor=classify(v)
    if 0<=bay<bays and abs(float(v[1])-heights[floor])<1.05:lit.add((bay,floor))
 selected=set(sorted(lit)[1::3]);counts=0
 for m in g['meshes']:
  if m['name']!=prefix+'Curtains':continue
  for prim in m['primitives']:
   pi=prim['attributes']['POSITION'];ni=prim['attributes']['NORMAL'];pos=acc(pi);new=pos.copy();norm=acc(ni);changed=np.zeros(len(pos),bool)
   for bay,floor in selected:
    a=aa+(bay+.5)*step;t=np.array([-math.sin(a),0,-math.cos(a)]);rad=np.array([math.cos(a),0,-math.sin(a)]);side=1 if (bay+floor)%2 else -1
    project=pos@rad;tangent=pos@t;height=pos[:,1];mask=(abs(project-(r+.29))<.031)&(abs(height-heights[floor])<.94)&(side*tangent>.15*w)&(side*tangent<.49*w)
    ids=np.where(mask)[0]
    if len(ids)<12:continue
    u=side*tangent[ids];outer=float(max(u));inner=float(min(u));span=outer-inner
    if span<.06*w:continue
    factor=(span+.27*w)/span;unew=outer+(u-outer)*factor;new[ids]+=((unew-u)*side)[:,None]*t;changed[ids]=True;counts+=1
   idx=acc(prim['indices']).astype(np.int64).reshape(-1,3);touched=changed[idx].any(axis=1);adj=np.unique(idx[touched]);facecross=np.cross(new[idx[:,1]]-new[idx[:,0]],new[idx[:,2]]-new[idx[:,0]]);summed=np.zeros_like(new)
   for j in range(3):np.add.at(summed,idx[:,j],facecross)
   length=np.linalg.norm(summed,axis=1);valid=length>1e-10;summed[valid]/=length[valid,None];norm[adj]=summed[adj]
   # Topology/winding remains valid after widening simple ruled pleated sheets.
   before=np.cross(pos[idx[:,1]]-pos[idx[:,0]],pos[idx[:,2]]-pos[idx[:,0]]);dots=np.sum(before*facecross,axis=1);assert np.all(dots[touched]>=-1e-12)
   prim['attributes']['POSITION']=append(new,pi);prim['attributes']['NORMAL']=append(norm,ni)
 report[group]={'litWindows':len(lit),'halfDrawnWindows':counts,'addedPaneCoverage':.27};print(group,report[group],flush=True)
g['buffers'][0]['byteLength']=len(buf);js=json.dumps(g,separators=(',',':')).encode();js+=b' '*((-len(js))%4);ln=12+8+len(js)+8+len(buf);out=ROOT/'public/assets/environment-final.glb';out.write_bytes(struct.pack('<III',0x46546c67,2,ln)+struct.pack('<II',len(js),0x4e4f534a)+js+struct.pack('<II',len(buf),0x004e4942)+buf);(ROOT/'.dream-loop/environment-final-report.json').write_text(json.dumps(report,indent=2))
bpy.ops.object.select_all(action='SELECT');bpy.ops.object.delete(use_global=False);bpy.ops.import_scene.gltf(filepath=str(out));bpy.ops.wm.save_as_mainfile(filepath=str(ROOT/'.dream-loop/environment-final.blend'));print('ENVIRONMENT FINAL READY',flush=True)
