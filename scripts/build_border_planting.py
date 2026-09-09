"""Original low autumn planting for the two annular island-edge beds.
Reads src/layout.json. Exports only vegetation, never soil/rail/collision geometry.
No GPU preview is started: exports and geometric containment checks are CPU-only.
"""
import bpy,math,random,json,bmesh
from pathlib import Path
from mathutils import Vector
from collections import defaultdict
ROOT=Path(__file__).resolve().parents[1]
rng=random.Random(6014)
bpy.ops.object.select_all(action='SELECT');bpy.ops.object.delete(use_global=False)
parts=defaultdict(lambda:[[],[],[]]);mats={};counts=defaultdict(int)

def material(name,c):
 m=bpy.data.materials.new(name);m.use_nodes=True;m.diffuse_color=(*c,1);m.use_backface_culling=False
 p=m.node_tree.nodes.get('Principled BSDF');p.inputs['Base Color'].default_value=(*c,1);p.inputs['Roughness'].default_value=1;p.inputs['Specular IOR Level'].default_value=.055
 a=m.node_tree.nodes.new('ShaderNodeVertexColor');a.layer_name='Col';m.node_tree.links.new(a.outputs['Color'],p.inputs['Base Color']);mats[name]=(m,c)
material('Border muted olive leaf',(.043,.065,.027))
material('Border tobacco dry leaf',(.125,.078,.036))
material('Border dry umber grass',(.130,.109,.054))
material('Border deep olive grass',(.068,.078,.034))
material('Border bare wet twigs',(.082,.058,.035))
material('Border dark seed capsules',(.120,.093,.052))

def mesh(name,vs,fs,variation=1):
 points,faces,colors=parts[name];offset=len(points);points.extend(vs);base=mats[name][1]
 for f in fs:
  faces.append(tuple(offset+i for i in f))
  for i in f:
   v=vs[i];d=variation*(.97+.03*math.sin(v[0]*4.3+v[2]*5.1));colors.append((*[min(.9,c*d) for c in base],1))

def tube(name,ps,rs,segments=4,var=1):
 vs=[];fs=[]
 for i,p in enumerate(ps):
  p=Vector(p);t=(Vector(ps[min(i+1,len(ps)-1)])-Vector(ps[max(i-1,0)])).normalized();u=t.cross(Vector((0,0,1)))
  if u.length<.001:u=Vector((1,0,0))
  u.normalize();w=t.cross(u).normalized()
  for j in range(segments):a=j*math.tau/segments;vs.append(tuple(p+rs[i]*(math.cos(a)*u+math.sin(a)*w)))
 for i in range(len(ps)-1):
  for j in range(segments):a=i*segments+j;b=i*segments+(j+1)%segments;fs.append((a,b,b+segments,a+segments))
 fs.append(tuple((len(ps)-1)*segments+j for j in range(segments)));mesh(name,vs,fs,var)

def capsule(p,r,var):
 vs=[];fs=[];N=5
 for zz,rr in [(-r*.65,r*.25),(0,r),(r*.9,r*.18)]:
  for j in range(N):a=j*math.tau/N;vs.append((p[0]+rr*math.cos(a),p[1]+rr*math.sin(a),p[2]+zz))
 for i in range(2):
  for j in range(N):a=i*N+j;b=i*N+(j+1)%N;fs.append((a,b,b+N,a+N))
 mesh('Border dark seed capsules',vs,fs,var)

def grass(x,y,scale,base):
 counts['grass_tufts']+=1
 for j in range(rng.randint(21,26)):
  a=rng.random()*math.tau;fw=Vector((math.cos(a),math.sin(a),0));side=Vector((-math.sin(a),math.cos(a),0))
  origin=Vector((x+rng.uniform(-.04,.04),y+rng.uniform(-.04,.04),base))
  h=rng.uniform(.25,.49)*scale;lean=rng.uniform(.16,.31)*scale;width=rng.uniform(.008,.015)*scale;vs=[];fs=[];N=4
  for k in range(N+1):
   t=k/N;center=origin+fw*(lean*t*t)+Vector((0,0,h*(t-.30*t*t*t)));center+=side*(math.sin(t*3.5+j)*.023*t)
   w=width*(1-t*.97);vs.extend([tuple(center-side*w),tuple(center+Vector((0,0,.005*(1-t)))),tuple(center+side*w)])
  for k in range(N):fs.extend([(k*3,k*3+1,k*3+4,k*3+3),(k*3+1,k*3+2,k*3+5,k*3+4)])
  mesh('Border dry umber grass' if rng.random()<.58 else 'Border deep olive grass',vs,fs,rng.uniform(.73,1.16))

def shrub(x,y,scale,base):
 counts['dry_twig_shrubs']+=1
 for j in range(rng.randint(6,8)):
  a=j*2.399+rng.random()*.5;h=rng.uniform(.24,.47)*scale;r=rng.uniform(.12,.27)*scale;origin=Vector((x,y,base));tip=origin+Vector((r*math.cos(a),r*math.sin(a),h))
  mid=origin.lerp(tip,.56)+Vector((.013,-.017,0));tube('Border bare wet twigs',[origin,mid,tip],[.013,.007,.0015],4,rng.uniform(.72,1.12))
  for k in range(3):
   start=origin.lerp(tip,.34+k*.19);az=a+(-1 if k%2 else 1)*.85;end=start+Vector((math.cos(az)*r*.5,math.sin(az)*r*.5,h*.22))
   tube('Border bare wet twigs',[start,end],[.0035,.0008],3)
   if rng.random()<.10:capsule(end,.015,rng.uniform(.74,1.05))

def hosta(x,y,scale,base):
 counts['hosta_clusters']+=1
 for j in range(rng.randint(4,5)):
  a=j*2.399+rng.uniform(-.3,.3);fw=Vector((math.cos(a),math.sin(a),0));side=Vector((-math.sin(a),math.cos(a),0));origin=Vector((x,y,base))
  length=rng.uniform(.27,.39)*scale;width=rng.uniform(.067,.108)*scale;rise=rng.uniform(.08,.17)*scale;vs=[];fs=[];N=6;M=4
  for k in range(N+1):
   t=k/N;center=origin+fw*(length*t)+Vector((0,0,rise*math.sin(t*math.pi*.88)+.02*t))
   breadth=width*math.sin(math.pi*t)**.75 if k not in [0,N] else .0015
   for q in range(M+1):
    s=q/M*2-1;ridge=.005*math.cos(s*math.pi*2)*math.sin(math.pi*t);curl=.018*s*s*math.sin(math.pi*t)+.011*math.sin(t*5.7+s*3.1)*abs(s)
    vs.append(tuple(center+side*(s*breadth)+Vector((0,0,ridge+curl))))
  for k in range(N):
   for q in range(M):v=k*(M+1)+q;fs.append((v,v+1,v+M+2,v+M+1))
  mesh('Border muted olive leaf' if rng.random()<.62 else 'Border tobacco dry leaf',vs,fs,rng.uniform(.75,1.12))
  ps=[origin+fw*(length*t)+Vector((0,0,rise*math.sin(t*math.pi*.88)+.02*t+.005)) for t in [0,.33,.66,1]]
  tube('Border bare wet twigs',ps,[.006,.004,.002,.0005],3,.86)

def seedplant(x,y,scale,base):
 counts['dried_seed_stands']+=1
 for j in range(rng.randint(3,4)):
  a=rng.random()*math.tau;origin=Vector((x,y,base));tip=origin+Vector((.07*math.cos(a),.07*math.sin(a),rng.uniform(.27,.42)*scale))
  tube('Border bare wet twigs',[origin,origin.lerp(tip,.5),tip],[.005,.003,.001],3)
  for k in range(4):
   b=k*math.tau/4;end=tip+Vector((.024*math.cos(b),.024*math.sin(b),rng.uniform(-.01,.007)));tube('Border bare wet twigs',[tip-Vector((0,0,.04)),end],[.0014,.0004],3);capsule(end,.012,rng.uniform(.7,.95))

def dead_leaf(x,y,base):
 counts['curled_ground_leaves']+=1
 az=rng.random()*math.tau;fw=Vector((math.cos(az),math.sin(az),0));side=Vector((-math.sin(az),math.cos(az),0));origin=Vector((x,y,base+.004));length=rng.uniform(.08,.17);width=rng.uniform(.022,.049);vs=[];fs=[]
 profile=[(0,.02),(.17,.53),(.3,.40),(.43,1),(.56,.68),(.72,.80),(.87,.38),(1,0)]
 for k,(t,breadth) in enumerate(profile):
  center=origin+fw*(length*(t-.5))+Vector((0,0,.011*math.sin(t*math.pi)+.009*t**3))
  for sign in [-1,0,1]:vs.append(tuple(center+side*(width*breadth*sign*(1 if sign<=0 else .88))+Vector((0,0,.006*abs(sign)*math.sin(t*3.1)))))
 for k in range(len(profile)-1):fs.extend([(k*3,k*3+1,k*3+4,k*3+3),(k*3+1,k*3+2,k*3+5,k*3+4)])
 mesh('Border tobacco dry leaf' if rng.random()<.8 else 'Border muted olive leaf',vs,fs,rng.uniform(.43,.94))

def sector_polygon(c):
 N=48;start=c['start'];end=c['end'];outer=[(c['outerRx']*math.sin(start+(end-start)*i/N),c['outerRz']*math.cos(start+(end-start)*i/N)) for i in range(N+1)]
 inner=[(c['innerRx']*math.sin(start+(end-start)*i/N),c['innerRz']*math.cos(start+(end-start)*i/N)) for i in range(N,-1,-1)];return outer+inner

def inside(px,pz,poly):
 result=False;j=len(poly)-1
 for i,(x,z) in enumerate(poly):
  qx,qz=poly[j]
  if (z>pz)!=(qz>pz) and px<(qx-x)*(pz-z)/(qz-z)+x:result=not result
  j=i
 return result

def boundary_distance(x,z,poly):
 d=1000
 for i,a in enumerate(poly):
  b=poly[(i+1)%len(poly)];dx=b[0]-a[0];dz=b[1]-a[1];t=max(0,min(1,((x-a[0])*dx+(z-a[1])*dz)/(dx*dx+dz*dz)));d=min(d,math.hypot(x-a[0]-t*dx,z-a[1]-t*dz))
 return d

layout=json.loads((ROOT/'src/layout.json').read_text())
if 'borderBeds' not in layout:raise RuntimeError('Waiting for authoritative src/layout.json borderBeds, no geometry generated from guessed layout.')
sectors=[]
for item in layout['borderBeds']:
 c=dict(item)
 for key,value in {'outerRx':10.72,'outerRz':13.58,'innerRx':8.25,'innerRz':10.85}.items():c.setdefault(key,value)
 c['base']=c.get('height',c.get('y',.18))+.005;sectors.append(c)
polygons=[sector_polygon(c) for c in sectors]
all_positions=[]
for index,c in enumerate(sectors):
 poly=polygons[index];positions=[];target=62 if index==0 else 66
 for attempt in range(30000):
  if len(positions)>=target:break
  t=rng.uniform(c['start'],c['end']);r=rng.uniform(.14,.86);x=(c['innerRx']+(c['outerRx']-c['innerRx'])*r)*math.sin(t);z=(c['innerRz']+(c['outerRz']-c['innerRz'])*r)*math.cos(t)
  if not inside(x,z,poly) or boundary_distance(x,z,poly)<.45:continue
  if any((x-a)**2+(z-b)**2<.46**2 for a,b in positions):continue
  quiet_center=c['start']+(c['end']-c['start'])*(.38 if index==0 else .62)
  if abs(t-quiet_center)<.115 and rng.random()<.88:continue
  if math.sin(t*7.1+index)*math.cos(r*8.2)>.55 and rng.random()<.65:continue
  positions.append((x,z))
 if len(positions)<target:raise RuntimeError(f'Sector {index}: only {len(positions)} of {target} safe plant placements found')
 for i,(x,z) in enumerate(positions):
  scale=rng.uniform(.73,.92);y=-z;base=c['base']
  if i in [7,22,40,55]:hosta(x,y,scale,base)
  elif i%13==0:seedplant(x,y,scale,base)
  elif rng.random()<.33:shrub(x,y,scale,base)
  else:grass(x,y,scale,base)
 all_positions.extend(positions)
 for j in range(170 if index==0 else 190):
  for attempt in range(200):
   t=rng.uniform(c['start'],c['end']);r=rng.uniform(.05,.95);x=(c['innerRx']+(c['outerRx']-c['innerRx'])*r)*math.sin(t);z=(c['innerRz']+(c['outerRz']-c['innerRz'])*r)*math.cos(t)
   if inside(x,z,poly) and boundary_distance(x,z,poly)>.11:break
  dead_leaf(x,-z,c['base'])

# Ensure every plant tip and ground leaf stays within the authoritative annular sectors.
outside=0
for vs,fs,cols in parts.values():
 for x,y,z in vs:
  if not any(inside(x,-y,poly) for poly in polygons):outside+=1
if outside:raise RuntimeError(f'Containment failed: {outside} vegetation vertices outside border soil sectors')
triangles=0;objects=[]
for name,(vs,fs,cols) in parts.items():
 me=bpy.data.meshes.new(name);me.from_pydata(vs,[],fs);me.materials.append(mats[name][0]);me.update();me.calc_loop_triangles();triangles+=len(me.loop_triangles)
 for p in me.polygons:p.use_smooth=True
 color=me.color_attributes.new(name='Col',type='FLOAT_COLOR',domain='CORNER')
 for d,c in zip(color.data,cols):d.color=c
 me.color_attributes.active_color=color
 o=bpy.data.objects.new(name,me);bpy.context.collection.objects.link(o);objects.append(o)
if triangles>70000:raise RuntimeError(f'Geometry budget exceeded: {triangles}')
bpy.ops.object.select_all(action='DESELECT')
for o in objects:o.select_set(True)
bpy.context.view_layer.objects.active=objects[0]
bpy.ops.export_scene.gltf(filepath=str(ROOT/'public/assets/border-planting.glb'),export_format='GLB',use_selection=True,export_yup=True,export_apply=True,export_animations=False)
bpy.ops.wm.save_as_mainfile(filepath=str(ROOT/'.dream-loop/border-planting.blend'))
report={'counts':dict(counts),'plants':len(all_positions),'triangles':triangles,'drawCalls':len(objects),'outsideVertices':outside,'sectors':sectors,'positions':all_positions}
(ROOT/'.dream-loop/border-planting-report.json').write_text(json.dumps(report,indent=2))
print('BORDER_PLANTING_RESULT',json.dumps({k:v for k,v in report.items() if k not in ['positions','sectors']}))
