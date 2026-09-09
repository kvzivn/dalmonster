"""Shallow original cloth deformation of existing character mesh vertices.
Preserves meshes, topology, node transforms, materials, UVs, rig and identity.
"""
import bpy, json, struct, math
import numpy as np
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
def smooth(a,b,x):
 t=max(0,min(1,(x-a)/(b-a)));return t*t*(3-2*t)
def ridge(value,width):
 # One broad asymmetric fabric roll with a shallow, softly compressed underside.
 return math.exp(-(value/width)**2)-.52*math.exp(-((value+width*.95)/(width*.8))**2)
def field(kind,p,side):
 x,y,z=map(float,p)
 if kind=='torso':
  # Waist tension pulls out from zipper/pocket anchors. No deformation of zipper.
  front=smooth(.075,.23,z);center=smooth(.065,.12,abs(x));outer=1-smooth(.40,.50,abs(x));mask=front*center*outer
  heightmask=smooth(.805,.84,y)*(1-smooth(1.23,1.29,y))
  f=0
  for level,slope,amp,width,phase in [(.866,.052,.013,.031,.3),(.947,-.080,.011,.034,1.2),(1.060,.10,.009,.038,2.0)]:
   curve=level+slope*x+.018*math.sin(x*6+phase)
   # Incomplete folds, stronger on alternating sides; avoid regular padded ribs.
   weight=.48+.52*smooth(-.32,.32,x*(1 if phase<1 else -1))
   f+=amp*weight*ridge(y-curve,width)
  return np.array([x*.22,0,1])*f*mask*heightmask
 if kind=='sleeve':
  # Two diagonal compressions across bent elbow, fading before cuff and shoulder.
  cx=side*(.071 if y<-.19 else .05);rad=np.array([x-cx,0,z-.022]);ln=np.linalg.norm(rad)
  if ln<.001:return np.zeros(3)
  radial=rad/ln;angle=math.atan2(rad[2],rad[0]);mask=smooth(-.40,-.35,y)*(1-smooth(-.15,-.10,y))
  azimuth=.48+.52*max(0,math.sin(angle+.55*side))
  center1=-.237+.031*math.sin(angle+.7*side);center2=-.316+.025*math.sin(angle-1.1*side)
  f=(.010*ridge(y-center1,.029)+.0065*ridge(y-center2,.029))*mask*azimuth
  return radial*f
 if kind=='hood':
  # Front opening (z=.145) and crown seam x=0 stay fitted exactly to existing trim.
  back=smooth(-.21,-.14,z)*(1-smooth(.080,.12,z));seamclear=smooth(.016,.045,abs(x));lateral=smooth(.07,.14,abs(x));bottom=1-smooth(.14,.23,y)
  sign=1 if x>0 else -1
  drape1=-.010+.30*(z+.05)+.009*sign
  drape2=-.103-.14*z
  f=(.0075*ridge(y-drape1,.041)+.006*ridge(y-drape2,.035))*back*seamclear*lateral*bottom
  # Directional fold follows the shoulderward hanging cloth, not concentric rings.
  return np.array([sign*.72,-.18,-.16])*f
 return np.zeros(3)
reports={}
for asset in ['player','npc']:
 raw=(ROOT/f'public/assets/{asset}.glb').read_bytes();jn=struct.unpack_from('<I',raw,12)[0];g=json.loads(raw[20:20+jn]);off=20+jn;size=struct.unpack_from('<I',raw,off)[0];buf=bytearray(raw[off+8:off+8+size]);original=bytes(buf)
 def acc(i):
  a=g['accessors'][i];v=g['bufferViews'][a['bufferView']];dtype={5126:np.float32,5125:np.uint32,5123:np.uint16,5121:np.uint8}[a['componentType']];nc={'VEC3':3,'VEC4':4,'VEC2':2,'SCALAR':1}[a['type']];sz=np.dtype(dtype).itemsize;return np.ndarray((a['count'],nc),dtype=dtype,buffer=buf,offset=v.get('byteOffset',0)+a.get('byteOffset',0),strides=(v.get('byteStride',nc*sz),sz)).copy()
 def append(data,copyaccessor):
  while len(buf)%4:buf.append(0)
  b=len(buf);payload=np.asarray(data,dtype=np.float32).tobytes();buf.extend(payload);vi=len(g['bufferViews']);g['bufferViews'].append({'buffer':0,'byteOffset':b,'byteLength':len(payload),'target':34962});a=dict(copyaccessor);a['bufferView']=vi;a.pop('byteOffset',None)
  if 'min' in a:a['min']=np.min(data,axis=0).tolist();a['max']=np.max(data,axis=0).tolist()
  ai=len(g['accessors']);g['accessors'].append(a);return ai
 report=[]
 for node in g['nodes']:
  if 'mesh' not in node:continue
  name=node['name'];kind=None;side=-1 if 'Left' in name else 1
  if asset=='player' and name=='Head_Mesh':kind='hood'
  if asset=='npc' and name=='NPC_Mesh':kind='torso'
  if asset=='npc' and 'Arm.' in name:kind='sleeve'
  if not kind:continue
  assert 'rotation' not in node and 'matrix' not in node
  scale=np.array(node.get('scale',[1,1,1]));trans=np.array(node.get('translation',[0,0,0]))
  for primitive in g['meshes'][node['mesh']]['primitives']:
   material=g['materials'][primitive['material']]['name']
   if material!=('Weathered charcoal canvas' if asset=='player' else 'Washed crimson jacket'):continue
   pi=primitive['attributes']['POSITION'];ni=primitive['attributes']['NORMAL'];pos=acc(pi);normal=acc(ni);parent=pos*scale+trans;delta=np.array([field(kind,p,side) for p in parent]);updated=((parent+delta)-trans)/scale
   idx=acc(primitive['indices']).astype(np.int64).reshape(-1,3);e1=updated[idx[:,1]]-updated[idx[:,0]];e2=updated[idx[:,2]]-updated[idx[:,0]];cross=np.cross(e1,e2);summed=np.zeros_like(updated)
   for j in range(3):np.add.at(summed,idx[:,j],cross)
   # UV splits share normals on the continuous cloth surface, just as in source.
   keys={}
   for i,p in enumerate(parent):keys.setdefault(tuple(np.round(p,5)),[]).append(i)
   for inds in keys.values():summed[inds]=np.sum(summed[inds],axis=0)
   lengths=np.linalg.norm(summed,axis=1);good=lengths>1e-9;summed[good]/=lengths[good,None];summed[~good]=normal[~good]
   # Keep normals in every completely unchanged region exactly as authored.
   touched=np.linalg.norm(delta,axis=1)>1e-6;adj=np.unique(idx[touched[idx].any(axis=1)]);normal[adj]=summed[adj]
   primitive['attributes']['POSITION']=append(updated,g['accessors'][pi]);primitive['attributes']['NORMAL']=append(normal,g['accessors'][ni]);report.append({'node':name,'part':kind,'vertices':len(pos),'changed':int(touched.sum()),'maxMovementMeters':float(np.max(np.linalg.norm(delta,axis=1)))})
 assert bytes(buf[:len(original)])==original
 g['buffers'][0]['byteLength']=len(buf);js=json.dumps(g,separators=(',',':')).encode();js+=b' '*((-len(js))%4);total=12+8+len(js)+8+len(buf);dest=ROOT/f'public/assets/{asset}-cloth.glb';dest.write_bytes(struct.pack('<III',0x46546c67,2,total)+struct.pack('<II',len(js),0x4e4f534a)+js+struct.pack('<II',len(buf),0x004e4942)+buf);reports[asset]=report;print(asset,report,flush=True)
 bpy.ops.object.select_all(action='SELECT');bpy.ops.object.delete(use_global=False);bpy.ops.import_scene.gltf(filepath=str(dest));bpy.ops.wm.save_as_mainfile(filepath=str(ROOT/f'.dream-loop/{asset}-cloth.blend'))
(ROOT/'.dream-loop/character-cloth-report.json').write_text(json.dumps(reports,indent=2))
print('CLOTH DERIVATIVES COMPLETE',flush=True)
