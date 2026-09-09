"""Final original local facade finish over corrected geometry + baked vertex AO.
No geometry, winding, normals, layout or runtime lighting changes.
"""
import bpy,json,struct,zlib,math
import numpy as np
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];source=ROOT/'public/assets/environment-ao.glb';raw=source.read_bytes();jn=struct.unpack_from('<I',raw,12)[0];g=json.loads(raw[20:20+jn]);at=20+jn;bl=struct.unpack_from('<I',raw,at)[0];buf=bytearray(raw[at+8:at+8+bl]);original=bytes(buf);report={}
N=512;yy,xx=np.mgrid[0:N,0:N].astype(np.float32);x=(xx+.5)/N;y=(yy+.5)/N;gen=np.random.default_rng(92987)
def png(a):
 a=np.uint8(np.clip(a,0,1)*255+.5);h,w,_=a.shape
 def chunk(t,data):return struct.pack('>I',len(data))+t+data+struct.pack('>I',zlib.crc32(t+data)&0xffffffff)
 return b'\x89PNG\r\n\x1a\n'+chunk(b'IHDR',struct.pack('>IIBBBBB',w,h,8,6,0,0,0))+chunk(b'IDAT',zlib.compress(b''.join(b'\x00'+row.tobytes() for row in a),8))+chunk(b'IEND',b'')
def texture(name,rgba):
 payload=png(rgba);(ROOT/f'public/assets/{name}.png').write_bytes(payload)
 while len(buf)%4:buf.append(0)
 off=len(buf);buf.extend(payload);bv=len(g['bufferViews']);g['bufferViews'].append({'buffer':0,'byteOffset':off,'byteLength':len(payload)});im=len(g['images']);g['images'].append({'name':name,'mimeType':'image/png','bufferView':bv});tex=len(g['textures']);g['textures'].append({'source':im,'sampler':0});return tex
# Non-uniform rain wash attached directly beneath existing sill projection.
noise=gen.uniform(.78,1.13,(N,N));alpha=.27*np.exp(-y/0.31)
for j in range(17):
 center=gen.uniform(.05,.95);width=gen.uniform(.008,.040);length=gen.uniform(.30,.98);bend=.011*np.sin(y*7+j)
 alpha+=np.exp(-((x-center-bend)/width)**2)*np.clip((length-y)/.18,0,1)*gen.uniform(.21,.53)
alpha*=noise*np.clip(x/.065,0,1)*np.clip((1-x)/.065,0,1);rgba=np.ones((N,N,4));rgba[:,:,0]=.255*noise;rgba[:,:,1]=.235*noise;rgba[:,:,2]=.19*noise;rgba[:,:,3]=np.clip(alpha,0,.76)
patina=texture('facade-finish-sill-runoff',rgba)
# Rising damp with a feathered irregular top edge and a visibly dirtier first 40cm.
noise=gen.uniform(.78,1.14,(N,N));top=.14+.085*np.sin(x*19)+.05*np.sin(x*43+.8);alpha=np.clip((y-top)/.38,0,1)*(.40+.12*np.sin(x*13+1)**2)*noise
rgba=np.ones((N,N,4));rgba[:,:,0]=.225*noise;rgba[:,:,1]=.229*noise;rgba[:,:,2]=.181*noise;rgba[:,:,3]=np.clip(alpha,0,.64);base=texture('facade-finish-base-damp',rgba)
# Fine vertical linen thread; narrow pleated source curtain meshes retain silhouette.
weave=.82+.10*np.sin(xx*math.tau/5)+.04*np.sin(yy*math.tau/3)+gen.uniform(-.04,.04,(N,N));rgba=np.ones((N,N,4));rgba[:,:,:3]=weave[:,:,None];curtain=texture('facade-finish-curtain-weave',rgba)
for m in g['materials']:
 name=m['name'];pbr=m.setdefault('pbrMetallicRoughness',{})
 if name=='Facade_Patina':pbr['baseColorTexture']={'index':patina};pbr['baseColorFactor']=[1,1,1,1];pbr['roughnessFactor']=1
 if name=='Facade_BaseWear':pbr['baseColorTexture']={'index':base};pbr['baseColorFactor']=[1,1,1,1];pbr['roughnessFactor']=1
 if name=='Curtains':pbr['baseColorFactor']=[.135,.094,.057,1];pbr['baseColorTexture']={'index':curtain};pbr['roughnessFactor']=1;m.setdefault('extensions',{}).setdefault('KHR_materials_specular',{})['specularFactor']=.06
 if name=='Stone_Trim':pbr['roughnessFactor']=.94
 if name=='Stone_Dark':pbr['roughnessFactor']=.98

def acc(i):
 a=g['accessors'][i];v=g['bufferViews'][a['bufferView']];dt={5126:np.float32,5125:np.uint32,5123:np.uint16,5121:np.uint8}[a['componentType']];n={'VEC3':3,'VEC4':4,'VEC2':2,'SCALAR':1}[a['type']];sz=np.dtype(dt).itemsize;return np.ndarray((a['count'],n),dtype=dt,buffer=buf,offset=v.get('byteOffset',0)+a.get('byteOffset',0),strides=(v.get('byteStride',n*sz),sz)).copy()
def color_accessor(data):
 while len(buf)%4:buf.append(0)
 off=len(buf);bb=np.uint8(np.clip(data,0,1)*255+.5).tobytes();buf.extend(bb);bv=len(g['bufferViews']);g['bufferViews'].append({'buffer':0,'byteOffset':off,'byteLength':len(bb),'target':34962});ai=len(g['accessors']);g['accessors'].append({'bufferView':bv,'componentType':5121,'normalized':True,'count':len(data),'type':'VEC4'});return ai
for mesh in g['meshes']:
 if not mesh['name'].startswith(('Building_North_','Building_West_')):continue
 group='North' if mesh['name'].startswith('Building_North') else 'West';r,start,end=(27,39,134) if group=='North' else (29,151,218);aa=math.radians(start);step=math.radians(end-start)/round(r*math.radians(end-start)/2.85)
 for p in mesh['primitives']:
  mat=g['materials'][p['material']]['name']
  if mat not in ['Stone_Trim','Stone_Dark','Curtains','Interior_Amber','Interior_Honey','Window_Lit','Window_Dim']:continue
  pos=acc(p['attributes']['POSITION']);colors=np.ones((len(pos),4),dtype=np.float32)
  if 'COLOR_0' in p['attributes']:
   old=acc(p['attributes']['COLOR_0']);colors[:,:old.shape[1]]=old/255 if old.dtype==np.uint8 else old
  for i,(px,py,pz) in enumerate(pos):
   angle=math.atan2(-pz,px)%math.tau;bay=math.floor((angle-aa)/step);floor=max(0,round((float(py)-2.15)/3.1));seed=(bay*137+floor*7919+(0 if group=='North' else 6121));rng=np.random.default_rng(seed%2**32)
   if mat in ['Window_Lit','Window_Dim','Interior_Amber','Interior_Honey']:
    # Keep large luminous areas warm, but individual occupied rooms differ.
    palettes=[(.98,.88,.77),(.78,.85,.96),(.85,.77,.66),(1,.97,.88),(.69,.72,.73)]
    tint=np.array(palettes[seed%len(palettes)]);strength=[.76,1,.91,.84][(seed//7)%4];localheight=(float(py)-(2.15+floor*3.1))/.95
    # Dim upper room ceiling compared with the lower wall/window light.
    gradient=.96-.10*max(0,localheight);colors[i,:3]*=tint*strength*gradient
   elif mat=='Curtains':
    # Irregularly selected tobacco/slate linen preserves existing baked contact AO.
    tint=np.array([(.83,.79,.72),(.66,.78,.91),(.99,.88,.67)][seed%3]);colors[i,:3]*=tint*(.83+.17*(seed%5)/4)
   else:
    # Stone pieces acquire modest mineral color variation with darker undersides.
    tint=np.array([(.98,.98,.94),(.86,.90,.94),(.93,.88,.79)][seed%3]);variation=.94+.06*(seed%7)/6
    colors[i,:3]*=tint*variation
  p['attributes']['COLOR_0']=color_accessor(colors);report[mesh['name']]={'vertices':len(pos),'material':mat}
assert bytes(buf[:len(original)])==original
while len(buf)%4:buf.append(0)
g['buffers'][0]['byteLength']=len(buf);js=json.dumps(g,separators=(',',':')).encode();js+=b' '*((-len(js))%4);length=12+8+len(js)+8+len(buf);out=ROOT/'public/assets/environment-finish.glb';out.write_bytes(struct.pack('<III',0x46546c67,2,length)+struct.pack('<II',len(js),0x4e4f534a)+js+struct.pack('<II',len(buf),0x004e4942)+buf)
(ROOT/'.dream-loop/environment-finish-report.json').write_text(json.dumps(report,indent=2));print('ENVIRONMENT FINISH COMPLETE',len(report),'material batches modified, bytes',len(out.read_bytes()),flush=True)
bpy.ops.object.select_all(action='SELECT');bpy.ops.object.delete(use_global=False);bpy.ops.import_scene.gltf(filepath=str(out));bpy.ops.wm.save_as_mainfile(filepath=str(ROOT/'.dream-loop/environment-finish.blend'))
