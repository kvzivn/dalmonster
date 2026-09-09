"""Author periodic cobbles from our original generated reference. CPU only.
Run with the Codex dependency Python (numpy, opencv-python-headless, shapely).
Blender imports the resulting original meshes, embeds granite-grain.png and exports.
"""
import os,sys,json,math,random
BASE=os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA=os.path.join(BASE,'.dream-loop','road-fan-meshes.json')
if '--blender' in sys.argv:
 import bpy,bmesh
 bpy.ops.object.select_all(action='SELECT');bpy.ops.object.delete(use_global=False)
 mat=bpy.data.materials.new('Varied natural granite cobbles');mat.use_nodes=True
 nt=mat.node_tree;p=nt.nodes.get('Principled BSDF');p.inputs['Roughness'].default_value=.84
 tex=nt.nodes.new('ShaderNodeTexImage');tex.image=bpy.data.images.load(os.path.join(BASE,'public/assets/granite-grain.png'));tex.image.pack()
 col=nt.nodes.new('ShaderNodeVertexColor');col.layer_name='Color'
 mul=nt.nodes.new('ShaderNodeMixRGB');mul.blend_type='MULTIPLY';mul.inputs[0].default_value=1
 nt.links.new(tex.outputs['Color'],mul.inputs[1]);nt.links.new(col.outputs['Color'],mul.inputs[2]);nt.links.new(mul.outputs[0],p.inputs['Base Color'])
 # glTF exports this familiar texture plus COLOR_0 multiplication directly.
 # Keep the vertex-color multiply in the connected material graph.
 for d in json.load(open(DATA)):
  me=bpy.data.meshes.new(d['name']);me.from_pydata(d['vertices'],[],d['faces']);me.materials.append(mat);me.update()
  ob=bpy.data.objects.new(d['name'],me);bpy.context.collection.objects.link(ob)
  uv=me.uv_layers.new(name='GraniteUV')
  for loop in me.loops:uv.data[loop.index].uv=d['uvs'][loop.vertex_index]
  vc=me.color_attributes.new(name='Color',type='FLOAT_COLOR',domain='POINT')
  for i,c in enumerate(d['colors']):vc.data[i].color=(*[c]*3,1)
  me.color_attributes.active_color=vc
  # Flat top facets, sharply readable bevels; do not smooth out the stone joints.
  # Face winding is explicitly upward for every chamfer and top triangle.
 bpy.ops.wm.save_as_mainfile(filepath=os.path.join(BASE,'.dream-loop/road-fan.blend'))
 bpy.ops.export_scene.gltf(filepath=os.path.join(BASE,'public/assets/road-fan.glb'),export_format='GLB',export_yup=True,export_apply=True,export_vertex_color='ACTIVE')
 print('ROAD_FAN_EXPORT_COMPLETE');sys.exit(0)
import cv2,numpy as np
from shapely.geometry import Polygon,box
from shapely import constrained_delaunay_triangles
from shapely.affinity import translate
import subprocess
N=768;L=2.4
im=cv2.imread(os.path.join(BASE,'public/assets/cobblestone-fan.png'));im=cv2.resize(im,(N,N))
tile=np.tile(im,(3,3,1));g=cv2.GaussianBlur(cv2.cvtColor(tile,cv2.COLOR_BGR2GRAY),(11,11),0)
mask=(g>67).astype('uint8');dist=cv2.distanceTransform(mask,cv2.DIST_L2,5)
peaks=((dist>=cv2.dilate(dist,np.ones((37,37),np.uint8))-.0001)&(dist>8)).astype('uint8')
count,markers,stats,centers=cv2.connectedComponentsWithStats(peaks)
markers=cv2.watershed(cv2.GaussianBlur(tile,(17,17),0),markers.astype('int32'))
raw=[]
for k in np.unique(markers[N:2*N,N:2*N]):
 if k<=0:continue
 cs,_=cv2.findContours((markers==k).astype('uint8'),cv2.RETR_EXTERNAL,cv2.CHAIN_APPROX_SIMPLE)
 if not cs:continue
 co=max(cs,key=cv2.contourArea)
 if cv2.contourArea(co)<80:continue
 coords=(co[:,0,:].astype(float)-N)*L/N
 p=Polygon(coords).buffer(0)
 if p.geom_type!='Polygon':p=max(p.geoms,key=lambda x:x.area)
 cx,cy=p.centroid.coords[0];p=translate(p,-math.floor(cx/L)*L,-math.floor(cy/L)*L)
 if any(p.centroid.distance(q.centroid)<.025 for q in raw):continue
 raw.append(p)
# Merge grain-induced tiny islands back into their enclosing stone before meshing.
# The seam is found by the longest almost-touching boundary, not arbitrary proximity.
from shapely.ops import unary_union
for small in sorted(list(raw),key=lambda p:p.area):
 if small.area>=.004:break
 if not any(small is q for q in raw):continue
 candidates=[q for q in raw if q is not small and q.area>small.area and q.distance(small)<.006]
 if not candidates:continue
 target=max(candidates,key=lambda q:small.buffer(.006).intersection(q).area)
 merged=unary_union([small.buffer(.0018),target.buffer(.0018)]).buffer(-.0018)
 if merged.geom_type=='Polygon':
  raw=[q for q in raw if q is not small and q is not target];raw.append(merged)
# Simplify edge chips at sub-centimeter scale; preserve irregular rectangular course shapes.
# Convex setts preserve the reference course direction while removing grain-induced
# concave notches. Clip adjacent hulls on shared center bisectors before recessing
# the joint: this guarantees there are no crossing or overlapping upper faces.
def hull_cell(p):
 points=list(p.convex_hull.buffer(.035,join_style=2).exterior.coords)[:-1];cx,cy=p.centroid.coords[0]
 for q in raw:
  qx,qy=q.centroid.coords[0]
  for dx in [-L,0,L]:
   for dy in [-L,0,L]:
    nx,ny=qx+dx-cx,qy+dy-cy;dd=nx*nx+ny*ny
    if dd<1e-8 or dd>.52**2:continue
    mx,my=cx+nx*.5,cy+ny*.5;out=[]
    for j,aa in enumerate(points):
     bb=points[(j+1)%len(points)];fa=(aa[0]-mx)*nx+(aa[1]-my)*ny;fb=(bb[0]-mx)*nx+(bb[1]-my)*ny
     if fa<=0:out.append(aa)
     if (fa<=0)!=(fb<=0):
      t=fa/(fa-fb);out.append((aa[0]+t*(bb[0]-aa[0]),aa[1]+t*(bb[1]-aa[1])))
    points=out
    if len(points)<3:return p
 return Polygon(points)
base=[]
for p in raw:
 p=hull_cell(p).buffer(-.0032,join_style=2)
 if p.is_empty:continue
 if p.geom_type!='Polygon':p=max(p.geoms,key=lambda q:q.area)
 eps=.003
 while len(p.simplify(eps,preserve_topology=True).exterior.coords)>10:eps+=.001
 p=p.simplify(eps,preserve_topology=True)
 if p.area>.00055:base.append(p)
# Remove any approximate-contour overlap. Most are already disjoint; periodic copies
# matter at the reference edges. No duplicate top faces survive this operation.
clean=[]
for p in sorted(base,key=lambda p:-p.area):
 for q in clean:
  for dx in [-L,0,L]:
   for dy in [-L,0,L]:
    qq=translate(q,dx,dy)
    if p.intersects(qq):p=p.difference(qq.buffer(.0007))
 if p.is_empty:continue
 if p.geom_type!='Polygon':p=max(p.geoms,key=lambda q:q.area)
 clean.append(p)
base=clean

def deform(x,y,variant):
 # All stones share the same displacement field: neighboring joints stay narrow.
 # Freeze a 20cm strip at every tile edge, so arbitrary variant neighbors match.
 edge=min(x%L,L-x%L,y%L,L-y%L)
 w=max(0,min(1,(edge-.20)/.22));w=w*w*(3-2*w)
 phase=variant*2.094
 return (x+w*.019*math.sin(x*11+phase)*math.cos(y*8-phase),y+w*.019*math.cos(x*8-phase)*math.sin(y*12+phase))

def clip_triangle(tri):
 # Vertex tuple: x,y,height,u,v,color; all vary continuously through an edge cut.
 poly=tri
 for axis,value,sign in [(0,0,1),(0,L,-1),(1,0,1),(1,L,-1)]:
  out=[]
  for i,a in enumerate(poly):
   b=poly[(i+1)%len(poly)];ina=(a[axis]-value)*sign>=-1e-10;inb=(b[axis]-value)*sign>=-1e-10
   if ina:out.append(a)
   if ina!=inb:
    t=(value-a[axis])/(b[axis]-a[axis]);out.append(tuple(aa+t*(bb-aa) for aa,bb in zip(a,b)))
  poly=out
  if len(poly)<3:return []
 return [(poly[0],poly[i],poly[i+1]) for i in range(1,len(poly)-1)]

results=[];report=[]
for variant in range(3):
 vertices=[];faces=[];uvs=[];colors=[]
 for idx,p in enumerate(base):
  seed=random.Random(idx*7741+91);cx,cy=p.centroid.coords[0]
  boundary=min(cx,L-cx,cy,L-cy)<.33
  rng=random.Random(idx*7741+(0 if boundary else variant*12317)+91)
  height=.012+rng.random()*.008;tone=.66+rng.random()*.32
  grainx=seed.random()*3;grainy=seed.random()*3;ang=seed.random()*math.tau
  for dx in [-L,0,L]:
   for dy in [-L,0,L]:
    q=translate(p,dx,dy)
    if not q.intersects(box(0,0,L,L)):continue
    points=[deform(x,y,variant) for x,y in list(q.exterior.coords)[:-1]]
    cxx,cyy=deform(cx+dx,cy+dy,variant)
    # A shallow chamfer and varied, slightly tilted upper face with faceted chips.
    inner=[(x+(cxx-x)*.055,y+(cyy-y)*.055) for x,y in points]
    ip=Polygon(inner)
    if not ip.is_valid:ip=ip.buffer(0)
    def vert(x,y,z,c):
     ux=(x-cx-dx)*math.cos(ang)-(y-cy-dy)*math.sin(ang)
     uy=(x-cx-dx)*math.sin(ang)+(y-cy-dy)*math.cos(ang)
     return (x,y,z,grainx+ux*2.7,grainy+uy*2.7,c)
    def top(x,y):return height+ .006*(x-cxx)+.003*(y-cyy)
    tris=[]
    for j in range(len(points)):
     k=(j+1)%len(points);a=vert(*points[j],0,tone*.58);b=vert(*points[k],0,tone*.58);c=vert(*inner[k],top(*inner[k]),tone*.95);d=vert(*inner[j],top(*inner[j]),tone*.95)
     tris.extend([(a,b,c),(a,c,d)])
    for t in constrained_delaunay_triangles(ip).geoms:
     coords=list(t.exterior.coords)[:3];tris.append(tuple(vert(x,y,top(x,y),tone*(.97+.03*math.sin(x*41+y*33))) for x,y in coords))
    for tri in tris:
     for clipped in clip_triangle(tri):
      a=len(vertices)
      for x,y,z,u,v,c in clipped:vertices.append((x-L/2,-y+L/2,z));uvs.append((u,v));colors.append(c)
      va,vb,vc=vertices[a:a+3]
      cross=(vb[0]-va[0])*(vc[1]-va[1])-(vb[1]-va[1])*(vc[0]-va[0])
      faces.append((a,a+1,a+2) if cross>=0 else (a,a+2,a+1))
 results.append(dict(name=f'RoadFan_{variant}',vertices=vertices,faces=faces,uvs=uvs,colors=colors))
 report.append(dict(name=f'RoadFan_{variant}',triangles=len(faces),stones=len(base),height=max(v[2] for v in vertices)))
# Reference-contour footprint coverage is useful evidence without a render/GPU load.
json.dump(results,open(DATA,'w'));json.dump(report,open(os.path.join(BASE,'.dream-loop/road-fan-report.json'),'w'),indent=2);print(report,flush=True)
subprocess.run(['/Applications/Blender.app/Contents/MacOS/Blender','-b','-t','2','--python',__file__,'--','--blender'],check=True)
